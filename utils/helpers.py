from typing import Any, Dict, List, Optional

from flask import flash
from markupsafe import escape
from sqlalchemy import or_

from constants import AppConstants


def flash_success(message: str) -> None:
    """
    Flash a success message.
    :param message: Success message to flash
    """
    flash(message, 'success')


def flash_error(message: str) -> None:
    """
    Flash an error message.
    :param message: Error message to flash
    """
    flash(message, 'error')


def safe_get_form_data(form, key: str, default: Any = None) -> Any:
    """
    Safely get form data with default value.
    :param form: Flask request form
    :param key: Form field key
    :param default: Default value if key not found or empty
    :return: Form value or default
    """
    value = form.get(key, default)
    if isinstance(value, str) and not value.strip():
        return escape(value.strip())
    return value


def build_search_query(model, search_term: str, search_fields: List[str]):
    """
    Build a search query for the given model and fields.
    :param model: SQLAlchemy model class
    :param search_term: Search term to look for
    :param search_fields: List of field names to search in
    :return: SQLAlchemy query object
    """
    if not search_term or not search_term.strip():
        return model.query

    search_term = search_term.strip()
    query = model.query

    conditions = []
    for field_name in search_fields:
        field = getattr(model, field_name, None)
        if field:
            conditions.append(field.ilike(f'%{search_term}%'))

    if conditions:
        query = query.filter(or_(*conditions))

    return query


def get_book_cover_url(isbn: Optional[str], size: str = 'M') -> str:
    """
    Get book cover URL from Open Library.
    :param isbn: Book ISBN
    :param size: Cover size ('S', 'M', 'L')
    :return: Cover URL or placeholder
    """
    if isbn:
        return f"https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg"
    return AppConstants.DEFAULT_COVER_URL


def format_author_display_name(author) -> str:
    """
    Format author name for display with birth/death years.
    :param author: Author model instance
    :return: Formatted author name
    """
    if not author:
        return "Unknown Author"

    name = author.name

    if author.birth_date or author.date_of_death:
        birth_year = author.birth_date.year if author.birth_date else "?"
        death_year = author.date_of_death.year if author.date_of_death else ""

        if death_year:
            name += f" ({birth_year}-{death_year})"
        else:
            name += f" (b. {birth_year})"

    return name


def calculate_reading_statistics(books: List) -> Dict[str, Any]:
    """
    Calculate reading statistics from a list of books.
    :param books: List of book instances
    :return: Dictionary containing statistics
    """
    if not books:
        return {
            'total_books': 0,
            'rated_books': 0,
            'average_rating': None,
            'highest_rated': None,
            'publication_years': []
        }

    rated_books = [book for book in books if book.rating]
    ratings = [book.rating for book in rated_books]

    stats = {
        'total_books': len(books),
        'rated_books': len(rated_books),
        'average_rating': round(sum(ratings) / len(ratings), 1) if ratings else None,
        'highest_rated': max(rated_books, key=lambda b: b.rating) if rated_books else None,
        'publication_years': [book.publication_year for book in books if book.publication_year]
    }

    return stats


def paginate_results(query, page: int = 1, per_page: int = 20):
    """
    Paginate query results.
    :param query: SQLAlchemy query object
    :param page: Page number (1-based)
    :param per_page: Items per page
    :return: Paginated results
    """
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )