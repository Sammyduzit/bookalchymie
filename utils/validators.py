from datetime import datetime
from typing import Optional, Tuple, Union

from constants import AppConstants, ValidationMessages


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class BookValidator:
    """Validator class for book-related data."""

    @staticmethod
    def validate_title(title: str) -> str:
        """
        Validate book title.
        :param title: The book title to validate
        :return: The cleaned title
        :raises ValidationError: If title is invalid
        """
        if not title or not title.strip():
            raise ValidationError(ValidationMessages.TITLE_REQUIRED)

        title = title.strip()
        if len(title) > AppConstants.MAX_TITLE_LENGTH:
            raise ValidationError(ValidationMessages.TITLE_TOO_LONG)

        return title

    @staticmethod
    def validate_isbn(isbn: Optional[str]) -> Optional[str]:
        """
        Validate ISBN.
        :param isbn: The ISBN to validate
        :return: The cleaned ISBN or None
        :raises ValidationError: If ISBN format is invalid
        """
        if not isbn or not isbn.strip():
            return None

        clean_isbn = ''.join(char for char in isbn.strip() if char.isdigit())

        if not clean_isbn:
            raise ValidationError("ISBN must contain at least some digits")

        if len(clean_isbn) not in [AppConstants.ISBN_10_LENGTH, AppConstants.ISBN_13_LENGTH]:
            raise ValidationError(ValidationMessages.ISBN_INVALID_LENGTH)

        return isbn.strip()

    @staticmethod
    def validate_publication_year(year: Union[str, int, None]) -> Optional[int]:
        """
        Validate publication year.
        :param year: The year to validate
        :return: The validated year or None
        :raises ValidationError: If year is invalid
        """
        if not year:
            return None

        try:
            year = int(year)
        except (ValueError, TypeError):
            raise ValidationError("Publication year must be a valid number")

        if (year < AppConstants.MIN_PUBLICATION_YEAR or
                year > AppConstants.MAX_PUBLICATION_YEAR):
            raise ValidationError(ValidationMessages.YEAR_INVALID_RANGE)

        return year

    @staticmethod
    def validate_rating(rating: Union[str, float, None]) -> Optional[float]:
        """
        Validate book rating.
        :param rating: The rating to validate
        :return: The validated rating or None
        :raises ValidationError: If rating is invalid
        """
        if not rating:
            return None

        try:
            rating = float(rating)
        except (ValueError, TypeError):
            raise ValidationError("Rating must be a valid number")

        if not (AppConstants.MIN_RATING <= rating <= AppConstants.MAX_RATING):
            raise ValidationError(ValidationMessages.RATING_INVALID_RANGE)

        return round(rating, 1)

    @staticmethod
    def validate_author_id(author_id: Union[str, int, None]) -> int:
        """
        Validate author ID.
        :param author_id: The author ID to validate
        :return: The validated author ID
        :raises ValidationError: If author ID is invalid
        """
        if not author_id:
            raise ValidationError(ValidationMessages.AUTHOR_SELECTION_REQUIRED)

        try:
            author_id = int(author_id)
        except (ValueError, TypeError):
            raise ValidationError(ValidationMessages.INVALID_AUTHOR_SELECTION)

        if author_id <= 0:
            raise ValidationError(ValidationMessages.INVALID_AUTHOR_SELECTION)

        return author_id


class AuthorValidator:
    """Validator class for author-related data."""

    @staticmethod
    def validate_name(name: str) -> str:
        """
        Validate author name.
        :param name: The author name to validate
        :return: The cleaned name
        :raises ValidationError: If name is invalid
        """
        if not name or not name.strip():
            raise ValidationError(ValidationMessages.AUTHOR_NAME_REQUIRED)

        name = name.strip()
        if len(name) > AppConstants.MAX_AUTHOR_NAME_LENGTH:
            raise ValidationError(ValidationMessages.AUTHOR_NAME_TOO_LONG)

        return name

    @staticmethod
    def validate_date(date_str: Optional[str], field_name: str) -> Optional[datetime]:
        """
        Validate date string.
        :param date_str: The date string to validate
        :param field_name: Name of the field for error messages
        :return: The validated date or None
        :raises ValidationError: If date is invalid
        """
        if not date_str or not date_str.strip():
            return None

        try:
            date_obj = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValidationError(f"{field_name} must be in YYYY-MM-DD format")

        current_date = datetime.now()
        if date_obj > current_date:
            raise ValidationError(f"{field_name} cannot be in the future")

        return date_obj

    @staticmethod
    def validate_birth_death_dates(birth_date: Optional[datetime],
                                   death_date: Optional[datetime]) -> Tuple[Optional[datetime],
                                    Optional[datetime]]:
        """
        Validate birth and death dates together.
        :param birth_date: The birth date
        :param death_date: The death date
        :return: The validated dates
        :raises ValidationError: If dates are invalid together
        """
        if birth_date and death_date:
            if death_date <= birth_date:
                raise ValidationError(ValidationMessages.DEATH_BEFORE_BIRTH)

        return birth_date, death_date


def validate_book_data(form_data: dict) -> dict:
    """
    Validate all book form data.
    :param form_data: Dictionary containing form data
    :return: Dictionary containing validated data
    :raises ValidationError: If any validation fails
    """
    validator = BookValidator()

    return {
        'title': validator.validate_title(form_data.get('title', '')),
        'isbn': validator.validate_isbn(form_data.get('isbn')),
        'publication_year': validator.validate_publication_year(form_data.get('publication_year')),
        'author_id': validator.validate_author_id(form_data.get('author_id')),
        'rating': validator.validate_rating(form_data.get('rating'))
    }


def validate_author_data(form_data: dict) -> dict:
    """
    Validate all author form data.
    :param form_data: Dictionary containing form data
    :return: Dictionary containing validated data
    :raises ValidationError: If any validation fails
    """
    validator = AuthorValidator()

    birth_date = validator.validate_date(form_data.get('birthdate'), 'Birth date')
    death_date = validator.validate_date(form_data.get('date_of_death'), 'Death date')

    birth_date, death_date = validator.validate_birth_death_dates(birth_date, death_date)

    return {
        'name': validator.validate_name(form_data.get('name', '')),
        'birth_date': birth_date.date() if birth_date else None,
        'date_of_death': death_date.date() if death_date else None
    }