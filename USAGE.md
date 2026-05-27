# Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
3. [CLI Interface](#cli-interface)
4. [Python API](#python-api)
5. [Advanced Examples](#advanced-examples)
6. [Evaluation](#evaluation)
7. [Troubleshooting](#troubleshooting)

## Installation

### From Source

```bash
git clone https://github.com/Noel-Reji/qa.git
cd qa

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"

# For UI (optional)
pip install -e ".[ui]"
```

### Configuration

```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
nano .env  # or your favorite editor
```

Required settings:
- `LLM_API_KEY` - Your LLM provider API key
- `LLM_PROVIDER` - openai, anthropic, gemini, or openrouter

## Basic Usage

### 1. Ingest Documents

```python
from src.ingestion import initialize_system
from pathlib import Path

# Initialize system
system = initialize_system()

# Ingest from directory
doc_count = system.ingest_directory("data/corpus")
print(f"Ingested {doc_count} documents")

# Or ingest specific files
system.ingest_documents([
    Path("document1.pdf"),
    Path("document2.csv"),
    Path("document3.txt"),
])

# Check corpus size
stats = system.get_corpus_stats()
print(f"Corpus has {stats['num_chunks']} chunks")
```

### 2. Ask Questions

```python
# Single question
result = system.answer_question("What is the total revenue for 2024?")

print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']:.1%}")
print(f"Grounded: {result['is_grounded']}")
print(f"Sources: {result['sources']}")

# Access detailed information
if result['evidence']:
    print(f"\nEvidence ({len(result['evidence'])} chunks):")
    for i, ev in enumerate(result['evidence'][:3]):
        print(f"  {i+1}. {ev['source_document']} (relevance: {ev['relevance_score']:.2f})")

# Access reasoning steps
if result['metadata']:
    for step in result['metadata'].get('reasoning_steps', []):
        print(f"  - {step}")
```

### 3. Batch Processing

```python
# Multiple questions
questions = [
    "What is the total revenue?",
    "Who is the CEO?",
    "What are the main challenges?",
]

results = system.batch_answer_questions(questions)

for q, r in zip(questions, results):
    print(f"Q: {q}")
    print(f"A: {r['answer']}\n")
```

## CLI Interface

### Ingest Documents

```bash
# Ingest entire directory
python -m src.cli ingest data/corpus

# Output:
# ✓ Ingested 5 documents
#   - Total documents: 5
#   - Total chunks: 243
#   - Total tables: 8
#   - Total characters: 145,230
```

### Ask Questions

```bash
# Single question (formatted output)
python -m src.cli ask "What is the total?"

# Output:
# Question: What is the total?
# 
# Answer: The total amount is $5,000,000...
# 
# Confidence: 85%
# Grounded: True
# Sources: financial_report.pdf

# Single question (JSON output)
python -m src.cli ask "What is the total?" --json

# Output:
# {
#   "answer": "The total amount is $5,000,000",
#   "confidence": 0.85,
#   ...
# }
```

### Batch Processing

```bash
# Prepare questions file (one per line)
cat > questions.txt << EOF
What is the total revenue?
What is the profit margin?
Who is the CFO?
EOF

# Process batch
python -m src.cli batch questions.txt --output results.json

# Output:
# Processing [===================================] 100%
# 
# Summary:
#   - Total questions: 3
#   - Avg confidence: 82%
#   - Grounded answers: 3/3
```

### Corpus Statistics

```bash
python -m src.cli stats

# Output:
# Corpus Statistics:
#   - Documents: 5
#   - Chunks: 243
#   - Tables: 8
#   - Total size: 145,230 characters
```

## Python API

### Core System

```python
from src.ingestion import initialize_system

# Get system instance
system = initialize_system()

# Ingest documents
system.ingest_directory("data/corpus")

# Ask question
answer = system.answer_question("Your question here?")

# Clear corpus
system.clear_corpus()
```

### Document Parsing

```python
from src.parsing import DocumentParsingEngine
from pathlib import Path

parser = DocumentParsingEngine()

# Parse single document
doc = parser.parse_document(Path("report.pdf"))
print(f"Parsed {len(doc.chunks)} chunks from {doc.filename}")

# Parse directory
docs = parser.parse_directory(Path("data/corpus"))
print(f"Parsed {len(docs)} documents")

# Access parsed content
for chunk in doc.chunks:
    print(f"Chunk {chunk.position}: {chunk.content[:100]}...")
```

### Retrieval

```python
from src.retrieval import HybridRetriever
from src.parsing import DocumentParsingEngine

# Parse documents
parser = DocumentParsingEngine()
doc = parser.parse_document("document.pdf")

# Create retriever
retriever = HybridRetriever()
retriever.index_chunks(doc.chunks)

# Retrieve chunks
chunks = retriever.retrieve("What is the total?", top_k=5)

for chunk in chunks:
    print(f"Score: {chunk.retrieval_score:.2f}")
    print(f"Content: {chunk.content[:100]}...")
    print()

# Retrieve with metadata filtering
chunks = retriever.retrieve_with_metadata_filter(
    query="financial results",
    metadata_filter={"section": "Financial Statements"},
    top_k=5
)
```

### Table Reasoning

```python
from src.sql_engine import TableReasoningEngine
import pandas as pd

engine = TableReasoningEngine()

# Create sample data
df = pd.DataFrame({
    "Product": ["A", "B", "C"],
    "Revenue": [1000, 2000, 1500],
    "Cost": [500, 800, 600],
})

# Reason over table
result = engine.reason_over_table(
    question="What is the total revenue?",
    table_data=df,
    table_name="sales"
)

print(f"Answer: {result['answer']}")
print(f"Computation: {result['computation']}")
```

### Evaluation

```python
from src.evaluation import BenchmarkEvaluator
from src.ingestion import initialize_system

system = initialize_system()
system.ingest_directory("data/corpus")

# Prepare benchmark data
benchmark = [
    {
        "question": "What is the total?",
        "expected_answer": "5000000",
        "expected_sources": ["report.pdf"],
    },
    {
        "question": "Who is the CEO?",
        "expected_answer": "John Smith",
        "expected_sources": ["report.pdf"],
    },
]

# Answer questions
answers = [
    system.answer_question(q["question"])
    for q in benchmark
]

# Evaluate
evaluator = BenchmarkEvaluator()
results = evaluator.evaluate_batch(
    [Answer(**a) for a in answers],
    benchmark
)

# Print results
evaluator.print_results(results)

# Save results
evaluator.save_results(results, "benchmark_v1")
```

### Logging and Tracing

```python
from src.logging import get_logger, ReasoningTrace, ReasoningTraceLevel

logger = get_logger("my_app")

# Start trace
logger.start_trace("q1", "What is the total?", "numerical")

# Do some processing...
logger.info("Processing query")

# Add reasoning trace
trace = ReasoningTrace(
    step=1,
    level=ReasoningTraceLevel.RETRIEVAL,
    description="Retrieved 5 chunks",
    confidence=0.85,
    latency_ms=45.2,
    tokens_used=150,
)
logger.add_reasoning_trace(trace)

# Finalize
trace_obj = logger.finalize_trace(
    final_answer="The answer is 5000",
    confidence_score=0.85,
    total_latency_ms=234.5,
    total_tokens=450,
    estimated_cost=0.01,
    sources_used=["file1.pdf", "file2.pdf"],
)

print(f"Trace saved to: {trace_obj}")
```

## Advanced Examples

### Custom Retrieval with Filters

```python
from src.retrieval import HybridRetriever

retriever = HybridRetriever()
retriever.index_chunks(corpus_chunks)

# Retrieve with filters
chunks = retriever.retrieve_with_metadata_filter(
    query="Q3 financial results",
    metadata_filter={
        "document_id": "annual_report_2024",
        "section": "Financial Results",
    },
    top_k=10
)
```

### Multi-Stage Reasoning

```python
from src.reasoning import MultiStageReasoningAgent
from src.retrieval import HybridRetriever

retriever = HybridRetriever()
retriever.index_chunks(corpus_chunks)

agent = MultiStageReasoningAgent(retriever)

# Get full answer with tracing
answer = agent.answer_question("What were the key achievements in 2024?")

print(f"Answer: {answer.answer_text}")
print(f"Confidence: {answer.confidence_score:.1%}")
print(f"Reasoning:")
for step in answer.reasoning_steps:
    print(f"  - {step}")
```

### Table-based Computation

```python
from src.sql_engine import TableReasoningEngine, ComputationEngine
import pandas as pd

# Sample financial data
df = pd.DataFrame({
    "Year": [2022, 2023, 2024],
    "Revenue": [1000000, 1500000, 2000000],
    "Expenses": [600000, 800000, 1000000],
})

engine = TableReasoningEngine()

# Question answering with table reasoning
result = engine.reason_over_table(
    "What is the average revenue across all years?",
    df,
    "financial_data"
)

print(f"Result: {result}")

# Alternative: Direct computation
comp_engine = ComputationEngine()
comp_result = comp_engine.extract_and_compute(
    "The revenues were 1000000, 1500000, and 2000000"
)
print(f"Extracted: {comp_result}")
```

### Custom Configuration

```python
from src.config import settings

# Override settings programmatically
settings.retrieval.top_k = 10
settings.retrieval.use_reranker = True
settings.reasoning.confidence_threshold = 0.7
settings.llm.temperature = 0.1

# Verify changes
print(f"Top-K: {settings.retrieval.top_k}")
print(f"Confidence Threshold: {settings.reasoning.confidence_threshold}")
```

## Evaluation

### Benchmark Evaluation

```python
from src.evaluation import BenchmarkEvaluator
from src.ingestion import initialize_system

system = initialize_system()

# Create benchmark data
benchmark = [
    {
        "question": q,
        "expected_answer": expected_a,
        "expected_sources": sources,
    }
    for q, expected_a, sources in [
        ("Q1?", "Answer1", ["doc1.pdf"]),
        ("Q2?", "Answer2", ["doc2.pdf"]),
        # ... more benchmarks
    ]
]

# Run evaluation
evaluator = BenchmarkEvaluator()
answers = [system.answer_question(b["question"]) for b in benchmark]
results = evaluator.evaluate_batch(answers, benchmark)

# Analyze results
metrics = evaluator.compute_aggregate_metrics(results)
print(f"Accuracy: {metrics['accuracy']:.1%}")
print(f"Avg Latency: {metrics['avg_latency_ms']:.1f}ms")
print(f"Total Cost: ${metrics['total_estimated_cost']:.4f}")
```

### Error Analysis

```python
# Find failed queries
failed = [r for r in results if r.error is not None]
print(f"Failed queries: {len(failed)}")

for result in failed:
    print(f"  Q: {result.question}")
    print(f"  Error: {result.error}\n")

# Find low confidence answers
low_conf = [r for r in results if r.grounding_score < 0.5]
print(f"Low confidence: {len(low_conf)}")

# Find hallucinations (high confidence but wrong)
hallucinations = [
    r for r in results 
    if not r.exact_match and result.grounding_score > 0.8
]
```

## Troubleshooting

### Low Accuracy

```python
# Increase retrieval quality
settings.retrieval.top_k = 10  # Get more candidates
settings.retrieval.use_reranker = True  # Enable reranking
settings.retrieval.chunk_size = 256  # Smaller chunks for better specificity

# Or adjust reasoning
settings.reasoning.require_evidence = True  # Don't answer without evidence
settings.reasoning.confidence_threshold = 0.7  # Higher threshold
```

### High Latency

```python
# Optimize retrieval
settings.retrieval.use_reranker = False  # Disable reranking
settings.retrieval.top_k = 3  # Get fewer candidates

# Use faster models
settings.llm.reasoning_model = "gpt-3.5-turbo"  # Faster LLM
settings.retrieval.embedding_model = "all-MiniLM-L6-v2"  # Faster embeddings
```

### Out of Memory

```python
# Reduce batch sizes
settings.batch_size = 16  # Default: 32

# Reduce chunk size
settings.retrieval.chunk_size = 256  # Default: 512

# Disable embeddings caching
settings.enable_cache = False
```

### Parsing Failures

```python
# Check file format
from pathlib import Path
file = Path("document.pdf")
print(f"Extension: {file.suffix}")  # Should be recognized

# Try specific parser
from src.parsing import PDFDocumentParser
parser = PDFDocumentParser()
doc = parser.parse(file)

# Check error logs
from src.logging import get_logger
logger = get_logger("parsing")
# Logs in: logs/parsing.log
```

---

For API reference, see [ARCHITECTURE.md](./ARCHITECTURE.md)  
For configuration options, see [CONFIG.md](./CONFIG.md)
