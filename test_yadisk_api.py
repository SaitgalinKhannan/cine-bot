#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Яндекс.Диск API
Проверяет, какие файлы возвращает API и почему поиск может не работать
"""

import os
import sys
from dotenv import load_dotenv
import yadisk

# Загружаем переменные окружения
load_dotenv()

def test_yadisk_api():
    """Тестирование Яндекс.Диск API"""

    # Получаем токен
    token = os.getenv("YANDEX_DISK_TOKEN")
    if not token:
        print("❌ YANDEX_DISK_TOKEN не найден в .env")
        sys.exit(1)

    print("=" * 80)
    print("ТЕСТ ЯНДЕКС.ДИСК API")
    print("=" * 80)

    # Создаем клиент
    client = yadisk.YaDisk(token=token)

    # Проверяем токен
    print("\n1. Проверка токена...")
    try:
        if client.check_token():
            print("✅ Токен валидный")
        else:
            print("❌ Токен невалидный")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка проверки токена: {e}")
        sys.exit(1)

    # Получаем все файлы
    print("\n2. Получение списка всех файлов через get_files()...")
    try:
        files = list(client.get_files(limit=1000))
        print(f"✅ Получено файлов: {len(files)}")
    except Exception as e:
        print(f"❌ Ошибка получения файлов: {e}")
        sys.exit(1)

    # Выводим все файлы
    print("\n3. Список всех файлов:")
    print("-" * 80)
    for i, file in enumerate(files, 1):
        print(f"{i}. {file.name}")
        print(f"   Путь: {file.path}")
        print(f"   Тип: {file.type}")
        print()

    # Тестируем поиск
    print("\n4. Тестирование поиска...")
    print("-" * 80)

    search_queries = [
        "сценарий Асия",
        "Сценарий АСИЯ",
        "АСИЯ",
        "Асия",
        "асия",
        "сценарий",
        "Сценарий",
    ]

    for query in search_queries:
        print(f"\nПоиск: '{query}'")
        query_lower = query.lower()

        # Простой поиск по вхождению
        found = []
        for file in files:
            if query_lower in file.name.lower():
                found.append(file)

        if found:
            print(f"✅ Найдено файлов: {len(found)}")
            for file in found:
                print(f"   - {file.name} ({file.path})")
        else:
            print(f"❌ Ничего не найдено")

    # Тестируем поиск по словам
    print("\n5. Тестирование поиска по словам (как в боте)...")
    print("-" * 80)

    query = "сценарий Асия"
    query_lower = query.lower()
    query_words = query_lower.split()

    print(f"Запрос: '{query}'")
    print(f"Слова для поиска: {query_words}")

    matching_files = []
    for file in files:
        file_name_lower = file.name.lower()
        # Проверяем, что ВСЕ слова из запроса есть в названии файла
        if all(word in file_name_lower for word in query_words):
            matching_files.append(file)

    if matching_files:
        print(f"✅ Найдено файлов: {len(matching_files)}")
        for file in matching_files:
            print(f"   - {file.name} ({file.path})")
    else:
        print(f"❌ Ничего не найдено")
        print("\nПроверка каждого слова отдельно:")
        for word in query_words:
            print(f"\n  Слово: '{word}'")
            for file in files:
                if word in file.name.lower():
                    print(f"    ✅ Найдено в: {file.name}")

    # Проверяем конкретный файл
    print("\n6. Проверка конкретного файла 'Загрузки/Сценарий АСИЯ.docx'...")
    print("-" * 80)

    target_file = None
    for file in files:
        if "Сценарий АСИЯ" in file.name or "сценарий асия" in file.name.lower():
            target_file = file
            break

    if target_file:
        print(f"✅ Файл найден!")
        print(f"   Имя: {target_file.name}")
        print(f"   Путь: {target_file.path}")
        print(f"   Тип: {target_file.type}")

        # Проверяем, почему поиск не работает
        print("\n   Проверка поиска:")
        test_queries = ["сценарий Асия", "Сценарий АСИЯ", "асия"]
        for test_query in test_queries:
            query_words = test_query.lower().split()
            file_name_lower = target_file.name.lower()

            print(f"\n   Запрос: '{test_query}'")
            print(f"   Слова: {query_words}")
            print(f"   Имя файла (lowercase): '{file_name_lower}'")

            for word in query_words:
                if word in file_name_lower:
                    print(f"     ✅ '{word}' найдено в имени файла")
                else:
                    print(f"     ❌ '{word}' НЕ найдено в имени файла")

            if all(word in file_name_lower for word in query_words):
                print(f"   ✅ Все слова найдены - файл должен быть в результатах")
            else:
                print(f"   ❌ Не все слова найдены - файл НЕ будет в результатах")
    else:
        print(f"❌ Файл 'Сценарий АСИЯ.docx' не найден в списке")
        print("\nВозможные причины:")
        print("1. Файл находится в другой папке")
        print("2. Файл называется по-другому")
        print("3. API не возвращает этот файл")
        print("\nПопробуйте найти файл вручную:")
        print("Все файлы со словом 'сценарий':")
        for file in files:
            if "сценарий" in file.name.lower():
                print(f"  - {file.name} ({file.path})")

    print("\n" + "=" * 80)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 80)


if __name__ == "__main__":
    test_yadisk_api()
