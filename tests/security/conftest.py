"""
Pytest configuration for security tests.
Provides Flask app and database fixtures.
"""

import pytest
from flask import Flask

from models_auth import TierLevel, User, db


@pytest.fixture(scope="function")
def app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing

    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope="function")
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        yield db.session


@pytest.fixture(scope="function")
def client(app):
    """Create test client."""
    return app.test_client()
