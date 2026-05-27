# Sentient Arena — Office QA Agent

Enterprise-grade grounded reasoning agent for the **Databricks OfficeQA / Sentient Arena** benchmark.

## Architecture

```
                         ┌─────────────────────────────┐
                         │      PARSE ONCE corpus       │
                         │  PDFPlumber + PyMuPDF + OCR  │
                         └────────────┬────────────────┘
                                      │
                         ┌────────────▼────────────────┐
                         │     Persistent Index         │
                         │  BM25 • FAISS • DuckDB       │
                         └────────────┬────────────────┘
                                      │
          ┌───────────────────────────▼───────────────────────────┐
          │                  6-Stage Agent Pipeline                │
          │  A: Query Classify  →  B: Hybrid Retrieve             │
          │  C: Rerank + Validate  →  D: SQL Compute (DuckDB)     │
          │  E: LLM Synthesize  →  F: Self-Verify                 │
          └───────────────────────────────────────────────────────┘
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Add: ANTHROPIC_API_KEY=sk-ant-...

# 3. Place documents in data/corpus/
mkdir -p data/corpus
cp your_docs/*.pdf data/corpus/

# 4. Ingest (parse + index — run once)
python cli.py ingest --corpus data/corpus

# 5. Query
python cli.py query "What was the net income in FY2023?"

# 6. Run benchmark eval
python cli.py eval --benchmark data/eval/benchmark.jsonl --errors

# 7. Start API server
python cli.py serve
```

## Project Structure

```
sentient_arena/
├── ingestion/
│   └── parser.py          # PDF parsing, table extraction, chunking
├── retrieval/
│   └── hybrid_retriever.py # BM25 + FAISS + cross-encoder reranking
├── sql_engine/
│   └── table_db.py        # Tables → DuckDB, text-to-SQL
├── agents/
│   └── pipeline.py        # 6-stage reasoning pipeline
├── evaluation/
│   └── harness.py         # Accuracy, latency, cost metrics
├── logging_utils/
│   └── tracer.py          # Structured logging + reasoning traces
├── config/
│   ├── settings.py        # All tunables
│   └── models.py          # Shared data models
├── main.py                # FastAPI server
├── cli.py                 # CLI interface
└── requirements.txt
```

## Key Design Decisions

### Parse Once, Query Many
The entire corpus is parsed and indexed upfront. Inference is fast retrieval
over a pre-built FAISS index — no repeated document parsing.

### Table-as-Database
All extracted tables are registered in DuckDB. Numerical questions go through
text-to-SQL execution rather than LLM arithmetic, eliminating hallucinated math.

### Adaptive Model Routing
- **Easy lookups** → `claude-haiku` (fast, cheap)
- **Multi-hop / numerical / low-confidence** → `claude-sonnet` (deep)

Cost is minimized by routing to the stronger model only when needed.

### Grounding Guarantee
Answers include evidence chunk IDs. Stage F verifies every answer against
retrieved evidence. The system prefers "Insufficient evidence" over hallucination.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | System status |
| POST | `/query` | Ask a question |
| POST | `/ingest` | Ingest a new corpus |
| POST | `/eval` | Run benchmark |
| GET | `/schema` | Show registered tables |

## Benchmark Format

`data/eval/benchmark.jsonl` — one question per line:
```json
{"id": "q001", "question": "What is the total debt in 2022?", "answer": "$1.2 trillion"}
```

## Configuration

Key tunables in `config/settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `embedding.model_name` | `BAAI/bge-small-en-v1.5` | Local embedding model |
| `retrieval.rerank_top_n` | `5` | Evidence pieces fed to LLM |
| `cost.max_context_tokens` | `8000` | Max context per LLM call |
| `cost.escalation_threshold` | `0.6` | Confidence cutoff for strong model |
| `llm.strong_model` | `claude-sonnet-4-20250514` | Deep reasoning |
| `llm.fast_model` | `claude-haiku-4-5-20251001` | Triage + classification |

## Optimization Tips

1. **First, run error analysis**: `python cli.py eval --errors` to find failure modes
2. **Tune chunk size**: Larger chunks help multi-hop, smaller help lookup precision
3. **Add domain-specific reranking**: Fine-tune the cross-encoder on financial text
4. **Cache embeddings**: Already supported via `diskcache`
5. **Parallel ingestion**: Use Python multiprocessing for large corpora
