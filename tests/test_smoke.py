"""
Smoke test: verify test infrastructure works
No external dependencies required
"""
import sys


def test_python_version():
    """Verify Python 3.12+ is running"""
    assert sys.version_info >= (3, 12), f"Python 3.12+ required, got {sys.version_info}"


def test_basic_arithmetic():
    """Verify Python interpreter works"""
    assert 2 + 2 == 4


def test_imports():
    """Verify core dependencies can be imported"""
    try:
        import flask
        import sqlalchemy
        import pytest
        assert True
    except ImportError as e:
        assert False, f"Import failed: {e}"
