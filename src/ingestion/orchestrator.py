"""Ingestion and orchestration system."""

from pathlib import Path
from typing import List, Optional, Dict, Any

from src.utils import Document, Chunk
from src.parsing import DocumentParsingEngine
from src.retrieval import HybridRetriever
from src.reasoning import MultiStageReasoningAgent
from src.config import settings
from src.logging import get_logger

logger = get_logger("ingestion")


class DocumentCorpus:
    """Manages the document corpus."""

    def __init__(self):
        self.documents: List[Document] = []
        self.chunks: List[Chunk] = []
        self.document_map: Dict[str, Document] = {}

    def add_document(self, document: Document) -> None:
        """Add a document to corpus."""
        self.documents.append(document)
        self.document_map[document.document_id] = document
        self.chunks.extend(document.chunks)
        logger.info(f"Added document: {document.filename} ({len(document.chunks)} chunks)")

    def add_documents(self, documents: List[Document]) -> None:
        """Add multiple documents."""
        for doc in documents:
            self.add_document(doc)

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self.document_map.get(document_id)

    def remove_document(self, document_id: str) -> None:
        """Remove document from corpus."""
        if document_id in self.document_map:
            doc = self.document_map.pop(document_id)
            self.documents = [d for d in self.documents if d.document_id != document_id]
            self.chunks = [c for c in self.chunks if c.metadata.document_id != document_id]
            logger.info(f"Removed document: {doc.filename}")

    def get_stats(self) -> Dict[str, Any]:
        """Get corpus statistics."""
        return {
            "num_documents": len(self.documents),
            "num_chunks": len(self.chunks),
            "num_tables": sum(len(d.tables) for d in self.documents),
            "total_chars": sum(len(d.content) for d in self.documents),
        }


class OfficeQASystem:
    """Main Office-QA system orchestrator."""

    def __init__(self):
        self.parser = DocumentParsingEngine()
        self.corpus = DocumentCorpus()
        self.retriever = HybridRetriever()
        self.agent = MultiStageReasoningAgent(self.retriever)
        self.logger = logger

    def ingest_documents(self, file_paths: List[Path]) -> int:
        """Ingest documents into system."""
        parsed_count = 0

        for file_path in file_paths:
            doc = self.parser.parse_document(Path(file_path))
            if doc:
                self.corpus.add_document(doc)
                parsed_count += 1
            else:
                self.logger.warning(f"Failed to parse: {file_path}")

        # Index for retrieval
        if self.corpus.chunks:
            self.retriever.index_chunks(self.corpus.chunks)

        self.logger.info(f"Ingested {parsed_count} documents")
        return parsed_count

    def ingest_directory(self, directory: Path) -> int:
        """Ingest all documents from directory."""
        directory = Path(directory)
        self.logger.info(f"Ingesting documents from: {directory}")

        docs = self.parser.parse_directory(directory)
        self.corpus.add_documents(docs)

        if self.corpus.chunks:
            self.retriever.index_chunks(self.corpus.chunks)

        self.logger.info(f"Ingested {len(docs)} documents")
        return len(docs)

    def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a question about the corpus."""
        if not self.corpus.chunks:
            self.logger.error("No documents in corpus")
            return {
                "answer": "No documents in corpus",
                "confidence": 0.0,
                "error": "No corpus",
            }

        answer = self.agent.answer_question(question)

        return {
            "answer": answer.answer_text,
            "confidence": answer.confidence_score,
            "evidence": [e.to_dict() for e in answer.evidence],
            "reasoning": answer.reasoning_steps,
            "sources": answer.evidence[0].source_document if answer.evidence else None,
            "is_grounded": answer.is_grounded,
            "metadata": answer.metadata,
        }

    def batch_answer_questions(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Answer multiple questions."""
        results = []

        for question in questions:
            result = self.answer_question(question)
            results.append(result)

        return results

    def get_corpus_stats(self) -> Dict[str, Any]:
        """Get corpus statistics."""
        stats = self.corpus.get_stats()
        self.logger.info(f"Corpus stats: {stats}")
        return stats

    def clear_corpus(self) -> None:
        """Clear corpus."""
        self.corpus = DocumentCorpus()
        self.logger.info("Corpus cleared")


# Global system instance
_system: Optional[OfficeQASystem] = None


def get_system() -> OfficeQASystem:
    """Get or create system instance."""
    global _system
    if _system is None:
        _system = OfficeQASystem()
    return _system


def initialize_system() -> OfficeQASystem:
    """Initialize system."""
    system = get_system()
    logger.info("Office-QA system initialized")
    return system
