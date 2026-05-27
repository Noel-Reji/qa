# Office-QA Challenge: Production-Grade Document Reasoning Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Version: 0.1.0](https://img.shields.io/badge/version-0.1.0-blue)
![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-brightgreen)

## Overview

A production-grade AI agent system for the **Sentient Arena Office-QA Challenge** that combines sophisticated document processing, hybrid retrieval, and multi-stage reasoning to answer complex financial and business questions from enterprise documents with **high accuracy, low latency, and minimal cost**.

### Key Features

✅ **Multi-Format Document Parsing** - PDFs, CSVs, text, tables  
✅ **Hybrid Retrieval** - BM25 + Dense embeddings + Reranking  
✅ **Table-as-Database** - SQL-based numerical reasoning  
✅ **6-Stage Reasoning Pipeline** - Structured, traceable reasoning  
✅ **Cost Optimization** - Minimal token usage, selective model routing  
✅ **Enterprise-Grade Evaluation** - Comprehensive metrics & benchmarking  
✅ **Structured Logging** - Full execution traces for debugging  
✅ **Production Ready** - Modular, scalable, well-tested architecture  

## Quick Start

```bash
# Install
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your API keys

# Ingest documents
python -m src.cli ingest data/corpus

# Ask a question
python -m src.cli ask "What is the total revenue?"

# Batch process
python -m src.cli batch questions.txt --output results.json
```

## Architecture

### Multi-Stage Reasoning Pipeline

1. **Query Understanding** - Classify question type, extract entities
2. **Retrieval Planning** - BM25 + Dense search + Reranking
3. **Evidence Validation** - Filter and rank evidence by confidence
4. **Computation** - SQL queries and numerical operations
5. **Reasoning** - Synthesize answer from evidence
6. **Verification** - Check consistency and prevent hallucinations

### Core Components

- **Document Parser** - PDFs, CSVs, DOCX, TXT with hierarchical chunking
- **Hybrid Retriever** - BM25 + Dense embeddings + Cross-encoder reranking
- **Table Engine** - SQL (DuckDB) + Pandas for table reasoning
- **Reasoning Agent** - Multi-stage pipeline with confidence scoring
- **Evaluation System** - Accuracy, latency, cost metrics
- **Logging System** - Full execution traces for debugging

## Documentation

- [Full README](./ARCHITECTURE.md) - System architecture and design
- [Usage Guide](./USAGE.md) - Detailed usage examples
- [Configuration](./CONFIG.md) - All available settings
- [Development](./DEVELOPMENT.md) - Contributing guide

## Project Structure

```
src/
├── config/           # Configuration management
├── parsing/          # Document parsing
├── retrieval/        # Hybrid retrieval
├── sql_engine/       # Table reasoning
├── reasoning/        # Multi-stage agent
├── evaluation/       # Benchmarking
├── logging/          # Tracing & logging
├── utils/            # Data models
├── ingestion/        # Orchestration
└── cli.py            # CLI interface

data/
├── corpus/           # Input documents
├── indices/          # Retrieval indices
├── results/          # Evaluation results
└── traces/           # Reasoning traces
```

## Key Features

### Production-Grade
- Structured error handling and logging
- Comprehensive evaluation framework
- Cost and latency tracking
- Full reasoning trace logging

### Enterprise-Ready
- Multi-format document support
- Hierarchical chunking strategy
- Table handling with SQL
- Metadata-aware retrieval

### Cost-Optimized
- Minimal token usage
- Selective model routing
- Efficient caching
- Fast retrieval-first approach

### High Quality
- Multi-stage reasoning prevents hallucinations
- Evidence validation ensures grounding
- Confidence scoring on all outputs
- Structured verification

## Performance

- **Accuracy**: Grounded retrieval + multi-stage reasoning
- **Latency**: Parallel processing + caching
- **Cost**: Selective LLM use, efficient retrieval
- **Quality**: Table reasoning, confidence scoring

## Usage Examples

### Python API

```python
from src.ingestion import initialize_system

system = initialize_system()
system.ingest_directory("data/corpus")

result = system.answer_question("What is the total?")
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']:.1%}")
```

### CLI

```bash
python -m src.cli ingest data/corpus
python -m src.cli ask "What are the main findings?"
python -m src.cli batch questions.txt
```

## Configuration

All settings can be configured via `.env` file:

```env
LLM_PROVIDER=openai
LLM_REASONING_MODEL=gpt-4-turbo-preview
RETRIEVAL_TOP_K=5
REASONING_CONFIDENCE_THRESHOLD=0.6
```

See `.env.example` for all available options.

## Evaluation

```python
from src.evaluation import BenchmarkEvaluator

evaluator = BenchmarkEvaluator()
results = evaluator.evaluate_batch(answers, benchmark_data)
evaluator.print_results(results)
```

## Testing

```bash
pytest tests/ -v
black src/ --line-length=100
ruff check src/
mypy src/
```

## License

MIT License - See LICENSE file

## Citation

If you use this system, please cite:

```bibtex
@software{office_qa_2026,
  title={Office-QA: Production-Grade Document Reasoning Agent},
  author={Your Name},
  year={2026},
  url={https://github.com/Noel-Reji/qa}
}
```

---

For full documentation, see [ARCHITECTURE.md](./ARCHITECTURE.md)