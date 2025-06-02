from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError

from models.models import Author, Book, db
from services.cover_service import get_book_cover_url
from utils.validators import ValidationError, validate_author_data, validate_book_data


class BookService:
    """Service class for book-related operations."""

    @staticmethod
    def get_all_books(search_query: str = '', sort_by: str = 'title') -> List[Book]:
        """
        Get all books with optional search and sorting.
        :param search_query: Search term
        :param sort_by: Sort field ('title', 'author', 'year')
        :return: List of books
        """
        try:
            return Book.search(search_query, sort_by).all()
        except SQLAlchemyError as e:
            raise ServiceError(f"Error retrieving books: {str(e)}")

    @staticmethod
    def get_book_by_id(book_id: int) -> Optional[Book]:
        """
        Get a book by its ID.
        :param book_id: Book ID
        :return: Book instance or None
        """
        try:
            return Book.query.get(book_id)
        except SQLAlchemyError as e:
            raise ServiceError(f"Error retrieving book: {str(e)}")

    @staticmethod
    def create_book(form_data: Dict[str, Any]) -> Book:
        """
        Create a new book with cover URL fetched directly.
        :param form_data: Form data dictionary
        :return: Created book instance
        :raises ValidationError: If validation fails
        :raises ServiceError: If database operation fails
        """
        try:
            validated_data = validate_book_data(form_data)

            author = Author.query.get(validated_data['author_id'])
            if not author:
                raise ValidationError("Selected author does not exist")

            if validated_data['isbn']:
                existing_book = Book.query.filter_by(isbn=validated_data['isbn']).first()
                if existing_book:
                    raise ValidationError("A book with this ISBN already exists")

            cover_url = get_book_cover_url(validated_data['isbn'], validated_data['title'])

            book = Book(
                title=validated_data['title'],
                isbn=validated_data['isbn'],
                publication_year=validated_data['publication_year'],
                author_id=validated_data['author_id'],
                rating=validated_data['rating'],
                cover_url_cached=cover_url
            )

            db.session.add(book)
            db.session.commit()

            return book

        except ValidationError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ServiceError(f"Error creating book: {str(e)}")
        except Exception as e:
            db.session.rollback()
            raise ServiceError(f"Error creating book: {str(e)}")

    @staticmethod
    def update_book(book_id: int, form_data: Dict[str, Any]) -> Book:
        """
        Update an existing book with new cover URL if ISBN changed.
        :param book_id: Book ID
        :param form_data: Form data dictionary
        :return: Updated book instance
        :raises ValidationError: If validation fails
        :raises ServiceError: If book not found or database operation fails
        """
        try:
            book = Book.query.get(book_id)
            if not book:
                raise ServiceError("Book not found")

            validated_data = validate_book_data(form_data)

            author = Author.query.get(validated_data['author_id'])
            if not author:
                raise ValidationError("Selected author does not exist")

            if validated_data['isbn'] and validated_data['isbn'] != book.isbn:
                existing_book = Book.query.filter_by(isbn=validated_data['isbn']).first()
                if existing_book:
                    raise ValidationError("A book with this ISBN already exists")

            isbn_changed = validated_data['isbn'] != book.isbn

            book.title = validated_data['title']
            book.isbn = validated_data['isbn']
            book.publication_year = validated_data['publication_year']
            book.author_id = validated_data['author_id']
            book.rating = validated_data['rating']

            if isbn_changed:
                book.cover_url_cached = get_book_cover_url(book.isbn, book.title)

            db.session.commit()

            return book

        except ValidationError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ServiceError(f"Error updating book: {str(e)}")
        except Exception as e:
            db.session.rollback()
            raise ServiceError(f"Error updating book: {str(e)}")

    @staticmethod
    def rate_book(book_id: int, rating: float) -> Book:
        """
        Rate a book.
        :param book_id: Book ID
        :param rating: Rating value (1-10)
        :return: Updated book instance
        :raises ValidationError: If rating is invalid
        :raises ServiceError: If book not found or database operation fails
        """
        try:
            book = Book.query.get(book_id)
            if not book:
                raise ServiceError("Book not found")

            if not (1.0 <= rating <= 10.0):
                raise ValidationError("Rating must be between 1 and 10")

            book.rating = round(rating, 1)
            db.session.commit()

            return book

        except ValidationError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ServiceError(f"Error rating book: {str(e)}")

    @staticmethod
    def delete_book(book_id: int) -> Dict[str, Any]:
        """
        Delete a book and optionally its author if it's their only book.
        :param book_id: Book ID
        :return: Dictionary with deletion information
        :raises ServiceError: If book not found or database operation fails
        """
        try:
            book = Book.query.get(book_id)
            if not book:
                raise ServiceError("Book not found")

            book_title = book.title
            author = book.author
            author_deleted = False
            author_name = None

            if author:
                author_book_count = Book.query.filter_by(author_id=author.id).count()
                if author_book_count == 1:
                    author_name = author.name
                    author_deleted = True

            db.session.delete(book)

            if author_deleted and author:
                db.session.delete(author)

            db.session.commit()

            return {
                'book_title': book_title,
                'author_deleted': author_deleted,
                'author_name': author_name
            }

        except SQLAlchemyError as e:
            db.session.rollback()
            raise ServiceError(f"Error deleting book: {str(e)}")


class AuthorService:
    """Service class for author-related operations."""

    @staticmethod
    def get_all_authors() -> List[Author]:
        """
        Get all authors ordered by name.
        :return: List of authors
        """
        try:
            return Author.query.order_by(Author.name).all()
        except SQLAlchemyError as e:
            raise ServiceError(f"Error retrieving authors: {str(e)}")

    @staticmethod
    def get_author_by_id(author_id: int) -> Optional[Author]:
        """
        Get an author by their ID.
        :param author_id: Author ID
        :return: Author instance or None
        """
        try:
            return Author.query.get(author_id)
        except SQLAlchemyError as e:
            raise ServiceError(f"Error retrieving author: {str(e)}")

    @staticmethod
    def create_author(form_data: Dict[str, Any]) -> Author:
        """
        Create a new author.
        :param form_data: Form data dictionary
        :return: Created author instance
        :raises ValidationError: If validation fails
        :raises ServiceError: If database operation fails
        """
        try:
            validated_data = validate_author_data(form_data)

            existing_author = Author.query.filter_by(name=validated_data['name']).first()
            if existing_author:
                raise ValidationError("An author with this name already exists")

            author = Author(
                name=validated_data['name'],
                birth_date=validated_data['birth_date'],
                date_of_death=validated_data['date_of_death']
            )

            db.session.add(author)
            db.session.commit()

            return author

        except ValidationError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ServiceError(f"Error creating author: {str(e)}")

    @staticmethod
    def update_author(author_id: int, form_data: Dict[str, Any]) -> Author:
        """
        Update an existing author.
        :param author_id: Author ID
        :param form_data: Form data dictionary
        :return: Updated author instance
        :raises ValidationError: If validation fails
        :raises ServiceError: If author not found or database operation fails
        """
        try:
            author = Author.query.get(author_id)
            if not author:
                raise ServiceError("Author not found")

            validated_data = validate_author_data(form_data)

            if validated_data['name'] != author.name:
                existing_author = Author.query.filter_by(name=validated_data['name']).first()
                if existing_author:
                    raise ValidationError("An author with this name already exists")

            author.name = validated_data['name']
            author.birth_date = validated_data['birth_date']
            author.date_of_death = validated_data['date_of_death']

            db.session.commit()

            return author

        except ValidationError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            raise ServiceError(f"Error updating author: {str(e)}")

    @staticmethod
    def delete_author(author_id: int) -> Dict[str, Any]:
        """
        Delete an author and all their books (cascade delete).
        :param author_id: Author ID
        :return: Dictionary with deletion information
        :raises ServiceError: If author not found or database operation fails
        """
        try:
            author = Author.query.get(author_id)
            if not author:
                raise ServiceError("Author not found")

            author_name = author.name
            book_count = len(author.books)
            book_titles = [book.title for book in author.books]

            db.session.delete(author)
            db.session.commit()

            return {
                'author_name': author_name,
                'book_count': book_count,
                'book_titles': book_titles
            }

        except SQLAlchemyError as e:
            db.session.rollback()
            raise ServiceError(f"Error deleting author: {str(e)}")

    @staticmethod
    def get_author_with_books(author_id: int) -> Optional[Author]:
        """
        Get an author with their books, ordered by publication year.
        :param author_id: Author ID
        :return: Author instance with books or None
        """
        try:
            author = Author.query.get(author_id)
            if not author:
                return None

            books = Book.query.filter_by(author_id=author_id).order_by(
                Book.publication_year.desc()
            ).all()

            author._books_ordered = books

            return author

        except SQLAlchemyError as e:
            raise ServiceError(f"Error retrieving author with books: {str(e)}")


class ServiceError(Exception):
    """Custom exception for service layer errors."""
    pass