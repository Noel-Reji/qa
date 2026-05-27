"""Data models for Office-QA system."""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    HTML = "html"


class ChunkType(str, Enum):
    """Types of chunks."""
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    METADATA = "metadata"


@dataclass
class Metadata:
    """Document metadata."""
    document_id: str
    filename: str
    document_type: DocumentType
    created_at: datetime
    modified_at: datetime
    author: Optional[str] = None
    revision: int = 1
    page_numbers: Optional[List[int]] = None
    section: Optional[str] = None
    source_url: Optional[str] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "document_type": self.document_type.value,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "author": self.author,
            "revision": self.revision,
            "page_numbers": self.page_numbers,
            "section": self.section,
            "source_url": self.source_url,
            "custom_metadata": self.custom_metadata,
        }


@dataclass
class TableMetadata:
    """Metadata for table chunks."""
    table_id: str
    num_rows: int
    num_columns: int
    column_names: List[str]
    has_header: bool = True
    table_caption: Optional[str] = None
    table_source: Optional[str] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "table_id": self.table_id,
            "num_rows": self.num_rows,
            "num_columns": self.num_columns,
            "column_names": self.column_names,
            "has_header": self.has_header,
            "table_caption": self.table_caption,
            "table_source": self.table_source,
            "custom_metadata": self.custom_metadata,
        }


@dataclass
class Chunk:
    """A chunk of document content."""
    chunk_id: str
    content: str
    chunk_type: ChunkType
    metadata: Metadata
    embedding: Optional[List[float]] = None
    table_metadata: Optional[TableMetadata] = None
    position: int = 0  # Position in document
    retrieval_score: float = 0.0
    confidence: float = 1.0
    related_chunks: List[str] = field(default_factory=list)
    structured_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "chunk_type": self.chunk_type.value,
            "metadata": self.metadata.to_dict(),
            "position": self.position,
            "retrieval_score": self.retrieval_score,
            "confidence": self.confidence,
            "related_chunks": self.related_chunks,
            "structured_data": self.structured_data,
        }
        if self.table_metadata:
            data["table_metadata"] = self.table_metadata.to_dict()
        return data


@dataclass
class Document:
    """A document with metadata and chunks."""
    document_id: str
    filename: str
    document_type: DocumentType
    content: str
    metadata: Metadata
    chunks: List[Chunk] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    extracted_entities: List[str] = field(default_factory=list)
    lineage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_content: bool = True) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "document_id": self.document_id,
            "filename": self.filename,
            "document_type": self.document_type.value,
            "metadata": self.metadata.to_dict(),
            "chunks": [c.to_dict() for c in self.chunks],
            "tables": self.tables,
            "extracted_entities": self.extracted_entities,
            "lineage": self.lineage,
        }
        if include_content:
            data["content"] = self.content
        return data


@dataclass
class Question:
    """A question to be answered."""
    question_id: str
    query: str
    question_type: str  # e.g., "factual", "numerical", "comparative", "temporal"
    entities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    requires_computation: bool = False
    requires_table_reasoning: bool = False
    temporal_scope: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence:
    """Retrieved evidence for an answer."""
    chunk_id: str
    chunk_content: str
    relevance_score: float
    source_document: str
    page_number: Optional[int] = None
    is_table: bool = False
    table_metadata: Optional[TableMetadata] = None
    grounding_confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "chunk_id": self.chunk_id,
            "chunk_content": self.chunk_content,
            "relevance_score": self.relevance_score,
            "source_document": self.source_document,
            "page_number": self.page_number,
            "is_table": self.is_table,
            "grounding_confidence": self.grounding_confidence,
        }
        if self.table_metadata:
            data["table_metadata"] = self.table_metadata.to_dict()
        return data


@dataclass
class Answer:
    """Generated answer."""
    answer_id: str
    query: str
    answer_text: str
    confidence_score: float
    evidence: List[Evidence]
    reasoning_steps: List[str] = field(default_factory=list)
    citations: Dict[str, str] = field(default_factory=dict)
    is_grounded: bool = True
    contains_computation: bool = False
    extracted_numbers: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "answer_id": self.answer_id,
            "query": self.query,
            "answer_text": self.answer_text,
            "confidence_score": self.confidence_score,
            "evidence": [e.to_dict() for e in self.evidence],
            "reasoning_steps": self.reasoning_steps,
            "citations": self.citations,
            "is_grounded": self.is_grounded,
            "contains_computation": self.contains_computation,
            "extracted_numbers": self.extracted_numbers,
            "metadata": self.metadata,
        }


@dataclass
class EvaluationResult:
    """Evaluation result for a single query."""
    query_id: str
    question: str
    expected_answer: Optional[str]
    generated_answer: str
    exact_match: bool = False
    semantic_similarity: float = 0.0
    retrieval_recall: float = 0.0
    grounding_score: float = 0.0
    latency_ms: float = 0.0
    token_count: int = 0
    estimated_cost: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_id": self.query_id,
            "question": self.question,
            "expected_answer": self.expected_answer,
            "generated_answer": self.generated_answer,
            "exact_match": self.exact_match,
            "semantic_similarity": self.semantic_similarity,
            "retrieval_recall": self.retrieval_recall,
            "grounding_score": self.grounding_score,
            "latency_ms": self.latency_ms,
            "token_count": self.token_count,
            "estimated_cost": self.estimated_cost,
            "error": self.error,
        }
