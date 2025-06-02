import os

from flask import Flask, jsonify, redirect, render_template, request, url_for

from config import config
from models.models import Author, Book, init_db
from services.cover_service import refresh_book_cover
from services.services import AuthorService, BookService, ServiceError
from utils.helpers import flash_error, flash_success, safe_get_form_data
from utils.validators import ValidationError


def create_app(config_name: str = None) -> Flask:
    """
    Create and configure the Flask application.
    :param config_name: Configuration environment name
    :return: Configured Flask app
    """
    app = Flask(__name__)

    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])

    init_db(app)
    register_error_handlers(app)
    register_routes(app)

    return app


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers for the application.
    :param app: Flask application instance
    """

    @app.errorhandler(404)
    def not_found_error(error):
        """
        Handle 404 errors.
        :param error: Error instance
        :return: 404 error template and status code
        """
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """
        Handle 500 errors.
        :param error: Error instance
        :return: 500 error template and status code
        """
        return render_template('errors/500.html'), 500

    @app.errorhandler(ValidationError)
    def validation_error(error):
        """
        Handle validation errors.
        :param error: ValidationError instance
        :return: Redirect to referrer or homepage
        """
        flash_error(str(error))
        return redirect(request.referrer or url_for('homepage'))

    @app.errorhandler(ServiceError)
    def service_error(error):
        """
        Handle service errors.
        :param error: ServiceError instance
        :return: Redirect to referrer or homepage
        """
        flash_error(str(error))
        return redirect(request.referrer or url_for('homepage'))


def register_routes(app: Flask) -> None:
    """
    Register all application routes.
    :param app: Flask application instance
    """

    @app.route("/")
    def homepage():
        """
        Display the library homepage with books.
        :return: Homepage template with books
        """
        try:
            search_query = request.args.get('search', '').strip()
            sort_by = request.args.get('sort', 'title')

            if sort_by not in ['title', 'author', 'year']:
                sort_by = 'title'

            books = BookService.get_all_books(search_query, sort_by)

            return render_template(
                "home.html",
                books=books,
                search_query=search_query,
                sort_by=sort_by
            )

        except ServiceError as e:
            flash_error(f"Error loading books: {str(e)}")
            return render_template("home.html", books=[], search_query='', sort_by='title')

    @app.route("/add_author", methods=["GET", "POST"])
    def add_author():
        """
        Add a new author to the library.
        :return: Add author template or redirect
        """
        if request.method == "POST":
            try:
                form_data = {
                    'name': safe_get_form_data(request.form, 'name', ''),
                    'birthdate': safe_get_form_data(request.form, 'birthdate'),
                    'date_of_death': safe_get_form_data(request.form, 'date_of_death')
                }

                author = AuthorService.create_author(form_data)
                flash_success(f"Author '{author.name}' successfully added.")
                return redirect(url_for("add_author"))

            except (ValidationError, ServiceError) as e:
                flash_error(str(e))
                return redirect(url_for("add_author"))

        return render_template("add_author.html")

    @app.route("/add_book", methods=["GET", "POST"])
    def add_book():
        """
        Add a new book to the library.
        :return: Add book template or redirect
        """
        try:
            authors = AuthorService.get_all_authors()

            if request.method == "POST":
                form_data = {
                    'title': safe_get_form_data(request.form, 'title', ''),
                    'isbn': safe_get_form_data(request.form, 'isbn'),
                    'publication_year': safe_get_form_data(request.form, 'publication_year'),
                    'author_id': safe_get_form_data(request.form, 'author_id'),
                    'rating': safe_get_form_data(request.form, 'rating')
                }

                book = BookService.create_book(form_data)
                flash_success(f"Book '{book.title}' successfully added.")
                return redirect(url_for("add_book"))

            return render_template("add_book.html", authors=authors)

        except (ValidationError, ServiceError) as e:
            flash_error(str(e))
            return render_template("add_book.html", authors=[])

    @app.route("/book/<int:book_id>")
    def book_detail(book_id: int):
        """
        Display detailed information about a specific book.
        :param book_id: Book ID
        :return: Book detail template or redirect
        """
        try:
            book = BookService.get_book_by_id(book_id)
            if not book:
                flash_error("Book not found.")
                return redirect(url_for("homepage"))

            return render_template("book_detail.html", book=book)

        except ServiceError as e:
            flash_error(str(e))
            return redirect(url_for("homepage"))

    @app.route("/book/<int:book_id>/edit", methods=["GET", "POST"])
    def edit_book(book_id: int):
        """
        Edit an existing book.
        :param book_id: Book ID
        :return: Edit book template or redirect
        """
        try:
            book = BookService.get_book_by_id(book_id)
            if not book:
                flash_error("Book not found.")
                return redirect(url_for("homepage"))

            if request.method == "POST":
                try:
                    form_data = {
                        'title': safe_get_form_data(request.form, 'title', ''),
                        'isbn': safe_get_form_data(request.form, 'isbn'),
                        'publication_year': safe_get_form_data(request.form, 'publication_year'),
                        'author_id': safe_get_form_data(request.form, 'author_id'),
                        'rating': safe_get_form_data(request.form, 'rating')
                    }

                    updated_book = BookService.update_book(book_id, form_data)
                    flash_success(f"Book '{updated_book.title}' successfully updated.")
                    return redirect(url_for("book_detail", book_id=book_id))

                except (ValidationError, ServiceError) as e:
                    flash_error(str(e))
                    authors = AuthorService.get_all_authors()
                    return render_template("edit_book.html", book=book, authors=authors)

            authors = AuthorService.get_all_authors()
            return render_template("edit_book.html", book=book, authors=authors)

        except (ValidationError, ServiceError) as e:
            flash_error(str(e))
            return redirect(url_for("homepage"))

    @app.route("/book/<int:book_id>/rate", methods=["POST"])
    def rate_book(book_id: int):
        """
        Rate a book with a score from 1 to 10.
        :param book_id: Book ID
        :return: Redirect to book detail page
        """
        try:
            rating_str = safe_get_form_data(request.form, 'rating', '')
            if not rating_str:
                flash_error("Rating is required.")
                return redirect(url_for("book_detail", book_id=book_id))

            rating = float(rating_str)
            book = BookService.rate_book(book_id, rating)
            flash_success(f"Successfully rated '{book.title}' with {rating}/10!")

        except ValueError:
            flash_error("Invalid rating value. Please enter a number between 1 and 10.")
        except (ValidationError, ServiceError) as e:
            flash_error(str(e))

        return redirect(url_for("book_detail", book_id=book_id))

    @app.route("/book/<int:book_id>/delete", methods=["POST"])
    def delete_book(book_id: int):
        """
        Delete a book from the library.
        :param book_id: Book ID
        :return: Redirect to homepage
        """
        try:
            result = BookService.delete_book(book_id)

            if result['author_deleted']:
                flash_success(
                    f"Book '{result['book_title']}' and author "
                    f"'{result['author_name']}' successfully deleted."
                )
            else:
                flash_success(f"Book '{result['book_title']}' successfully deleted.")

        except ServiceError as e:
            flash_error(str(e))

        return redirect(url_for("homepage"))

    @app.route("/author/<int:author_id>")
    def author_detail(author_id: int):
        """
        Display detailed information about a specific author.
        :param author_id: Author ID
        :return: Author detail template or redirect
        """
        try:
            author = AuthorService.get_author_with_books(author_id)
            if not author:
                flash_error("Author not found.")
                return redirect(url_for("homepage"))

            books = getattr(author, '_books_ordered', author.books)

            return render_template("author_detail.html", author=author, books=books)

        except ServiceError as e:
            flash_error(str(e))
            return redirect(url_for("homepage"))

    @app.route("/author/<int:author_id>/edit", methods=["GET", "POST"])
    def edit_author(author_id: int):
        """
        Edit an existing author.
        :param author_id: Author ID
        :return: Edit author template or redirect
        """
        try:
            author = AuthorService.get_author_by_id(author_id)
            if not author:
                flash_error("Author not found.")
                return redirect(url_for("homepage"))

            if request.method == "POST":
                form_data = {
                    'name': safe_get_form_data(request.form, 'name', ''),
                    'birthdate': safe_get_form_data(request.form, 'birthdate'),
                    'date_of_death': safe_get_form_data(request.form, 'date_of_death')
                }

                updated_author = AuthorService.update_author(author_id, form_data)
                flash_success(f"Author '{updated_author.name}' successfully updated.")
                return redirect(url_for("author_detail", author_id=author_id))

            return render_template("edit_author.html", author=author)

        except (ValidationError, ServiceError) as e:
            flash_error(str(e))
            return redirect(url_for("homepage"))

    @app.route("/author/<int:author_id>/delete", methods=["POST"])
    def delete_author(author_id: int):
        """
        Delete an author and all their books from the library.
        :param author_id: Author ID
        :return: Redirect to homepage
        """
        try:
            result = AuthorService.delete_author(author_id)

            if result['book_count'] > 0:
                flash_success(
                    f"Author '{result['author_name']}' and {result['book_count']} "
                    f"book{'s' if result['book_count'] != 1 else ''} successfully deleted."
                )
            else:
                flash_success(f"Author '{result['author_name']}' successfully deleted.")

        except ServiceError as e:
            flash_error(str(e))

        return redirect(url_for("homepage"))

    @app.route("/api/books")
    def api_books():
        """
        API endpoint to get all books as JSON.
        :return: JSON response with books data
        """
        try:
            search_query = request.args.get('search', '')
            sort_by = request.args.get('sort', 'title')

            books = BookService.get_all_books(search_query, sort_by)
            books_data = [book.to_dict() for book in books]

            return jsonify({
                'success': True,
                'books': books_data,
                'count': len(books_data)
            })

        except ServiceError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route("/api/authors")
    def api_authors():
        """
        API endpoint to get all authors as JSON.
        :return: JSON response with authors data
        """
        try:
            authors = AuthorService.get_all_authors()
            authors_data = [author.to_dict() for author in authors]

            return jsonify({
                'success': True,
                'authors': authors_data,
                'count': len(authors_data)
            })

        except ServiceError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route("/api/book/<int:book_id>/cover")
    def get_book_cover_api(book_id: int):
        """
        API endpoint to get book cover asynchronously.
        :param book_id: Book ID
        :return: JSON response with cover URL
        """
        try:
            book = BookService.get_book_by_id(book_id)
            if not book:
                return jsonify({'error': 'Book not found'}), 404

            cover_url = book.cover_url
            return jsonify({'cover_url': cover_url})

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route("/api/book/<int:book_id>/refresh-cover", methods=["POST"])
    def refresh_book_cover_api(book_id: int):
        """
        API endpoint to refresh a book's cover.
        :param book_id: Book ID
        :return: JSON response with refreshed cover URL
        """
        try:
            cover_url = refresh_book_cover(book_id)

            if cover_url:
                return jsonify({
                    'success': True,
                    'cover_url': cover_url
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Book not found'
                }), 404

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


app = create_app()


if __name__ == "__main__":
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )