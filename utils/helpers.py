"""
Utility functions for the application
"""

import os
import hashlib
from typing import Optional


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def ensure_directory(directory: str):
    """Ensure directory exists, create if not"""
    os.makedirs(directory, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove potentially dangerous characters
    keepcharacters = (" ", ".", "_", "-")
    return "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()


def format_clause_reference(
    section_number: Optional[str], clause_path: Optional[str]
) -> str:
    """Format a human-readable clause reference"""
    if clause_path:
        return f"Clause {clause_path}"
    elif section_number:
        return f"Section {section_number}"
    else:
        return "Clause (unnumbered)"


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + suffix
