import os
from typing import Optional

import requests
from sqlalchemy.exc import SQLAlchemyError

from constants import AppConstants
from models.models import Book, db


def get_book_cover_url(isbn: str, title: str = None) -> str:
    """
    Get book cover URL using Google Books API.
    :param isbn: Book ISBN (can contain hyphens)
    :param title: Book title (used as fallback search)
    :return: Cover URL from Google Books or placeholder
    """
    api_key = os.environ.get('GOOGLE_BOOKS_API_KEY')
    if not api_key:
        return AppConstants.DEFAULT_COVER_URL

    clean_isbn = ''.join(char for char in isbn if char.isdigit()) if isbn else ""

    if clean_isbn and len(clean_isbn) in [AppConstants.ISBN_10_LENGTH,
                                          AppConstants.ISBN_13_LENGTH]:
        cover_url = get_google_books_cover(clean_isbn)
        if cover_url:
            return cover_url

    if title:
        cover_url = get_google_books_cover_by_title(title)
        if cover_url:
            return cover_url

    return AppConstants.DEFAULT_COVER_URL


def get_google_books_cover(isbn: str) -> Optional[str]:
    """
    Get book cover from Google Books API using ISBN.
    :param isbn: Clean ISBN (digits only)
    :return: Cover URL or None if not found
    """
    try:
        params = {
            'q': f'isbn:{isbn}',
            'key': os.environ.get('GOOGLE_BOOKS_API_KEY'),
            'maxResults': AppConstants.API_MAX_RESULTS
        }

        response = requests.get(AppConstants.GOOGLE_BOOKS_API_URL, params=params,
                                timeout=AppConstants.API_REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        if data.get('totalItems', 0) > 0:
            book = data['items'][0]
            volume_info = book.get('volumeInfo', {})
            image_links = volume_info.get('imageLinks', {})

            for size in ['large', 'medium', 'thumbnail']:
                if size in image_links:
                    cover_url = image_links[size]
                    if cover_url.startswith('http://'):
                        cover_url = cover_url.replace('http://', 'https://')
                    return cover_url

        return None

    except (requests.RequestException, ValueError, KeyError):
        return None


def refresh_book_cover(book_id: int) -> Optional[str]:
    """
    Refresh a book's cover by fetching it again and updating the database.
    :param book_id: Book ID
    :return: New cover URL or None if book not found
    """
    try:
        from models.models import Book, db

        book = Book.query.get(book_id)
        if not book:
            return None

        new_cover_url = get_book_cover_url(book.isbn, book.title)
        book.cover_url_cached = new_cover_url
        db.session.commit()

        return new_cover_url

    except Exception:
        return None


def get_google_books_cover_by_title(title: str) -> Optional[str]:
    """
    Get book cover from Google Books API using title search.
    :param title: Book title
    :return: Cover URL or None if not found
    """
    try:
        params = {
            'q': f'intitle:"{title}"',
            'key': os.environ.get('GOOGLE_BOOKS_API_KEY'),
            'maxResults': AppConstants.API_MAX_RESULTS
        }

        response = requests.get(AppConstants.GOOGLE_BOOKS_API_URL, params=params,
                                timeout=AppConstants.API_REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        if data.get('totalItems', 0) > 0:
            book = data['items'][0]
            volume_info = book.get('volumeInfo', {})
            image_links = volume_info.get('imageLinks', {})

            for size in ['large', 'medium', 'thumbnail']:
                if size in image_links:
                    cover_url = image_links[size]
                    if cover_url.startswith('http://'):
                        cover_url = cover_url.replace('http://', 'https://')
                    return cover_url

        return None

    except (requests.RequestException, ValueError, KeyError):
        return None