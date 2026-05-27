# Architecture Guide

## System Overview

The Office-QA system is a modular, production-grade document reasoning pipeline designed to answer complex questions about enterprise documents with high accuracy, low latency, and minimal cost.

## High-Level Architecture

```
Documents → Parsing → Chunks → Retriever → Evidence → Reasoner → Answer
                        ↓
                    Index (FAISS/
                    Embeddings)
```

## Core Modules

### 1. Document Parsing (`src/parsing/`)

**Purpose**: Convert documents into structured chunks for processing

**Components**:
- `DocumentParsingEngine` - Main orchestrator
- `TextDocumentParser` - Plain text files
- `PDFDocumentParser` - PDF documents  
- `CSVDocumentParser` - Tabular data

**Key Features**:
- Multi-format support (PDF, CSV, TXT, DOCX)
- Hierarchical chunking (paragraphs → sentences)
- Table extraction and preservation
- Metadata tracking (page numbers, section info)
- Parse caching for efficiency

**Output**: `Document` objects with `Chunk` list

### 2. Retrieval System (`src/retrieval/`)

**Purpose**: Find relevant evidence for a query

**Components**:
- `BM25Retriever` - Sparse, keyword-based retrieval
- `DenseRetriever` - Embedding-based semantic search
- `Reranker` - Cross-encoder reranking
- `HybridRetriever` - Combines all strategies
- `RetrieverCache` - Result caching

**Key Features**:
- Hybrid retrieval combines BM25 + dense
- Configurable reranking
- Metadata filtering support
- Score normalization and combination
- Result caching for common queries

**Pipeline**:
1. BM25 search → top 2K candidates
2. Dense search → top 2K candidates
3. Score combination and sorting
4. Cross-encoder reranking → top K
5. Return final chunks with scores

**Output**: Ranked `Chunk` list with retrieval scores

### 3. SQL Engine (`src/sql_engine/`)

**Purpose**: Handle table reasoning and numerical computations

**Components**:
- `SQLQueryExecutor` - Execute SQL queries (DuckDB/SQLite)
- `TableReasoningEngine` - NL-to-SQL and table QA
- `ComputationEngine` - Safe expression evaluation

**Key Features**:
- SQL execution with timeout protection
- Table extraction from text
- Basic NL-to-SQL conversion
- Fallback to pandas operations
- Safe expression evaluation

**Use Cases**:
- Sum/average/count operations
- Filtering and grouping
- Multi-table joins
- Temporal computations

**Output**: Computation results with reasoning steps

### 4. Reasoning Agent (`src/reasoning/`)

**Purpose**: Multi-stage reasoning pipeline for answer generation

**Stages**:

1. **Query Understanding**
   - Classify question type (factual/numerical/comparative/temporal)
   - Extract entities and keywords
   - Detect computation needs
   - Identify table reasoning requirements

2. **Retrieval Planning**
   - Choose retrieval strategy based on question type
   - Execute retrieval with appropriate top-k
   - Handle special cases (tables, metadata filtering)

3. **Evidence Validation**
   - Compute grounding confidence
   - Filter by confidence threshold
   - Rank evidence by relevance and grounding

4. **Computation**
   - Detect if computation is needed
   - Extract numbers and perform calculations
   - Execute SQL queries on tables

5. **Reasoning**
   - Synthesize answer from evidence
   - Combine multiple evidence chunks
   - Generate reasoning steps

6. **Verification**
   - Check consistency
   - Detect potential hallucinations
   - Validate grounding

**Output**: `Answer` object with confidence, evidence, and reasoning

### 5. Evaluation System (`src/evaluation/`)

**Purpose**: Benchmark and evaluate system performance

**Components**:
- `EvaluationMetrics` - Metric computations
- `BenchmarkEvaluator` - Batch evaluation

**Metrics**:
- **Accuracy**: Exact match percentage
- **Semantic Similarity**: Word overlap / embedding similarity
- **Retrieval Recall**: Expected sources retrieved
- **Grounding Score**: Evidence confidence
- **Latency**: End-to-end timing
- **Cost**: Token usage and estimated cost

**Output**: `EvaluationResult` objects with detailed metrics

### 6. Logging System (`src/logging/`)

**Purpose**: Structured logging and execution tracing

**Components**:
- `SystemLogger` - Main logger with console + file output
- `TraceLogger` - Execution trace logging
- `ExecutionTrace` - Complete trace object

**Trace Information**:
- Query and question type
- Retrieval traces (queries, scores, times)
- Reasoning traces (stages, confidence, tokens)
- Final answer and confidence
- Latency and cost
- Sources used

**Output**: JSON and plain-text logs + structured traces

## Data Models

### Document
```python
Document
├── document_id: str
├── filename: str
├── document_type: DocumentType
├── content: str
├── metadata: Metadata
├── chunks: List[Chunk]
├── tables: List[Dict]
├── extracted_entities: List[str]
└── lineage: Dict
```

### Chunk
```python
Chunk
├── chunk_id: str
├── content: str
├── chunk_type: ChunkType (TEXT | TABLE | IMAGE)
├── metadata: Metadata
├── embedding: List[float] (optional)
├── table_metadata: TableMetadata (optional)
├── position: int
├── retrieval_score: float
├── confidence: float
└── related_chunks: List[str]
```

### Answer
```python
Answer
├── answer_id: str
├── query: str
├── answer_text: str
├── confidence_score: float
├── evidence: List[Evidence]
├── reasoning_steps: List[str]
├── citations: Dict[str, str]
├── is_grounded: bool
└── metadata: Dict
```

## Configuration Flow

```
Environment Variables (.env)
    ↓
Settings (Pydantic) - src/config/settings.py
    ├── LLMConfig
    ├── RetrievalConfig
    ├── ParsingConfig
    ├── SQLConfig
    ├── ReasoningConfig
    ├── EvaluationConfig
    └── LoggingConfig
    ↓
Global settings instance
    ↓
Used by all modules
```

## Request Flow

```
Question Input
    ↓
[Stage 1] Query Understanding
    └→ Extract type, entities, keywords
    ↓
[Stage 2] Retrieval Planning
    └→ BM25 + Dense search + Reranking
    ↓
Retrieved Chunks
    ↓
[Stage 3] Evidence Validation
    └→ Filter, rank, compute confidence
    ↓
Validated Evidence
    ↓
[Stage 4] Computation (Optional)
    ├→ SQL queries (if needed)
    └→ Mathematical operations
    ↓
[Stage 5] Reasoning & Synthesis
    └→ Generate answer from evidence
    ↓
[Stage 6] Verification
    └→ Check consistency and grounding
    ↓
Final Answer + Evidence + Confidence
```

## Optimization Strategies

### Cost Optimization

1. **Minimal Token Usage**
   - Retrieve first, filter early
   - Use small models when possible
   - Implement query caching

2. **Efficient Retrieval**
   - BM25 first (fast, no LLM)
   - Dense search only when needed
   - Metadata filtering to narrow scope

3. **Table Handling**
   - SQL for deterministic computation
   - Avoid LLM arithmetic
   - Use pandas for fast operations

### Latency Optimization

1. **Parallel Processing**
   - Concurrent retrieval strategies
   - Batch embeddings
   - Async LLM calls

2. **Caching**
   - Cache embeddings
   - Cache retrieval results
   - Memoize computations

3. **Early Termination**
   - Stop if high confidence reached
   - Skip reranking if not needed
   - Use fast models for easy queries

### Quality Optimization

1. **Retrieval Quality**
   - Hierarchical chunking
   - Multi-strategy combination
   - Reranking with cross-encoders

2. **Reasoning Quality**
   - Multi-stage verification
   - Evidence validation
   - Hallucination detection

3. **Table Quality**
   - SQL-based computation
   - Type inference
   - Query optimization

## Extensibility Points

### Custom Retrievers

```python
class CustomRetriever(HybridRetriever):
    def retrieve(self, query, top_k=5):
        # Custom logic
        pass
```

### Custom Reasoning Stages

```python
class CustomStage:
    def execute(self, ...):
        # Custom stage logic
        pass
```

### New Document Types

```python
class CustomDocumentParser(DocumentParser):
    def parse(self, file_path):
        # Custom parsing logic
        pass
```

## Performance Characteristics

### Retrieval
- BM25: O(n log n) with precomputed inverted index
- Dense: O(n) with FAISS (can be O(log n) with IVF)
- Reranking: O(k log k) where k = top-k candidates

### Reasoning
- Query understanding: O(|query|) - linear in query length
- Evidence validation: O(|chunks|) - linear in chunk count
- Computation: O(|table|) - depends on table size
- Verification: O(1) - constant checks

### Overall Latency (typical)
- Retrieval: 10-50ms (with caching: <5ms)
- Computation: 0-100ms (depends on table size)
- Reasoning: 100-500ms (depends on LLM calls)
- **Total**: 100-1000ms

## Error Handling

### Graceful Degradation
- Missing embeddings → fallback to BM25
- SQL errors → fallback to pandas
- Parsing errors → skip document
- LLM errors → retry or fallback

### Hallucination Prevention
- Require evidence for all claims
- Confidence thresholds
- Grounding verification
- Source attribution

## Monitoring & Observability

### Logging
- All operations logged with timing
- Structured JSON logs for parsing
- Full execution traces

### Metrics
- Per-query latency and cost
- Retrieval recall and precision
- Answer confidence distribution
- Error rates by type

### Debugging
- Full execution traces stored
- Retrieval scores visible
- Reasoning steps traceable
- Computation results logged

---

For usage examples, see [USAGE.md](./USAGE.md)  
For configuration details, see [CONFIG.md](./CONFIG.md)
