"""
FastAPI Server — Production API for the Sentient Arena Agent
Exposes: /ingest, /query, /eval, /health
"""
from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from config.models import AgentAnswer
from config.settings import settings
from ingestion.parser import CorpusIngester
from retrieval.hybrid_retriever import DocumentIndex, HybridRetriever
from sql_engine.table_db import TableSQLEngine
from agents.pipeline import ReasoningPipeline
from evaluation.harness import EvaluationHarness
from logging_utils.tracer import get_logger

log = get_logger(__name__)
app = FastAPI(title="Sentient Arena — Office QA Agent", version="1.0.0")


# ─────────────────────────────────────────────
# Global State (initialized at startup)
# ─────────────────────────────────────────────

_index: Optional[DocumentIndex] = None
_retriever: Optional[HybridRetriever] = None
_sql_engine: Optional[TableSQLEngine] = None
_pipeline: Optional[ReasoningPipeline] = None


@app.on_event("startup")
async def startup():
    global _index, _retriever, _sql_engine, _pipeline

    _index = DocumentIndex()
    index_dir = settings.index_dir

    if (index_dir / "dense.faiss").exists():
        log.info("loading_prebuilt_index")
        _index.load(index_dir)
    else:
        log.info("no_index_found_building_fresh")
        ingester = CorpusIngester()
        _sql_engine = TableSQLEngine()
        docs = list(ingester.ingest_all(settings.corpus_dir))
        for doc in docs:
            _sql_engine.register_document(doc)
        _index.build(docs)
        _index.save(index_dir)

    if _sql_engine is None:
        _sql_engine = TableSQLEngine()

    _retriever = HybridRetriever(_index)
    _pipeline = ReasoningPipeline(_retriever, _sql_engine)
    log.info("pipeline_ready")


# ─────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    doc_filter: Optional[list[str]] = None


class IngestRequest(BaseModel):
    corpus_dir: str


class EvalRequest(BaseModel):
    benchmark_path: str
    max_questions: Optional[int] = 100


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "index_loaded": _index is not None and len(_index.chunks) > 0,
        "n_chunks": len(_index.chunks) if _index else 0,
        "n_tables": len(_sql_engine.table_names()) if _sql_engine else 0,
    }


@app.post("/query", response_model=AgentAnswer)
async def query(req: QueryRequest):
    if _pipeline is None:
        raise HTTPException(503, "Pipeline not initialized")
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty")
    return _pipeline.answer(req.question)


@app.post("/ingest")
async def ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    corpus_dir = Path(req.corpus_dir)
    if not corpus_dir.exists():
        raise HTTPException(404, f"Directory not found: {corpus_dir}")

    def _ingest():
        global _index, _retriever, _sql_engine, _pipeline
        ingester = CorpusIngester()
        sql_engine = TableSQLEngine()
        docs = list(ingester.ingest_all(corpus_dir))
        for doc in docs:
            sql_engine.register_document(doc)
        index = DocumentIndex()
        index.build(docs)
        index.save(settings.index_dir)
        _index = index
        _sql_engine = sql_engine
        _retriever = HybridRetriever(index)
        _pipeline = ReasoningPipeline(_retriever, sql_engine)
        log.info("re_ingestion_complete", n_docs=len(docs))

    background_tasks.add_task(_ingest)
    return {"status": "ingestion_started"}


@app.post("/eval")
async def evaluate(req: EvalRequest):
    if _pipeline is None:
        raise HTTPException(503, "Pipeline not initialized")
    bench_path = Path(req.benchmark_path)
    if not bench_path.exists():
        raise HTTPException(404, f"Benchmark not found: {bench_path}")

    harness = EvaluationHarness(_pipeline)
    summary = harness.run(bench_path, max_questions=req.max_questions)
    harness.save_results(settings.eval_dir / "latest")
    return summary.__dict__


@app.get("/schema")
async def schema():
    if _sql_engine is None:
        raise HTTPException(503, "SQL engine not initialized")
    return {
        "tables": _sql_engine.table_names(),
        "schema_summary": _sql_engine.schema_summary(),
    }
