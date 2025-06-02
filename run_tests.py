#!/usr/bin/env python3
"""
Test runner for the Digital Library application.
This script sets up the environment correctly before running tests.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py -v                 # Verbose output
    python run_tests.py -k "test_book"     # Run specific tests
    python run_tests.py --cov              # With coverage
"""

import os
import sys
import subprocess


def setup_environment():
    """Setup environment variables for testing"""
    os.environ['FLASK_ENV'] = 'development'
    os.environ['TESTING'] = 'True'

    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)


def patch_config():
    """Patch the config to add testing configuration"""
    try:
        import config

        # Create testing config class
        class TestingConfig(config.Config):
            TESTING = True
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            SECRET_KEY = 'test-secret-key'
            WTF_CSRF_ENABLED = False
            DEBUG = True

        # Add to config dictionary
        config.config['testing'] = TestingConfig
        print("✅ Testing configuration added successfully")
        return True

    except ImportError as e:
        print(f"❌ Could not import config: {e}")
        return False
    except Exception as e:
        print(f"❌ Error setting up config: {e}")
        return False


def run_tests():
    """Run the test suite"""
    # Setup environment
    setup_environment()

    # Patch config
    if not patch_config():
        print("⚠️  Warning: Could not patch config, tests might fail")

    # Build pytest command
    pytest_args = ['pytest']

    # Add command line arguments
    if len(sys.argv) > 1:
        pytest_args.extend(sys.argv[1:])
    else:
        # Default arguments
        pytest_args.extend([
            'test_library.py',
            '-v',
            '--tb=short',
            '--color=yes'
        ])

    print(f"🧪 Running tests with command: {' '.join(pytest_args)}")
    print("=" * 60)

    # Run pytest
    try:
        result = subprocess.run(pytest_args, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()

    if exit_code == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")

    sys.exit(exit_code)