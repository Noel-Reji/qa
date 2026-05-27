#!/usr/bin/env python3
"""
Sentient Arena CLI
Usage:
  python cli.py ingest --corpus ./data/corpus
  python cli.py query "What was the total revenue in FY2023?"
  python cli.py eval --benchmark ./data/eval/benchmark.jsonl
  python cli.py serve
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()


def cmd_ingest(args):
    from ingestion.parser import CorpusIngester
    from retrieval.hybrid_retriever import DocumentIndex
    from sql_engine.table_db import TableSQLEngine
    from config.settings import settings

    corpus_dir = Path(args.corpus)
    if not corpus_dir.exists():
        console.print(f"[red]Corpus directory not found: {corpus_dir}[/red]")
        sys.exit(1)

    console.print(f"[bold]Ingesting corpus from:[/bold] {corpus_dir}")
    ingester = CorpusIngester()
    sql_engine = TableSQLEngine()
    docs = list(ingester.ingest_all(corpus_dir))

    console.print(f"[green]Parsed {len(docs)} documents[/green]")
    total_chunks = sum(len(d.chunks) for d in docs)
    total_tables = sum(len(d.tables) for d in docs)
    console.print(f"  Chunks: {total_chunks}  |  Tables: {total_tables}")

    for doc in docs:
        sql_engine.register_document(doc)

    index = DocumentIndex()
    with console.status("[bold]Building index (BM25 + FAISS)…[/bold]"):
        index.build(docs)

    index_dir = settings.index_dir
    index.save(index_dir)
    console.print(f"[green]Index saved to {index_dir}[/green]")


def cmd_query(args):
    from retrieval.hybrid_retriever import DocumentIndex, HybridRetriever
    from sql_engine.table_db import TableSQLEngine
    from agents.pipeline import ReasoningPipeline
    from config.settings import settings

    index_dir = settings.index_dir
    if not (index_dir / "dense.faiss").exists():
        console.print("[red]No index found. Run 'ingest' first.[/red]")
        sys.exit(1)

    with console.status("Loading index…"):
        index = DocumentIndex()
        index.load(index_dir)
        retriever = HybridRetriever(index)
        sql_engine = TableSQLEngine()
        pipeline = ReasoningPipeline(retriever, sql_engine)

    question = args.question
    console.print(f"\n[bold blue]Question:[/bold blue] {question}\n")

    with console.status("[bold]Reasoning…[/bold]"):
        answer = pipeline.answer(question)

    console.print(Panel(
        f"[bold green]{answer.answer}[/bold green]",
        title="Answer",
        border_style="green",
    ))

    t = Table(show_header=True, header_style="bold magenta")
    t.add_column("Field")
    t.add_column("Value")
    t.add_row("Confidence", f"{answer.confidence:.0%}")
    t.add_row("Model", answer.model_used)
    t.add_row("Question Type", answer.question_type)
    t.add_row("Latency", f"{answer.latency_ms:.0f}ms")
    t.add_row("Tokens", f"in={answer.input_tokens} out={answer.output_tokens}")
    t.add_row("Evidence Chunks", str(len(answer.evidence_chunks)))
    t.add_row("SQL Queries", str(len(answer.sql_queries)))
    console.print(t)

    if answer.sql_queries and args.verbose:
        console.print("\n[bold]SQL Executed:[/bold]")
        for q in answer.sql_queries:
            console.print(f"  [dim]{q}[/dim]")

    if args.verbose:
        console.print(f"\n[dim]Trace: {answer.reasoning_summary}[/dim]")


def cmd_eval(args):
    from retrieval.hybrid_retriever import DocumentIndex, HybridRetriever
    from sql_engine.table_db import TableSQLEngine
    from agents.pipeline import ReasoningPipeline
    from evaluation.harness import EvaluationHarness
    from config.settings import settings

    bench_path = Path(args.benchmark)
    if not bench_path.exists():
        console.print(f"[red]Benchmark not found: {bench_path}[/red]")
        sys.exit(1)

    with console.status("Loading index…"):
        index = DocumentIndex()
        index.load(settings.index_dir)
        retriever = HybridRetriever(index)
        sql_engine = TableSQLEngine()
        pipeline = ReasoningPipeline(retriever, sql_engine)

    harness = EvaluationHarness(pipeline)
    with console.status(f"[bold]Evaluating {args.max_q} questions…[/bold]"):
        summary = harness.run(bench_path, max_questions=args.max_q)

    t = Table(title="Evaluation Results", header_style="bold cyan")
    t.add_column("Metric")
    t.add_column("Value")
    t.add_row("Questions", str(summary.n_questions))
    t.add_row("Exact Match", f"{summary.exact_match_rate:.1%}")
    t.add_row("Fuzzy Match (≥80)", f"{summary.fuzzy_match_rate:.1%}")
    t.add_row("ROUGE-L Mean", f"{summary.rouge_l_mean:.3f}")
    t.add_row("Numerical Accuracy", f"{summary.numerical_accuracy:.1%}")
    t.add_row("Abstention Rate", f"{summary.abstention_rate:.1%}")
    t.add_row("Avg Latency", f"{summary.avg_latency_ms:.0f}ms")
    t.add_row("P95 Latency", f"{summary.p95_latency_ms:.0f}ms")
    t.add_row("Total Tokens", f"{summary.total_input_tokens + summary.total_output_tokens:,}")
    t.add_row("Est. Cost", f"${summary.cost_estimate_usd:.4f}")
    console.print(t)

    out_dir = settings.eval_dir / "latest"
    harness.save_results(out_dir)
    console.print(f"\n[green]Full results saved to {out_dir}[/green]")

    if args.errors:
        console.print("\n[bold red]Worst 5 Questions:[/bold red]")
        for item in harness.error_analysis(top_n=5):
            console.print(f"  Q: {item['question'][:80]}")
            console.print(f"  Gold: {item['gold']}  Pred: {item['predicted'][:60]}")
            console.print()


def cmd_serve(args):
    import uvicorn
    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)


def main():
    parser = argparse.ArgumentParser(description="Sentient Arena Office-QA CLI")
    sub = parser.add_subparsers(dest="command")

    # ingest
    p_ingest = sub.add_parser("ingest", help="Parse and index a corpus")
    p_ingest.add_argument("--corpus", default="data/corpus")

    # query
    p_query = sub.add_parser("query", help="Ask a question")
    p_query.add_argument("question")
    p_query.add_argument("--verbose", action="store_true")

    # eval
    p_eval = sub.add_parser("eval", help="Run benchmark evaluation")
    p_eval.add_argument("--benchmark", default="data/eval/benchmark.jsonl")
    p_eval.add_argument("--max-q", type=int, default=100, dest="max_q")
    p_eval.add_argument("--errors", action="store_true", help="Show worst questions")

    # serve
    p_serve = sub.add_parser("serve", help="Start FastAPI server")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")

    args = parser.parse_args()
    if args.command == "ingest":   cmd_ingest(args)
    elif args.command == "query":  cmd_query(args)
    elif args.command == "eval":   cmd_eval(args)
    elif args.command == "serve":  cmd_serve(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
