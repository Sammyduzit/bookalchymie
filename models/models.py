from typing import Optional

from constants import AppConstants
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref

db = SQLAlchemy()


class Author(db.Model):
    """Author model representing book authors."""

    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    birth_date = db.Column(db.Date, nullable=True)
    date_of_death = db.Column(db.Date, nullable=True)

    def __repr__(self) -> str:
        return f"<Author(id={self.id}, name='{self.name}')>"

    def __str__(self) -> str:
        birth_str = self.birth_date.strftime('%Y') if self.birth_date else '?'
        death_str = self.date_of_death.strftime('%Y') if self.date_of_death else ''

        if death_str:
            return f"{self.name} ({birth_str}-{death_str})"
        elif birth_str != '?':
            return f"{self.name} (b. {birth_str})"
        else:
            return self.name

    @property
    def average_rating(self) -> Optional[float]:
        """
        Calculate the average rating of all books by this author.
        :return: Average rating or None if no rated books
        """
        ratings = [book.rating for book in self.books if book.rating is not None]
        if ratings:
            return round(sum(ratings) / len(ratings), 1)
        return None

    @property
    def book_count(self) -> int:
        """
        Return the number of books by this author.
        :return: Number of books
        """
        return len(self.books)

    @property
    def age_at_death(self) -> Optional[int]:
        """
        Calculate age at death if both dates are available.
        :return: Age at death or None if dates unavailable
        """
        if self.birth_date and self.date_of_death:
            return self.date_of_death.year - self.birth_date.year
        return None

    @property
    def is_living(self) -> bool:
        """
        Check if author is still living.
        :return: True if author is living, False otherwise
        """
        return self.date_of_death is None

    def to_dict(self) -> dict:
        """
        Convert author to dictionary representation.
        :return: Dictionary containing author data
        """
        return {
            'id': self.id,
            'name': self.name,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'date_of_death': self.date_of_death.isoformat() if self.date_of_death else None,
            'book_count': self.book_count,
            'average_rating': self.average_rating,
            'is_living': self.is_living
        }


class Book(db.Model):
    """Book model representing library books."""

    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(13), unique=True, nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    publication_year = db.Column(db.Integer, nullable=True, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("authors.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    cover_url_cached = db.Column(db.String(500), nullable=True)

    author = db.relationship("Author", backref=backref("books", cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return (f"<Book(id={self.id}, title='{self.title}', "
                f"author_id={self.author_id}, publication_year={self.publication_year}, "
                f"isbn='{self.isbn}', rating={self.rating})>")

    def __str__(self) -> str:
        year_str = f" ({self.publication_year})" if self.publication_year else ""
        return f"{self.title}{year_str}"

    @property
    def rating_stars(self) -> str:
        """
        Return a string representation of the rating as stars out of 5.
        :return: Star rating string or "Not rated"
        """
        if self.rating is None:
            return "Not rated"

        star_rating = self.rating / 2
        full_stars = int(star_rating)
        half_star = 1 if (star_rating - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star

        return "★" * full_stars + ("☆" if half_star else "") + "☆" * empty_stars

    @property
    def formatted_isbn(self) -> str:
        """
        Return formatted ISBN with hyphens.
        :return: Formatted ISBN string or "Not available"
        """
        if not self.isbn:
            return "Not available"

        isbn = self.isbn.replace('-', '')
        if len(isbn) == 13:
            return f"{isbn[:3]}-{isbn[3]}-{isbn[4:6]}-{isbn[6:12]}-{isbn[12]}"
        elif len(isbn) == 10:
            return f"{isbn[:1]}-{isbn[1:6]}-{isbn[6:9]}-{isbn[9]}"
        return self.isbn

    @property
    def cover_url(self) -> str:
        """
        Get book cover URL from cached value or placeholder.
        :return: Cover URL string
        """
        return self.cover_url_cached or AppConstants.DEFAULT_COVER_URL

    def to_dict(self) -> dict:
        """
        Convert book to dictionary representation.
        :return: Dictionary containing book data
        """
        return {
            'id': self.id,
            'title': self.title,
            'isbn': self.isbn,
            'formatted_isbn': self.formatted_isbn,
            'publication_year': self.publication_year,
            'author_id': self.author_id,
            'author': self.author.to_dict() if self.author else None,
            'rating': self.rating,
            'rating_stars': self.rating_stars,
            'cover_url': self.cover_url
        }

    @classmethod
    def search(cls, search_term: str, sort_by: str = 'title'):
        """
        Search books by title, author name, or publication year.
        :param search_term: Term to search for
        :param sort_by: Field to sort by ('title', 'author', 'year')
        :return: Query object with search and sort applied
        """
        query = cls.query

        if search_term and search_term.strip():
            search_term = search_term.strip()
            query = query.filter(
                (cls.title.ilike(f'%{search_term}%')) |
                (cls.author.has(Author.name.ilike(f'%{search_term}%'))) |
                (cls.publication_year == search_term)
            )

        if sort_by == 'author':
            query = query.join(Author).order_by(Author.name)
        elif sort_by == 'year':
            query = query.order_by(cls.publication_year.desc())
        else:
            query = query.order_by(cls.title)

        return query


def init_db(app):
    """
    Initialize database with the Flask app.
    :param app: Flask application instance
    """
    db.init_app(app)

    with app.app_context():
        db.create_all()