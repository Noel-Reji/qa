"""Configuration Reference Guide

All available configuration options for the Office-QA system.
"""

# LLM Configuration
LLM_PROVIDER
  Type: str (openai | anthropic | gemini | openrouter)
  Default: openai
  Description: LLM provider to use for reasoning and synthesis

LLM_API_KEY
  Type: str (required)
  Default: None
  Description: API key for the LLM provider

LLM_REASONING_MODEL
  Type: str
  Default: gpt-4-turbo-preview
  Description: Model used for reasoning (must support 4K+ context)

LLM_EMBEDDING_MODEL
  Type: str
  Default: text-embedding-3-small
  Description: Model used for document embeddings

LLM_FAST_MODEL
  Type: str
  Default: gpt-3.5-turbo
  Description: Faster model for simple queries

LLM_MAX_TOKENS
  Type: int
  Default: 4096
  Description: Maximum tokens for LLM output

LLM_TEMPERATURE
  Type: float
  Default: 0.1
  Description: Temperature for LLM sampling (0.0-1.0)

LLM_ENABLE_CACHING
  Type: bool
  Default: true
  Description: Cache LLM responses for identical queries


# Retrieval Configuration
RETRIEVAL_CHUNK_SIZE
  Type: int
  Default: 512
  Description: Size of text chunks for retrieval (characters)

RETRIEVAL_CHUNK_OVERLAP
  Type: int
  Default: 128
  Description: Overlap between consecutive chunks (characters)

RETRIEVAL_MIN_CHUNK_SIZE
  Type: int
  Default: 100
  Description: Minimum chunk size (skip smaller chunks)

RETRIEVAL_MAX_CHUNK_SIZE
  Type: int
  Default: 2048
  Description: Maximum chunk size (split larger chunks)

RETRIEVAL_EMBEDDING_DIM
  Type: int
  Default: 384
  Description: Embedding dimension size

RETRIEVAL_EMBEDDING_MODEL
  Type: str
  Default: sentence-transformers/all-MiniLM-L6-v2
  Description: Sentence transformer model for embeddings

RETRIEVAL_TOP_K
  Type: int
  Default: 5
  Description: Number of top results to retrieve

RETRIEVAL_RERANK_TOP_K
  Type: int
  Default: 3
  Description: Number of results to rerank (after initial retrieval)

RETRIEVAL_USE_BM25
  Type: bool
  Default: true
  Description: Use BM25 for sparse keyword-based retrieval

RETRIEVAL_USE_DENSE
  Type: bool
  Default: true
  Description: Use dense embeddings for semantic retrieval

RETRIEVAL_USE_RERANKER
  Type: bool
  Default: true
  Description: Use cross-encoder reranking

RETRIEVAL_INDEX_TYPE
  Type: str (faiss | lance | chroma)
  Default: faiss
  Description: Index type for embeddings

RETRIEVAL_PERSIST_INDEX
  Type: bool
  Default: true
  Description: Save index to disk for persistence

RETRIEVAL_INDEX_DIR
  Type: str
  Default: data/indices
  Description: Directory for persisting indices

RETRIEVAL_ENABLE_METADATA_FILTERING
  Type: bool
  Default: true
  Description: Enable metadata-based filtering

RETRIEVAL_ENABLE_TEMPORAL_FILTERING
  Type: bool
  Default: true
  Description: Enable temporal-based filtering


# Parsing Configuration
PARSING_MAX_FILE_SIZE_MB
  Type: int
  Default: 100
  Description: Maximum file size to process

PARSING_SUPPORTED_FORMATS
  Type: list[str]
  Default: [pdf, txt, docx, xlsx, csv]
  Description: Supported file formats

PARSING_ENABLE_OCR
  Type: bool
  Default: false
  Description: Enable OCR for scanned documents

PARSING_TABLE_EXTRACTION_STRATEGY
  Type: str (docling | pymupdf | pandas)
  Default: pandas
  Description: Strategy for extracting tables from documents

PARSING_ENABLE_HIERARCHICAL_PARSING
  Type: bool
  Default: true
  Description: Parse documents hierarchically (sections, paragraphs)

PARSING_CACHE_PARSED_DOCS
  Type: bool
  Default: true
  Description: Cache parsed documents for faster reprocessing

PARSING_PARSE_CACHE_DIR
  Type: str
  Default: data/parse_cache
  Description: Directory for caching parsed documents


# SQL Configuration
SQL_ENGINE_TYPE
  Type: str (sqlite | duckdb | pandas)
  Default: duckdb
  Description: SQL engine for table reasoning

SQL_DB_PATH
  Type: str
  Default: data/qa_engine.db
  Description: Path to database file

SQL_ENABLE_QUERY_OPTIMIZATION
  Type: bool
  Default: true
  Description: Optimize SQL queries before execution

SQL_MAX_QUERY_TIME
  Type: float
  Default: 10.0
  Description: Maximum query execution time (seconds)

SQL_ENABLE_QUERY_LOGGING
  Type: bool
  Default: true
  Description: Log executed SQL queries


# Reasoning Configuration
REASONING_MAX_REASONING_STEPS
  Type: int
  Default: 10
  Description: Maximum number of reasoning steps

REASONING_ENABLE_CONFIDENCE_SCORING
  Type: bool
  Default: true
  Description: Compute confidence scores for answers

REASONING_CONFIDENCE_THRESHOLD
  Type: float
  Default: 0.6
  Description: Minimum confidence threshold for accepting answers

REASONING_ENABLE_SELF_VERIFICATION
  Type: bool
  Default: true
  Description: Perform self-verification on answers

REASONING_MAX_PARALLEL_RETRIEVALS
  Type: int
  Default: 3
  Description: Maximum parallel retrieval operations

REASONING_ENABLE_QUERY_DECOMPOSITION
  Type: bool
  Default: true
  Description: Decompose complex queries into subqueries

REASONING_HALLUCINATION_CHECK
  Type: bool
  Default: true
  Description: Check for hallucinations in answers

REASONING_REQUIRE_EVIDENCE
  Type: bool
  Default: true
  Description: Require evidence for all answers


# Evaluation Configuration
EVALUATION_BENCHMARK_DIR
  Type: str
  Default: data/benchmarks
  Description: Directory for benchmark datasets

EVALUATION_RESULTS_DIR
  Type: str
  Default: data/results
  Description: Directory for evaluation results

EVALUATION_TRACK_ACCURACY
  Type: bool
  Default: true
  Description: Track accuracy metrics

EVALUATION_TRACK_LATENCY
  Type: bool
  Default: true
  Description: Track latency metrics

EVALUATION_TRACK_COST
  Type: bool
  Default: true
  Description: Track cost metrics

EVALUATION_TRACK_RETRIEVAL_QUALITY
  Type: bool
  Default: true
  Description: Track retrieval quality metrics

EVALUATION_SAVE_TRACES
  Type: bool
  Default: true
  Description: Save execution traces

EVALUATION_TRACES_DIR
  Type: str
  Default: data/traces
  Description: Directory for execution traces


# Logging Configuration
LOGGING_LOG_LEVEL
  Type: str (DEBUG | INFO | WARNING | ERROR | CRITICAL)
  Default: INFO
  Description: Logging level

LOGGING_LOG_DIR
  Type: str
  Default: logs
  Description: Directory for log files

LOGGING_ENABLE_CONSOLE_LOGGING
  Type: bool
  Default: true
  Description: Print logs to console

LOGGING_ENABLE_FILE_LOGGING
  Type: bool
  Default: true
  Description: Write logs to file

LOGGING_ENABLE_JSON_LOGGING
  Type: bool
  Default: true
  Description: Write structured JSON logs

LOGGING_RETENTION_DAYS
  Type: int
  Default: 30
  Description: Retain logs for this many days

LOGGING_MAX_LOG_SIZE_MB
  Type: int
  Default: 100
  Description: Maximum log file size before rotation


# System Configuration
ENVIRONMENT
  Type: str (development | staging | production)
  Default: development
  Description: Environment mode

DEBUG
  Type: bool
  Default: false
  Description: Enable debug mode

BATCH_SIZE
  Type: int
  Default: 32
  Description: Batch size for processing

NUM_WORKERS
  Type: int
  Default: 4
  Description: Number of worker threads

ENABLE_CACHE
  Type: bool
  Default: true
  Description: Enable caching system-wide

CACHE_DIR
  Type: str
  Default: data/cache
  Description: Directory for caching


# Example Configurations

## Development Setup (Fast, No Cost)
ENVIRONMENT=development
LLM_PROVIDER=openrouter
LLM_REASONING_MODEL=meta-llama/llama-2-70b
RETRIEVAL_USE_RERANKER=false
DEBUG=true
LOGGING_LOG_LEVEL=DEBUG

## Production Setup (Accurate, Cost-Optimized)
ENVIRONMENT=production
LLM_PROVIDER=openai
LLM_REASONING_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.0
REASONING_CONFIDENCE_THRESHOLD=0.8
RETRIEVAL_USE_RERANKER=true
RETRIEVAL_TOP_K=10
DEBUG=false
LOGGING_LOG_LEVEL=INFO

## High-Speed Setup (Fast, Lower Accuracy)
ENVIRONMENT=production
RETRIEVAL_TOP_K=3
RETRIEVAL_USE_RERANKER=false
REASONING_ENABLE_QUERY_DECOMPOSITION=false
LLM_FAST_MODEL=gpt-3.5-turbo
LLM_MAX_TOKENS=1024

## Premium Setup (Most Accurate, Highest Cost)
ENVIRONMENT=production
LLM_REASONING_MODEL=gpt-4-turbo-preview
RETRIEVAL_TOP_K=20
RETRIEVAL_USE_RERANKER=true
RETRIEVAL_RERANK_TOP_K=10
REASONING_CONFIDENCE_THRESHOLD=0.5
REASONING_HALLUCINATION_CHECK=true
REASONING_ENABLE_QUERY_DECOMPOSITION=true
