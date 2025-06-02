"""
Pytest configuration file for the Digital Library test suite.
This file contains shared fixtures and configuration for all tests.
"""

import pytest
import os
import sys
import tempfile
from datetime import date

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables for testing BEFORE importing anything
os.environ['FLASK_ENV'] = 'development'  # Use existing development config
os.environ['TESTING'] = 'True'

# Patch the config before importing app
def setup_test_config():
    """Setup test configuration before app import"""
    try:
        import config
        # Add testing config to existing config dict
        class TestConfig(config.Config):
            TESTING = True
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            SECRET_KEY = 'test-secret-key'
            WTF_CSRF_ENABLED = False
            DEBUG = True

        # Add to config dictionary
        config.config['testing'] = TestConfig
        return True
    except ImportError:
        return False

# Setup config before importing app
setup_test_config()

# Now import the app modules
from app import create_app
from models.models import db, Author, Book


@pytest.fixture(scope='function')
def app():
    """Create application for testing with fresh database for each test"""
    # Try to create app with testing config, fallback to development
    try:
        app = create_app('testing')
    except KeyError:
        # Fallback: create with development config and override
        app = create_app('development')
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'test-secret-key',
            'WTF_CSRF_ENABLED': False,
            'DEBUG': True
        })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def sample_author(app):
    """Create sample author for testing"""
    with app.app_context():
        author = Author(
            name="Jane Austen",
            birth_date=date(1775, 12, 16),
            date_of_death=date(1817, 7, 18)
        )
        db.session.add(author)
        db.session.commit()

        # Refresh to get the ID
        db.session.refresh(author)
        return author


@pytest.fixture
def living_author(app):
    """Create living author for testing"""
    with app.app_context():
        author = Author(
            name="Stephen King",
            birth_date=date(1947, 9, 21)
        )
        db.session.add(author)
        db.session.commit()

        # Refresh to get the ID
        db.session.refresh(author)
        return author


@pytest.fixture
def sample_book(app, sample_author):
    """Create sample book for testing"""
    with app.app_context():
        book = Book(
            title="Pride and Prejudice",
            isbn="9780141439518",
            publication_year=1813,
            author_id=sample_author.id,
            rating=8.5
        )
        db.session.add(book)
        db.session.commit()

        # Refresh to get the ID
        db.session.refresh(book)
        return book


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their names"""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid.lower() or "workflow" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        # Mark slow tests
        if "performance" in item.nodeid.lower() or "large_dataset" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
        # Mark unit tests (everything else)
        elif not any(marker.name in ['integration', 'slow'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)