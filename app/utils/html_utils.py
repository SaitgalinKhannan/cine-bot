"""HTML utility functions for safe message formatting"""
from html import escape as html_escape


def escape_html(text: str) -> str:
    """
    Escape HTML special characters to prevent XSS attacks

    Args:
        text: Text that may contain HTML special characters

    Returns:
        Escaped text safe for use in HTML messages
    """
    if not text:
        return ""
    return html_escape(str(text))
