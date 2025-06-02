"""
Test configuration for the Digital Library application.
This file contains configuration settings specifically for testing.
"""

import os
import tempfile


class TestConfig:
    """Testing configuration."""
    TESTING = True

    # Use in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for testing
    SECRET_KEY = 'test-secret-key-for-testing-only'

    # Disable CSRF for easier testing
    WTF_CSRF_ENABLED = False

    # Flask settings
    DEBUG = True
    HOST = '127.0.0.1'
    PORT = 5000

    # Disable external API calls during testing
    GOOGLE_BOOKS_API_KEY = None

    # Fast bcrypt rounds for testing
    BCRYPT_LOG_ROUNDS = 4


# Add the testing config to your existing config dictionary
# You can either modify your config.py or import this in your tests

def get_test_config():
    """Get test configuration"""
    return TestConfig


# Alternative: Patch the original config
def patch_config_for_testing():
    """
    Monkey patch the config module to include testing configuration.
    Call this before importing your app in tests.
    """
    try:
        import config
        config.config['testing'] = TestConfig
        return True
    except ImportError:
        return False