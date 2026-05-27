"""Configuration management for Office-QA Agent."""

from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class LLMConfig(BaseSettings):
    """LLM Provider Configuration."""
    provider: Literal["openai", "anthropic", "gemini", "openrouter"] = "openai"
    api_key: str = Field(default="", description="API key for LLM provider")
    reasoning_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    fast_model: str = "gpt-3.5-turbo"
    max_tokens: int = 4096
    temperature: float = 0.1
    enable_caching: bool = True

    class Config:
        env_prefix = "LLM_"
        case_sensitive = False


class RetrievalConfig(BaseSettings):
    """Retrieval System Configuration."""
    chunk_size: int = 512
    chunk_overlap: int = 128
    min_chunk_size: int = 100
    max_chunk_size: int = 2048
    
    # Embedding
    embedding_dim: int = 384
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Retrieval
    top_k: int = 5
    rerank_top_k: int = 3
    use_bm25: bool = True
    use_dense: bool = True
    use_reranker: bool = True
    
    # Indexing
    index_type: Literal["faiss", "lance", "chroma"] = "faiss"
    persist_index: bool = True
    index_dir: str = "data/indices"
    
    # Metadata filtering
    enable_metadata_filtering: bool = True
    enable_temporal_filtering: bool = True

    class Config:
        env_prefix = "RETRIEVAL_"
        case_sensitive = False


class ParsingConfig(BaseSettings):
    """Document Parsing Configuration."""
    max_file_size_mb: int = 100
    supported_formats: list[str] = ["pdf", "txt", "docx", "xlsx", "csv"]
    enable_ocr: bool = False
    table_extraction_strategy: Literal["docling", "pymupdf", "pandas"] = "pandas"
    enable_hierarchical_parsing: bool = True
    cache_parsed_docs: bool = True
    parse_cache_dir: str = "data/parse_cache"

    class Config:
        env_prefix = "PARSING_"
        case_sensitive = False


class SQLConfig(BaseSettings):
    """SQL Engine Configuration."""
    engine_type: Literal["sqlite", "duckdb", "pandas"] = "duckdb"
    db_path: str = "data/qa_engine.db"
    enable_query_optimization: bool = True
    max_query_time: float = 10.0
    enable_query_logging: bool = True

    class Config:
        env_prefix = "SQL_"
        case_sensitive = False


class ReasoningConfig(BaseSettings):
    """Reasoning Pipeline Configuration."""
    max_reasoning_steps: int = 10
    enable_confidence_scoring: bool = True
    confidence_threshold: float = 0.6
    enable_self_verification: bool = True
    max_parallel_retrievals: int = 3
    enable_query_decomposition: bool = True
    hallucination_check: bool = True
    require_evidence: bool = True

    class Config:
        env_prefix = "REASONING_"
        case_sensitive = False


class EvaluationConfig(BaseSettings):
    """Evaluation Configuration."""
    benchmark_dir: str = "data/benchmarks"
    results_dir: str = "data/results"
    track_accuracy: bool = True
    track_latency: bool = True
    track_cost: bool = True
    track_retrieval_quality: bool = True
    save_traces: bool = True
    traces_dir: str = "data/traces"

    class Config:
        env_prefix = "EVALUATION_"
        case_sensitive = False


class LoggingConfig(BaseSettings):
    """Logging Configuration."""
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_dir: str = "logs"
    enable_console_logging: bool = True
    enable_file_logging: bool = True
    enable_json_logging: bool = True
    retention_days: int = 30
    max_log_size_mb: int = 100

    class Config:
        env_prefix = "LOGGING_"
        case_sensitive = False


class Settings(BaseSettings):
    """Main settings object combining all configurations."""
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    
    # Sub-configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    parsing: ParsingConfig = Field(default_factory=ParsingConfig)
    sql: SQLConfig = Field(default_factory=SQLConfig)
    reasoning: ReasoningConfig = Field(default_factory=ReasoningConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # System
    batch_size: int = 32
    num_workers: int = 4
    enable_cache: bool = True
    cache_dir: str = "data/cache"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls()


# Global settings instance
settings = Settings()
