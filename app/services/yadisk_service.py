from typing import List, Optional
from datetime import datetime

import yadisk
from loguru import logger
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import YandexFileCache


class YandexDiskService:
    """Сервис для работы с Яндекс.Диском"""

    @staticmethod
    def _log_api_call(operation: str, params: dict, response: any = None, error: Exception = None):
        """Логировать вызов API Яндекс.Диска (если включен debug режим)"""
        if not settings.yadisk_debug:
            return

        log_msg = f"[Yandex.Disk API] {operation}"
        logger.debug(f"{log_msg} | Params: {params}")

        if error:
            logger.debug(f"{log_msg} | Error: {error}")
        elif response:
            logger.debug(f"{log_msg} | Response: {response}")

    @staticmethod
    def _get_client() -> yadisk.YaDisk:
        """Получить клиент Яндекс.Диска"""
        return yadisk.YaDisk(token=settings.yandex_disk_token)

    @staticmethod
    def _determine_file_type(file_name: str) -> str:
        """Определить тип файла по расширению"""
        file_name_lower = file_name.lower()

        video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"]
        photo_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
        document_extensions = [".pdf", ".doc", ".docx", ".txt", ".rtf"]
        scenario_extensions = [".fdx", ".fountain", ".celtx"]

        for ext in video_extensions:
            if file_name_lower.endswith(ext):
                return "video"

        for ext in photo_extensions:
            if file_name_lower.endswith(ext):
                return "photo"

        for ext in scenario_extensions:
            if file_name_lower.endswith(ext):
                return "scenario"

        for ext in document_extensions:
            if file_name_lower.endswith(ext):
                return "document"

        return "document"

    @staticmethod
    async def get_files_realtime(root_path: str = "/", max_files: int = 10000) -> List[dict]:
        """
        Получить список всех файлов через API в реальном времени (без кэша)
        Использует встроенный метод get_files() для получения ВСЕХ файлов на Диске

        Args:
            root_path: Корневая папка для поиска (не используется, оставлен для совместимости)
            max_files: Максимальное количество файлов для получения

        Returns:
            Список словарей с информацией о файлах
        """
        YandexDiskService._log_api_call("get_files_realtime", {"max_files": max_files})

        client = YandexDiskService._get_client()
        files_list = []

        try:
            # Проверяем подключение
            if not client.check_token():
                YandexDiskService._log_api_call("check_token", {}, error=Exception("Invalid token"))
                logger.error("Invalid Yandex.Disk token")
                return files_list

            YandexDiskService._log_api_call("check_token", {}, response="Token valid")

            # Используем get_files() для получения ВСЕХ файлов на Диске
            # Это встроенный метод API, который ищет по всем папкам
            YandexDiskService._log_api_call("get_files", {"limit": max_files})

            files_generator = client.get_files(limit=max_files)

            for item in files_generator:
                try:
                    file_info = {
                        "name": item.name,
                        "path": item.path,
                        "type": YandexDiskService._determine_file_type(item.name),
                        "size": getattr(item, 'size', 0),
                        "public_url": getattr(item, 'public_url', None)
                    }
                    files_list.append(file_info)

                    if settings.yadisk_debug:
                        logger.debug(f"[Yandex.Disk API] Found file: {file_info['name']} at {file_info['path']}")

                except Exception as e:
                    logger.error(f"Error processing file {getattr(item, 'name', 'unknown')}: {e}")

            YandexDiskService._log_api_call("get_files_realtime", {"max_files": max_files}, response=f"Found {len(files_list)} files")
            logger.info(f"Retrieved {len(files_list)} files from Yandex.Disk")

        except Exception as e:
            YandexDiskService._log_api_call("get_files_realtime", {"max_files": max_files}, error=e)
            logger.error(f"Error getting files from Yandex.Disk: {e}")

        return files_list

    @staticmethod
    async def sync_files_cache(session: AsyncSession, root_path: str = "/", max_files: int = 10000):
        """
        Синхронизировать кэш файлов с Яндекс.Диска
        Использует get_files() для получения ВСЕХ файлов на Диске за один запрос

        Args:
            session: Сессия БД
            root_path: Не используется, оставлен для совместимости
            max_files: Максимальное количество файлов для кэширования
        """
        logger.info(f"Starting Yandex.Disk sync (max {max_files} files)")

        client = YandexDiskService._get_client()

        try:
            YandexDiskService._log_api_call("sync_files_cache", {"max_files": max_files})

            # Проверяем подключение
            if not client.check_token():
                YandexDiskService._log_api_call("check_token", {}, error=Exception("Invalid token"))
                logger.error("Invalid Yandex.Disk token")
                return

            # Очищаем старый кэш
            await session.execute(delete(YandexFileCache))
            await session.commit()

            # Используем get_files() для получения ВСЕХ файлов на Диске
            YandexDiskService._log_api_call("get_files", {"limit": max_files})
            files_generator = client.get_files(limit=max_files)

            files_count = 0
            for item in files_generator:
                try:
                    # Получаем публичную ссылку (если файл опубликован)
                    public_url = None
                    try:
                        if hasattr(item, 'public_url') and item.public_url:
                            public_url = item.public_url
                    except:
                        pass

                    file_type = YandexDiskService._determine_file_type(item.name)

                    file_cache = YandexFileCache(
                        file_name=item.name,
                        file_path=item.path,
                        public_url=public_url,
                        file_type=file_type,
                        updated_at=datetime.now()
                    )

                    session.add(file_cache)
                    files_count += 1

                    if settings.yadisk_debug:
                        logger.debug(f"[Yandex.Disk API] Cached file: {item.name} at {item.path}")

                except Exception as e:
                    logger.error(f"Error caching file {getattr(item, 'name', 'unknown')}: {e}")

            await session.commit()
            logger.info(f"Yandex.Disk sync completed. Cached {files_count} files")

        except Exception as e:
            logger.error(f"Error syncing Yandex.Disk: {e}")
            await session.rollback()

    @staticmethod
    async def search_files(session: AsyncSession, query: str, limit: int = 20) -> List[YandexFileCache]:
        """Поиск файлов в кэше по запросу"""
        query_lower = query.lower()

        # Разбиваем запрос на слова для более гибкого поиска
        query_words = query_lower.split()

        stmt = select(YandexFileCache)
        result = await session.execute(stmt)
        all_files = list(result.scalars().all())

        # Фильтруем файлы, которые содержат все слова из запроса
        matching_files = []
        for file in all_files:
            file_name_lower = file.file_name.lower()
            if all(word in file_name_lower for word in query_words):
                matching_files.append(file)

        # Сортируем по релевантности (файлы, где запрос встречается раньше)
        matching_files.sort(key=lambda f: f.file_name.lower().find(query_lower))

        return matching_files[:limit]

    @staticmethod
    async def get_all_files_batched(session: AsyncSession, batch_size: int = 5000):
        """
        Получить все файлы из кэша по частям (генератор).
        
        Args:
            session: Сессия БД
            batch_size: Размер одной пачки файлов
            
        Yields:
            Списки файлов размером batch_size
        """
        offset = 0
        
        while True:
            stmt = select(YandexFileCache).offset(offset).limit(batch_size)
            result = await session.execute(stmt)
            files = list(result.scalars().all())
            
            if not files:
                break
                
            yield files
            offset += batch_size
            
            # Если получили меньше чем batch_size, значит это последняя пачка
            if len(files) < batch_size:
                break

    @staticmethod
    async def get_file_info(session: AsyncSession, file_id: int) -> Optional[YandexFileCache]:
        """Получить информацию о файле по ID"""
        stmt = select(YandexFileCache).where(YandexFileCache.id == file_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def publish_file(file_path: str) -> Optional[str]:
        """
        Опубликовать файл и получить публичную ссылку

        Args:
            file_path: Путь к файлу на Яндекс.Диске

        Returns:
            Публичная ссылка на файл или None в случае ошибки
        """
        client = YandexDiskService._get_client()

        try:
            YandexDiskService._log_api_call("publish_file", {"path": file_path})

            # Публикуем файл
            result = client.publish(file_path)

            # Получаем публичную ссылку
            public_url = result.public_url if hasattr(result, 'public_url') else None

            if public_url:
                YandexDiskService._log_api_call("publish_file", {"path": file_path}, response=public_url)
                logger.info(f"Published file: {file_path} -> {public_url}")
                return public_url
            else:
                logger.warning(f"Failed to get public URL for: {file_path}")
                return None

        except Exception as e:
            YandexDiskService._log_api_call("publish_file", {"path": file_path}, error=e)
            logger.error(f"Error publishing file {file_path}: {e}")
            return None

    @staticmethod
    async def ensure_public_url(session: AsyncSession, file_cache: YandexFileCache) -> Optional[str]:
        """
        Убедиться, что у файла есть публичная ссылка. Если нет - создать.

        Args:
            session: Сессия БД
            file_cache: Объект файла из кэша

        Returns:
            Публичная ссылка на файл или None в случае ошибки
        """
        # Если уже есть публичная ссылка - возвращаем её
        if file_cache.public_url:
            return file_cache.public_url

        # Публикуем файл
        public_url = YandexDiskService.publish_file(file_cache.file_path)

        if public_url:
            # Обновляем запись в БД
            file_cache.public_url = public_url
            file_cache.updated_at = datetime.now()
            await session.commit()

        return public_url
