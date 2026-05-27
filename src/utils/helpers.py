"""Utility functions and helpers."""

import hashlib
import time
from typing import Any, Optional
import uuid


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID."""
    uid = str(uuid.uuid4()).replace("-", "")
    return f"{prefix}_{uid}" if prefix else uid


def hash_string(s: str) -> str:
    """Hash a string."""
    return hashlib.md5(s.encode()).hexdigest()


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


class Timer:
    """Context manager for timing code."""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.end_time = time.time()

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000


def extract_numbers(text: str) -> list[float]:
    """Extract numbers from text."""
    import re
    # Pattern for integers and floats
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(m) for m in matches if m and m != '.']


def is_likely_number(text: str) -> bool:
    """Check if text is likely a number."""
    try:
        float(text.strip())
        return True
    except ValueError:
        return False


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    import re
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = text.strip()
    return text


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    import numpy as np
    
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same length")
    
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def batch_iterable(iterable, batch_size: int):
    """Batch an iterable."""
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
