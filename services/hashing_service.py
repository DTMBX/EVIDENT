""" 
Evident Hashing Service
Forensic-grade SHA-256 computation for evidence integrity

Evidence-grade requirements:
- Streaming (support multi-GB video files)
- Deterministic (same file → same hash always)
- Cryptographically secure (SHA-256, not MD5)

Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
PROPRIETARY — See LICENSE.
"""

import hashlib
from pathlib import Path
from typing import BinaryIO


def compute_sha256_file(file_path: Path) -> str:
    """
    Compute SHA-256 hash of file on disk.

    Args:
        file_path: Absolute path to file

    Returns:
        64-character hex string (SHA-256 digest)

    Example:
        >>> from pathlib import Path
        >>> hash_val = compute_sha256_file(Path("evidence.mp4"))
        >>> len(hash_val)
        64
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read in 4KB chunks (balance speed + memory)
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def compute_sha256_stream(file_obj: BinaryIO) -> str:
    """
    Compute SHA-256 hash of file-like object (e.g., Flask request.files).

    Args:
        file_obj: Binary file-like object with read() method

    Returns:
        64-character hex string (SHA-256 digest)

    Notes:
        - Does NOT reset file position (caller's responsibility)
        - Used for computing hash during upload before saving to disk

    Example:
        >>> from io import BytesIO
        >>> stream = BytesIO(b"evidence data")
        >>> hash_val = compute_sha256_stream(stream)
        >>> len(hash_val)
        64
    """
    sha256_hash = hashlib.sha256()

    # Read in 4KB chunks
    for chunk in iter(lambda: file_obj.read(4096), b""):
        sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def verify_file_hash(file_path: Path, expected_hash: str) -> bool:
    """
    Verify file integrity by comparing computed hash to expected value.

    Args:
        file_path: Path to file to verify
        expected_hash: Expected SHA-256 hash (64 hex chars)

    Returns:
        True if computed hash matches expected, False otherwise

    Example:
        >>> verify_file_hash(Path("evidence.mp4"), "abc123...")
        True
    """
    if len(expected_hash) != 64:
        raise ValueError(f"Invalid SHA-256 hash length: {len(expected_hash)} (expected 64)")

    computed = compute_sha256_file(file_path)
    return computed.lower() == expected_hash.lower()
