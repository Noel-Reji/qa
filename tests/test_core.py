"""Tests for Office-QA system."""

import pytest
from pathlib import Path
from src.utils import (
    Metadata,
    Chunk,
    ChunkType,
    DocumentType,
    generate_id,
    extract_numbers,
    cosine_similarity,
)
from datetime import datetime


class TestDataModels:
    """Tests for data models."""

    def test_generate_id(self):
        """Test ID generation."""
        id1 = generate_id("test")
        id2 = generate_id("test")
        assert id1.startswith("test_")
        assert id1 != id2

    def test_metadata(self):
        """Test metadata creation."""
        metadata = Metadata(
            document_id="doc1",
            filename="test.pdf",
            document_type=DocumentType.PDF,
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        assert metadata.document_id == "doc1"
        assert metadata.document_type == DocumentType.PDF

    def test_chunk(self):
        """Test chunk creation."""
        metadata = Metadata(
            document_id="doc1",
            filename="test.pdf",
            document_type=DocumentType.PDF,
            created_at=datetime.now(),
            modified_at=datetime.now(),
        )
        chunk = Chunk(
            chunk_id="chunk1",
            content="Test content",
            chunk_type=ChunkType.TEXT,
            metadata=metadata,
        )
        assert chunk.chunk_id == "chunk1"
        assert chunk.content == "Test content"


class TestHelpers:
    """Tests for helper functions."""

    def test_extract_numbers(self):
        """Test number extraction."""
        text = "The total is 123.45 and the average is 67.89"
        numbers = extract_numbers(text)
        assert 123.45 in numbers
        assert 67.89 in numbers

    def test_cosine_similarity(self):
        """Test cosine similarity."""
        vec1 = [1, 0, 0]
        vec2 = [1, 0, 0]
        sim = cosine_similarity(vec1, vec2)
        assert abs(sim - 1.0) < 0.001

        vec3 = [0, 1, 0]
        sim2 = cosine_similarity(vec1, vec3)
        assert abs(sim2) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
