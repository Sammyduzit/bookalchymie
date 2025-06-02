from datetime import datetime


class AppConstants:
    """Application-wide constants for validation and configuration."""

    # Validation limits
    MAX_TITLE_LENGTH = 200
    MAX_AUTHOR_NAME_LENGTH = 100
    MIN_PUBLICATION_YEAR = 1000
    MAX_PUBLICATION_YEAR = datetime.now().year + 2
    MIN_RATING = 1.0
    MAX_RATING = 10.0

    # ISBN validation
    ISBN_10_LENGTH = 10
    ISBN_13_LENGTH = 13

    # API settings
    DEFAULT_COVER_URL = "https://via.placeholder.com/200x300/cccccc/666666?text=No+Cover"
    GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
    API_REQUEST_TIMEOUT = 10
    API_MAX_RESULTS = 1

    # Application settings
    DEFAULT_BOOKS_PER_PAGE = 20
    MAX_SEARCH_LENGTH = 100

    # Template settings
    CURRENT_YEAR = datetime.now().year


class ValidationMessages:
    """Standardized validation error messages."""

    # Book validation messages
    TITLE_REQUIRED = "Book title is required"
    TITLE_TOO_LONG = f"Book title must be {AppConstants.MAX_TITLE_LENGTH} characters or less"
    ISBN_INVALID_LENGTH = f"ISBN must be {AppConstants.ISBN_10_LENGTH} or {AppConstants.ISBN_13_LENGTH} digits long"
    YEAR_INVALID_RANGE = f"Publication year must be between {AppConstants.MIN_PUBLICATION_YEAR} and {AppConstants.MAX_PUBLICATION_YEAR}"
    RATING_INVALID_RANGE = f"Rating must be between {AppConstants.MIN_RATING} and {AppConstants.MAX_RATING}"

    # Author validation messages
    AUTHOR_NAME_REQUIRED = "Author name is required"
    AUTHOR_NAME_TOO_LONG = f"Author name must be {AppConstants.MAX_AUTHOR_NAME_LENGTH} characters or less"
    BIRTH_DATE_FUTURE = "Birth date cannot be in the future"
    DEATH_DATE_FUTURE = "Death date cannot be in the future"
    DEATH_BEFORE_BIRTH = "Death date must be after birth date"

    # General messages
    AUTHOR_SELECTION_REQUIRED = "Author selection is required"
    INVALID_AUTHOR_SELECTION = "Invalid author selection"