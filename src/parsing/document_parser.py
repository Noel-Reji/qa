"""Document parsing and ingestion."""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
import hashlib

from src.utils import (
    Document,
    DocumentType,
    Metadata,
    Chunk,
    ChunkType,
    generate_id,
    Timer,
)
from src.config import settings
from src.logging import get_logger

logger = get_logger("parsing")


class DocumentParser:
    """Base class for document parsing."""

    def __init__(self):
        self.config = settings.parsing

    def parse(self, file_path: Path) -> Optional[Document]:
        """Parse a document."""
        raise NotImplementedError

    def _create_metadata(self, file_path: Path, filename: str) -> Metadata:
        """Create document metadata."""
        stat = os.stat(file_path)
        return Metadata(
            document_id=generate_id("doc"),
            filename=filename,
            document_type=self._detect_type(file_path),
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
        )

    def _detect_type(self, file_path: Path) -> DocumentType:
        """Detect document type from file extension."""
        ext = file_path.suffix.lower()[1:]
        try:
            return DocumentType(ext)
        except ValueError:
            logger.warning(f"Unknown file type: {ext}, defaulting to txt")
            return DocumentType.TXT


class TextDocumentParser(DocumentParser):
    """Parser for plain text documents."""

    def parse(self, file_path: Path) -> Optional[Document]:
        """Parse a text document."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = self._create_metadata(file_path, file_path.name)
            doc = Document(
                document_id=metadata.document_id,
                filename=file_path.name,
                document_type=DocumentType.TXT,
                content=content,
                metadata=metadata,
            )

            # Create chunks
            doc.chunks = self._chunk_content(content, metadata)
            logger.info(f"Parsed text document: {file_path.name} ({len(doc.chunks)} chunks)")
            return doc

        except Exception as e:
            logger.error(f"Error parsing text document {file_path}: {e}")
            return None

    def _chunk_content(self, content: str, metadata: Metadata) -> List[Chunk]:
        """Chunk text content."""
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        # Split by paragraphs first
        paragraphs = content.split('\n\n')

        current_chunk = ""
        position = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunk = Chunk(
                        chunk_id=generate_id("chunk"),
                        content=current_chunk.strip(),
                        chunk_type=ChunkType.TEXT,
                        metadata=metadata,
                        position=position,
                        confidence=1.0,
                    )
                    chunks.append(chunk)
                    position += 1

                current_chunk = para + "\n\n"

        if current_chunk:
            chunk = Chunk(
                chunk_id=generate_id("chunk"),
                content=current_chunk.strip(),
                chunk_type=ChunkType.TEXT,
                metadata=metadata,
                position=position,
                confidence=1.0,
            )
            chunks.append(chunk)

        return chunks


class PDFDocumentParser(DocumentParser):
    """Parser for PDF documents."""

    def parse(self, file_path: Path) -> Optional[Document]:
        """Parse a PDF document."""
        try:
            import pymupdf  # PyMuPDF

            metadata = self._create_metadata(file_path, file_path.name)
            doc = Document(
                document_id=metadata.document_id,
                filename=file_path.name,
                document_type=DocumentType.PDF,
                content="",
                metadata=metadata,
            )

            pdf = pymupdf.open(file_path)
            all_text = ""
            chunks = []

            for page_num in range(len(pdf)):
                page = pdf[page_num]
                text = page.get_text()
                all_text += text + "\n"

                # Extract tables from page if possible
                tables = self._extract_tables_from_page(page, metadata)
                doc.tables.extend(tables)

            pdf.close()

            doc.content = all_text
            doc.chunks = self._chunk_content(all_text, metadata)

            logger.info(f"Parsed PDF: {file_path.name} ({len(doc.chunks)} chunks, {len(doc.tables)} tables)")
            return doc

        except ImportError:
            logger.warning("PyMuPDF not installed, falling back to text parser")
            return TextDocumentParser().parse(file_path)
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            return None

    def _extract_tables_from_page(self, page, metadata: Metadata) -> List[Dict[str, Any]]:
        """Extract tables from a PDF page."""
        tables = []
        try:
            # Try to find tables in page
            import pymupdf
            found_tables = page.find_tables()

            for table in found_tables:
                table_dict = {
                    "table_id": generate_id("table"),
                    "data": table.extract(),
                    "metadata": {
                        "page": page.number,
                        "document_id": metadata.document_id,
                    }
                }
                tables.append(table_dict)
        except Exception as e:
            logger.debug(f"Could not extract tables from page: {e}")

        return tables

    def _chunk_content(self, content: str, metadata: Metadata) -> List[Chunk]:
        """Chunk PDF content."""
        return TextDocumentParser()._chunk_content(content, metadata)


class CSVDocumentParser(DocumentParser):
    """Parser for CSV documents."""

    def parse(self, file_path: Path) -> Optional[Document]:
        """Parse a CSV document."""
        try:
            import pandas as pd

            metadata = self._create_metadata(file_path, file_path.name)
            df = pd.read_csv(file_path)

            doc = Document(
                document_id=metadata.document_id,
                filename=file_path.name,
                document_type=DocumentType.CSV,
                content=df.to_string(),
                metadata=metadata,
            )

            # Store table data
            doc.tables = [
                {
                    "table_id": generate_id("table"),
                    "data": df,
                    "columns": df.columns.tolist(),
                    "rows": len(df),
                }
            ]

            # Create chunk for the entire table
            chunk = Chunk(
                chunk_id=generate_id("chunk"),
                content=df.to_string(),
                chunk_type=ChunkType.TABLE,
                metadata=metadata,
                position=0,
                confidence=1.0,
            )
            doc.chunks = [chunk]

            logger.info(f"Parsed CSV: {file_path.name} (1 table chunk, {len(df)} rows)")
            return doc

        except ImportError:
            logger.error("pandas not installed, cannot parse CSV")
            return None
        except Exception as e:
            logger.error(f"Error parsing CSV {file_path}: {e}")
            return None


class DocumentParsingEngine:
    """Main document parsing engine."""

    def __init__(self):
        self.parsers = {
            DocumentType.TXT: TextDocumentParser(),
            DocumentType.PDF: PDFDocumentParser(),
            DocumentType.CSV: CSVDocumentParser(),
        }
        self.cache_dir = Path(settings.parsing.parse_cache_dir)
        if settings.parsing.cache_parsed_docs:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def parse_document(self, file_path: Path) -> Optional[Document]:
        """Parse a document."""
        file_path = Path(file_path)

        # Check cache
        if settings.parsing.cache_parsed_docs:
            cached_doc = self._load_from_cache(file_path)
            if cached_doc:
                logger.info(f"Loaded {file_path.name} from cache")
                return cached_doc

        # Detect type and parse
        doc_type = self._detect_type(file_path)
        parser = self.parsers.get(doc_type)

        if not parser:
            logger.warning(f"No parser for document type: {doc_type}")
            parser = TextDocumentParser()

        with Timer() as timer:
            doc = parser.parse(file_path)

        if doc and settings.parsing.cache_parsed_docs:
            self._save_to_cache(doc)

        logger.info(f"Document parsing took {timer.elapsed_ms:.1f}ms")
        return doc

    def parse_directory(self, directory: Path) -> List[Document]:
        """Parse all documents in a directory."""
        directory = Path(directory)
        documents = []

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower()[1:] in [d.value for d in DocumentType]:
                doc = self.parse_document(file_path)
                if doc:
                    documents.append(doc)

        logger.info(f"Parsed {len(documents)} documents from {directory}")
        return documents

    def _detect_type(self, file_path: Path) -> DocumentType:
        """Detect document type."""
        ext = file_path.suffix.lower()[1:]
        try:
            return DocumentType(ext)
        except ValueError:
            return DocumentType.TXT

    def _get_cache_path(self, file_path: Path) -> Path:
        """Get cache file path for a document."""
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()
        return self.cache_dir / f"{file_hash}.json"

    def _load_from_cache(self, file_path: Path) -> Optional[Document]:
        """Load document from cache."""
        cache_path = self._get_cache_path(file_path)
        if not cache_path.exists():
            return None

        # Check if cache is still valid
        if cache_path.stat().st_mtime < file_path.stat().st_mtime:
            return None

        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            # Reconstruct document from cached data
            logger.debug(f"Loaded {file_path.name} from cache")
            return None  # TODO: Implement proper deserialization
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def _save_to_cache(self, doc: Document) -> None:
        """Save document to cache."""
        try:
            cache_path = self._get_cache_path(Path(doc.metadata.filename))
            with open(cache_path, 'w') as f:
                json.dump(doc.to_dict(include_content=False), f)
            logger.debug(f"Cached document: {doc.filename}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
