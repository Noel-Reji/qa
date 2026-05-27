"""Retrieval system with hybrid search capabilities."""

import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any
import pickle

from src.utils import Chunk, cosine_similarity, Timer, generate_id
from src.config import settings
from src.logging import get_logger

logger = get_logger("retrieval")


class BM25Retriever:
    """BM25 retriever for sparse retrieval."""

    def __init__(self):
        self.corpus: List[str] = []
        self.chunk_ids: List[str] = []
        self.k1 = 1.5
        self.b = 0.75
        self.idf: Dict[str, float] = {}
        self.doc_freqs: List[Dict[str, int]] = []

    def index(self, chunks: List[Chunk]) -> None:
        """Index chunks."""
        self.corpus = [chunk.content for chunk in chunks]
        self.chunk_ids = [chunk.chunk_id for chunk in chunks]

        # Build IDF
        doc_freq = {}
        for chunk in chunks:
            tokens = set(self._tokenize(chunk.content))
            for token in tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        self.doc_freqs = [self._get_doc_freq(chunk.content) for chunk in chunks]

        num_docs = len(chunks)
        for term, freq in doc_freq.items():
            self.idf[term] = np.log((num_docs - freq + 0.5) / (freq + 0.5) + 1)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Search for similar chunks."""
        query_tokens = self._tokenize(query)
        scores = []

        for i, doc_id in enumerate(self.chunk_ids):
            score = self._bm25_score(query_tokens, i)
            scores.append((doc_id, score))

        # Sort by score and return top-k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        return text.lower().split()

    def _get_doc_freq(self, text: str) -> Dict[str, int]:
        """Get term frequencies for document."""
        tokens = self._tokenize(text)
        freq = {}
        for token in tokens:
            freq[token] = freq.get(token, 0) + 1
        return freq

    def _bm25_score(self, query_tokens: List[str], doc_idx: int) -> float:
        """Compute BM25 score."""
        score = 0.0
        doc_len = len(self._tokenize(self.corpus[doc_idx]))
        avg_doc_len = sum(len(self._tokenize(doc)) for doc in self.corpus) / len(self.corpus)

        for token in query_tokens:
            if token not in self.idf:
                continue

            freq = self.doc_freqs[doc_idx].get(token, 0)
            idf = self.idf[token]

            numerator = idf * freq * (self.k1 + 1)
            denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / avg_doc_len)

            score += numerator / denominator

        return score


class DenseRetriever:
    """Dense retriever using embeddings."""

    def __init__(self):
        self.embeddings: List[List[float]] = []
        self.chunk_ids: List[str] = []
        self.model = None
        self._init_model()

    def _init_model(self):
        """Initialize embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            model_name = settings.retrieval.embedding_model
            self.model = SentenceTransformer(model_name)
            logger.info(f"Initialized embedding model: {model_name}")
        except ImportError:
            logger.error("sentence-transformers not installed")

    def index(self, chunks: List[Chunk]) -> None:
        """Index chunks with embeddings."""
        if not self.model:
            logger.warning("Embedding model not initialized")
            return

        self.chunk_ids = [chunk.chunk_id for chunk in chunks]
        contents = [chunk.content for chunk in chunks]

        with Timer() as timer:
            self.embeddings = self.model.encode(contents, convert_to_numpy=False)

        logger.info(f"Indexed {len(chunks)} chunks in {timer.elapsed_ms:.1f}ms")

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Search using dense embeddings."""
        if not self.model or not self.embeddings:
            logger.warning("Dense retriever not initialized")
            return []

        query_embedding = self.model.encode(query, convert_to_numpy=False)
        scores = []

        for i, chunk_id in enumerate(self.chunk_ids):
            # Convert to numpy for similarity computation
            sim = cosine_similarity(
                np.array(query_embedding).tolist(),
                np.array(self.embeddings[i]).tolist()
            )
            scores.append((chunk_id, float(sim)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class Reranker:
    """Reranker for candidate results."""

    def __init__(self):
        self.model = None
        self._init_model()

    def _init_model(self):
        """Initialize reranking model."""
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
            logger.info("Initialized reranker model")
        except ImportError:
            logger.warning("sentence-transformers not installed for reranking")

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[str, str, float]],
        top_k: int = 3
    ) -> List[Tuple[str, str, float]]:
        """Rerank candidates."""
        if not self.model:
            return candidates[:top_k]

        # Prepare input pairs
        pairs = [[query, doc] for _, doc, _ in candidates]

        scores = self.model.predict(pairs)

        # Combine with original scores
        reranked = []
        for i, (chunk_id, doc, original_score) in enumerate(candidates):
            combined_score = 0.7 * float(scores[i]) + 0.3 * original_score
            reranked.append((chunk_id, doc, combined_score))

        reranked.sort(key=lambda x: x[2], reverse=True)
        return reranked[:top_k]


class HybridRetriever:
    """Hybrid retriever combining multiple strategies."""

    def __init__(self):
        self.bm25 = BM25Retriever()
        self.dense = DenseRetriever()
        self.reranker = Reranker()
        self.chunks_map: Dict[str, Chunk] = {}

    def index_chunks(self, chunks: List[Chunk]) -> None:
        """Index chunks."""
        # Store mapping
        self.chunks_map = {chunk.chunk_id: chunk for chunk in chunks}

        # Index with both retrievers
        if settings.retrieval.use_bm25:
            self.bm25.index(chunks)

        if settings.retrieval.use_dense:
            self.dense.index(chunks)

        logger.info(f"Indexed {len(chunks)} chunks for hybrid retrieval")

    def retrieve(self, query: str, top_k: int = 5) -> List[Chunk]:
        """Retrieve relevant chunks."""
        candidates = {}

        # BM25 retrieval
        if settings.retrieval.use_bm25:
            bm25_results = self.bm25.search(query, top_k=top_k * 2)
            for chunk_id, score in bm25_results:
                if chunk_id not in candidates:
                    candidates[chunk_id] = {"bm25": score, "dense": 0.0}
                else:
                    candidates[chunk_id]["bm25"] = score

        # Dense retrieval
        if settings.retrieval.use_dense:
            dense_results = self.dense.search(query, top_k=top_k * 2)
            for chunk_id, score in dense_results:
                if chunk_id not in candidates:
                    candidates[chunk_id] = {"bm25": 0.0, "dense": score}
                else:
                    candidates[chunk_id]["dense"] = score

        # Combine scores
        combined_scores = []
        for chunk_id, scores in candidates.items():
            combined = (scores.get("bm25", 0.0) + scores.get("dense", 0.0)) / 2
            combined_scores.append((chunk_id, combined))

        combined_scores.sort(key=lambda x: x[1], reverse=True)

        # Get candidate chunks
        candidate_chunks = []
        for chunk_id, score in combined_scores[:top_k * 2]:
            chunk = self.chunks_map.get(chunk_id)
            if chunk:
                chunk.retrieval_score = score
                candidate_chunks.append((chunk_id, chunk.content, score))

        # Rerank if enabled
        if settings.retrieval.use_reranker:
            reranked = self.reranker.rerank(query, candidate_chunks, top_k)
            result_chunks = []
            for chunk_id, _, score in reranked:
                chunk = self.chunks_map[chunk_id]
                chunk.retrieval_score = score
                result_chunks.append(chunk)
            return result_chunks
        else:
            return [chunk for chunk_id, chunk, _ in candidate_chunks[:top_k]]

    def retrieve_with_metadata_filter(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[Chunk]:
        """Retrieve with metadata filtering."""
        results = self.retrieve(query, top_k=top_k * 3)

        if not metadata_filter:
            return results[:top_k]

        # Apply metadata filters
        filtered = []
        for chunk in results:
            if self._matches_filter(chunk, metadata_filter):
                filtered.append(chunk)

        return filtered[:top_k]

    def _matches_filter(self, chunk: Chunk, filter_dict: Dict[str, Any]) -> bool:
        """Check if chunk matches metadata filter."""
        for key, value in filter_dict.items():
            if key == "document_id":
                if chunk.metadata.document_id != value:
                    return False
            elif key == "section":
                if chunk.metadata.section != value:
                    return False
            # Add more filter types as needed

        return True


class RetrieverCache:
    """Cache for retrieval results."""

    def __init__(self, cache_dir: Path = Path("data/cache")):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Optional[List[Chunk]]:
        """Get cached result."""
        cache_file = self.cache_dir / f"{key}.pkl"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def set(self, key: str, results: List[Chunk]) -> None:
        """Cache result."""
        try:
            cache_file = self.cache_dir / f"{key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(results, f)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
