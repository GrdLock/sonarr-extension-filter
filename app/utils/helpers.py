"""
Helper functions
"""

import hashlib


def calculate_hash(data):
    """
    Calculate SHA1 hash of data

    Args:
        data: Data to hash

    Returns:
        str: Hex digest
    """
    return hashlib.sha1(data).hexdigest()


def sanitize_filename(filename):
    """
    Sanitize filename for safe usage

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    return filename
