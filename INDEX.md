# Office-QA System - Complete Index & Navigation

> **Status**: ✅ Production-Ready Implementation  
> **Challenge**: Sentient Arena Office-QA  
> **Version**: 0.1.0

---

## 📚 Documentation Index

### Getting Started
- **[README.md](./README.md)** - Start here! Project overview and quick start
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - What was built and why

### Core Documentation  
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System design, components, data flow
- **[USAGE.md](./USAGE.md)** - Detailed usage examples (CLI and Python API)
- **[CONFIG.md](./CONFIG.md)** - Configuration reference (all 60+ options)

### Development
- **[DEVELOPMENT.md](./DEVELOPMENT.md)** - Development setup, testing, contributing

---

## 🗂️ Project Structure

### Source Code (`src/`)

| Module | File | Purpose |
|--------|------|---------|
| **config** | `settings.py` | Configuration management (Pydantic) |
| **parsing** | `document_parser.py` | Document ingestion & chunking |
| **retrieval** | `hybrid_retriever.py` | BM25 + Dense + Reranking |
| **sql_engine** | `table_engine.py` | SQL & table-based reasoning |
| **reasoning** | `multi_stage_agent.py` | 6-stage reasoning pipeline |
| **evaluation** | `evaluator.py` | Benchmarking & metrics |
| **logging** | `trace_logger.py` | Structured logging & traces |
| **utils** | `data_models.py` | Data models |
| **utils** | `helpers.py` | Utility functions |
| **ingestion** | `orchestrator.py` | System orchestration |
| **CLI** | `cli.py` | Command-line interface |
| **Entry** | `__main__.py` | Main entry point |

### Tests (`tests/`)
- `test_core.py` - Unit tests for core components

### Data (`data/`)
- `corpus/` - Input documents (includes sample)
- `indices/` - Retrieval indices
- `results/` - Evaluation results
- `traces/` - Execution traces
- `cache/` - Cached results

### Configuration
- `.env.example` - Configuration template
- `pyproject.toml` - Project metadata & dependencies
- `Dockerfile` - Docker build file
- `docker-compose.yml` - Docker compose configuration
- `setup.sh` - Automated setup script

---

## 🚀 Quick Start

### 1. Setup
```bash
bash setup.sh
# or manually:
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env with your LLM API key
```

### 3. Use
```bash
# CLI
python -m src.cli ingest data/corpus
python -m src.cli ask "Your question?"

# Python API
from src.ingestion import initialize_system
system = initialize_system()
system.ingest_directory("data/corpus")
result = system.answer_question("Your question?")
```

---

## 🏗️ System Architecture

### Multi-Stage Reasoning Pipeline

```
Query Input
    ↓
[1] Query Understanding → Extract type, entities, keywords
    ↓
[2] Retrieval Planning → BM25 + Dense + Reranking
    ↓
[3] Evidence Validation → Filter, rank, compute confidence
    ↓
[4] Computation → SQL/Math (if needed)
    ↓
[5] Reasoning → Synthesize answer from evidence
    ↓
[6] Verification → Check grounding, detect hallucinations
    ↓
Grounded Answer + Evidence + Confidence
```

### Key Features

✅ **Hybrid Retrieval**
- BM25 for keyword search (fast, no LLM)
- Dense embeddings for semantic understanding
- Cross-encoder reranking for precision
- Metadata filtering

✅ **Table Reasoning**
- SQL execution (DuckDB/SQLite)
- Table extraction from documents
- NL-to-SQL conversion
- Numerical computations

✅ **Cost Optimization**
- Minimal token usage (retrieve first)
- Selective model routing
- Query caching
- Efficient parsing

✅ **Quality Assurance**
- Multi-stage verification
- Evidence validation
- Hallucination detection
- Grounding checks

✅ **Enterprise Ready**
- Structured logging
- Execution traces
- Comprehensive evaluation
- Error handling

---

## 📖 How to Read the Documentation

### For First-Time Users
1. Read [README.md](./README.md) - Overview
2. Run `bash setup.sh` - Get system running
3. Read [USAGE.md](./USAGE.md) - Learn by examples
4. Try the CLI and Python API

### For Understanding Architecture
1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
2. Review [src/](./src/) directory structure
3. Read key module docstrings

### For Configuration
1. Check [CONFIG.md](./CONFIG.md) - All options
2. Edit `.env` file based on needs
3. Review [src/config/settings.py](./src/config/settings.py)

### For Development
1. Read [DEVELOPMENT.md](./DEVELOPMENT.md)
2. Set up dev environment
3. Run tests: `pytest tests/`
4. Follow code style: `black`, `ruff`, `mypy`

### For Evaluation
1. Review [USAGE.md](./USAGE.md) - Evaluation section
2. Check [src/evaluation/](./src/evaluation/) module
3. Review [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Metrics

---

## 🔑 Key Components Explained

### 1. Document Parsing
- Converts PDFs, CSVs, text into chunks
- Preserves metadata (page, section, revision)
- Extracts and stores tables
- Creates hierarchical structure

**Entry Point**: `src/parsing/document_parser.py`

### 2. Retrieval System
- **BM25**: Fast keyword search
- **Dense**: Semantic understanding via embeddings
- **Reranker**: Cross-encoder refinement
- **Hybrid**: Combines all strategies

**Entry Point**: `src/retrieval/hybrid_retriever.py`

### 3. SQL Engine
- Executes deterministic queries on tables
- Converts to SQL for precision
- Fallback to pandas
- Safe expression evaluation

**Entry Point**: `src/sql_engine/table_engine.py`

### 4. Reasoning Agent
- 6-stage pipeline
- Each stage has clear input/output
- Produces grounded answers
- Tracks confidence scores

**Entry Point**: `src/reasoning/multi_stage_agent.py`

### 5. Orchestration
- Single system interface
- Manages corpus and processing
- Coordinates all components

**Entry Point**: `src/ingestion/orchestrator.py`

---

## 💻 API Quick Reference

### Python API

```python
from src.ingestion import initialize_system

# Initialize
system = initialize_system()

# Ingest documents
system.ingest_directory("data/corpus")

# Ask question
result = system.answer_question("What is total?")
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']:.1%}")
print(f"Sources: {result['sources']}")
```

### CLI Commands

```bash
# Ingest documents
python -m src.cli ingest data/corpus

# Ask single question
python -m src.cli ask "What is the total?"

# Batch process
python -m src.cli batch questions.txt --output results.json

# Show statistics
python -m src.cli stats

# Show version
python -m src.cli version
```

### Core Classes

| Class | Module | Purpose |
|-------|--------|---------|
| `OfficeQASystem` | `ingestion` | Main system |
| `DocumentParsingEngine` | `parsing` | Parse documents |
| `HybridRetriever` | `retrieval` | Retrieve evidence |
| `TableReasoningEngine` | `sql_engine` | Reason over tables |
| `MultiStageReasoningAgent` | `reasoning` | Generate answers |
| `BenchmarkEvaluator` | `evaluation` | Evaluate results |
| `SystemLogger` | `logging` | Structured logging |

---

## 🎯 Use Cases

### Basic Question Answering
```python
system.answer_question("What is the revenue?")
```

### Financial Analysis
```python
system.answer_question("What is the profit margin over time?")
# Will use table reasoning for calculations
```

### Document Summarization
```python
system.answer_question("What are the key findings?")
```

### Multi-Document QA
```python
system.ingest_directory("reports/")  # Multiple documents
system.answer_question("Compare revenue across reports")
```

### Batch Evaluation
```python
evaluator = BenchmarkEvaluator()
results = evaluator.evaluate_batch(answers, benchmark_data)
evaluator.print_results(results)
```

---

## 📊 Metrics & Monitoring

### Tracked Metrics
- **Accuracy** - Exact match %
- **Latency** - End-to-end time
- **Cost** - Token usage & estimated cost
- **Retrieval** - Recall, precision
- **Grounding** - Evidence confidence
- **Errors** - Failure tracking

### Logs & Traces
- Execution traces in `data/traces/`
- Logs in `logs/` directory
- Evaluation results in `data/results/`
- JSON and plain-text formats

---

## 🔧 Configuration Examples

### Development (Fast, Debug)
```env
ENVIRONMENT=development
LOGGING_LOG_LEVEL=DEBUG
RETRIEVAL_USE_RERANKER=false
DEBUG=true
```

### Production (Accurate, Cost-Optimized)
```env
ENVIRONMENT=production
LLM_TEMPERATURE=0.0
REASONING_CONFIDENCE_THRESHOLD=0.8
RETRIEVAL_USE_RERANKER=true
DEBUG=false
```

### High-Speed (Fastest Response)
```env
RETRIEVAL_TOP_K=3
RETRIEVAL_USE_RERANKER=false
LLM_FAST_MODEL=gpt-3.5-turbo
LLM_MAX_TOKENS=1024
```

See [CONFIG.md](./CONFIG.md) for complete reference

---

## 📋 Development Workflow

### Setup Dev Environment
```bash
pip install -e ".[dev]"
```

### Run Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
black src/
ruff check src/
mypy src/
```

### Add New Feature
1. Create module in appropriate `src/` directory
2. Implement functionality
3. Add tests
4. Update documentation
5. Follow code style

See [DEVELOPMENT.md](./DEVELOPMENT.md) for details

---

## 🚨 Troubleshooting

### Problem: Low retrieval quality
**Solution**: Increase `RETRIEVAL_TOP_K`, enable reranker, try different embedding model
See [USAGE.md - Troubleshooting](./USAGE.md#troubleshooting)

### Problem: High latency
**Solution**: Reduce `RETRIEVAL_TOP_K`, disable reranker, use faster LLM
See [CONFIG.md](./CONFIG.md) - High-Speed example

### Problem: Out of memory
**Solution**: Reduce batch size, chunk size, disable caching
See [DEVELOPMENT.md - Debugging](./DEVELOPMENT.md#debugging)

### Problem: Parsing errors
**Solution**: Check file format, verify file size, enable logging
See [USAGE.md - Troubleshooting](./USAGE.md#troubleshooting)

---

## 📦 Deployment Options

### Local
```bash
python -m src.cli ask "Your question?"
```

### Docker
```bash
docker build -t office-qa .
docker run -it office-qa ask "Your question?"
```

### Production
See [DEVELOPMENT.md - Release Process](./DEVELOPMENT.md#release-process)

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Implement changes with tests
4. Run code quality checks
5. Submit pull request

See [DEVELOPMENT.md - Contributing](./DEVELOPMENT.md#contributing-guidelines)

---

## 📞 Support Resources

| Need | Resource |
|------|----------|
| Quick start | [README.md](./README.md) |
| Usage examples | [USAGE.md](./USAGE.md) |
| Architecture details | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| Configuration | [CONFIG.md](./CONFIG.md) |
| Development | [DEVELOPMENT.md](./DEVELOPMENT.md) |
| What was built | [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) |

---

## 📈 Next Steps

1. ✅ **System Setup** - `bash setup.sh`
2. ✅ **Documentation Review** - Read README.md
3. ✅ **Configuration** - Edit .env
4. ✅ **Try Examples** - Review USAGE.md
5. ✅ **Ingest Corpus** - `python -m src.cli ingest data/corpus`
6. ✅ **Ask Questions** - `python -m src.cli ask "Your question?"`
7. ✅ **Evaluate** - Run benchmark evaluation
8. ✅ **Optimize** - Adjust configuration based on results
9. ✅ **Deploy** - Choose deployment option

---

## ✨ Key Achievements

✅ Production-grade system implemented  
✅ 6-stage reasoning pipeline with verification  
✅ Hybrid retrieval (BM25 + Dense + Reranking)  
✅ Table reasoning with SQL  
✅ Comprehensive logging and tracing  
✅ Modular, extensible architecture  
✅ Complete documentation  
✅ CLI and Python API  
✅ Evaluation framework  
✅ Docker support  

---

**Ready for Sentient Arena Office-QA Challenge! 🚀**

For any questions, refer to the relevant documentation file above.
