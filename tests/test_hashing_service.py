"""
Unit tests for services/hashing_service.py
Forensic-grade SHA-256 hashing verification
"""

import hashlib
from io import BytesIO
from pathlib import Path

import pytest

from services.hashing_service import (
    compute_sha256_file,
    compute_sha256_stream,
    verify_file_hash,
)


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary test file with known content"""
    test_file = tmp_path / "test_evidence.txt"
    content = b"Evidence file content for testing"
    test_file.write_bytes(content)

    # Compute expected hash
    expected_hash = hashlib.sha256(content).hexdigest()

    return test_file, expected_hash


@pytest.fixture
def large_temp_file(tmp_path):
    """Create a large temporary file (> 1MB) to test streaming"""
    test_file = tmp_path / "large_evidence.dat"
    # 5MB of data (1024 * 1024 * 5 bytes)
    content = b"X" * (1024 * 1024 * 5)
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()

    return test_file, expected_hash


def test_compute_sha256_file_small(temp_file):
    """Test SHA-256 computation on small file"""
    file_path, expected_hash = temp_file

    computed_hash = compute_sha256_file(file_path)

    assert len(computed_hash) == 64, "SHA-256 should be 64 hex chars"
    assert computed_hash == expected_hash


def test_compute_sha256_file_large(large_temp_file):
    """Test SHA-256 computation on large file (streaming)"""
    file_path, expected_hash = large_temp_file

    computed_hash = compute_sha256_file(file_path)

    assert computed_hash == expected_hash


def test_compute_sha256_file_not_found():
    """Test error handling for missing file"""
    with pytest.raises(FileNotFoundError):
        compute_sha256_file(Path("/nonexistent/file.txt"))


def test_compute_sha256_stream():
    """Test SHA-256 computation on file stream"""
    content = b"Stream content for evidence"
    stream = BytesIO(content)

    computed_hash = compute_sha256_stream(stream)

    expected_hash = hashlib.sha256(content).hexdigest()
    assert computed_hash == expected_hash


def test_compute_sha256_stream_large():
    """Test SHA-256 on large stream (> 1MB)"""
    content = b"Y" * (1024 * 1024 * 3)  # 3MB
    stream = BytesIO(content)

    computed_hash = compute_sha256_stream(stream)

    expected_hash = hashlib.sha256(content).hexdigest()
    assert computed_hash == expected_hash


def test_verify_file_hash_success(temp_file):
    """Test successful hash verification"""
    file_path, expected_hash = temp_file

    result = verify_file_hash(file_path, expected_hash)

    assert result is True


def test_verify_file_hash_failure(temp_file):
    """Test failed hash verification (tampered file)"""
    file_path, _ = temp_file
    wrong_hash = "0" * 64  # Invalid hash

    result = verify_file_hash(file_path, wrong_hash)

    assert result is False


def test_verify_file_hash_case_insensitive(temp_file):
    """Test hash verification is case-insensitive"""
    file_path, expected_hash = temp_file

    result_lower = verify_file_hash(file_path, expected_hash.lower())
    result_upper = verify_file_hash(file_path, expected_hash.upper())

    assert result_lower is True
    assert result_upper is True


def test_verify_file_hash_invalid_length():
    """Test error handling for invalid hash length"""
    with pytest.raises(ValueError, match="Invalid SHA-256 hash length"):
        verify_file_hash(Path("dummy.txt"), "tooshort")


def test_deterministic_hashing(temp_file):
    """Test that same file produces same hash (deterministic)"""
    file_path, _ = temp_file

    hash1 = compute_sha256_file(file_path)
    hash2 = compute_sha256_file(file_path)

    assert hash1 == hash2, "Hashing must be deterministic"
