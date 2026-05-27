"""Main CLI interface."""

import sys
from pathlib import Path
import click
import json

from src.ingestion import initialize_system
from src.evaluation import BenchmarkEvaluator
from src.logging import get_logger

logger = get_logger("cli")


@click.group()
def cli():
    """Office-QA Challenge - Production-grade Document Reasoning Agent."""
    pass


@cli.command()
@click.argument("corpus_path", type=click.Path(exists=True))
def ingest(corpus_path: str):
    """Ingest documents from a directory."""
    click.echo(f"Ingesting documents from: {corpus_path}")

    system = initialize_system()
    count = system.ingest_directory(Path(corpus_path))

    stats = system.get_corpus_stats()
    click.echo(f"\n✓ Ingested {count} documents")
    click.echo(f"  - Total documents: {stats['num_documents']}")
    click.echo(f"  - Total chunks: {stats['num_chunks']}")
    click.echo(f"  - Total tables: {stats['num_tables']}")
    click.echo(f"  - Total characters: {stats['total_chars']:,}")


@cli.command()
@click.argument("question", type=str)
@click.option("--json", is_flag=True, help="Output as JSON")
def ask(question: str, json_output: bool):
    """Ask a question about the corpus."""
    system = initialize_system()

    click.echo(f"Question: {question}\n")
    click.echo("Reasoning...", nl=False)

    result = system.answer_question(question)

    click.echo("\r" + " " * 30 + "\r", nl=False)

    if json_output:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Answer: {result['answer']}\n")
        click.echo(f"Confidence: {result['confidence']:.2%}")
        click.echo(f"Grounded: {result['is_grounded']}")

        if result['sources']:
            click.echo(f"Sources: {result['sources']}")

        if result['evidence']:
            click.echo(f"\nEvidence ({len(result['evidence'])} chunks):")
            for i, ev in enumerate(result['evidence'][:3]):
                click.echo(f"  {i+1}. {ev['source_document']} (score: {ev['relevance_score']:.2f})")


@cli.command()
@click.argument("questions_file", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), help="Output results file")
def batch(questions_file: str, output: str):
    """Answer questions from a file (one per line)."""
    system = initialize_system()

    with open(questions_file, 'r') as f:
        questions = [line.strip() for line in f if line.strip()]

    click.echo(f"Answering {len(questions)} questions...\n")

    results = []
    with click.progressbar(questions, label="Processing") as bar:
        for question in bar:
            result = system.answer_question(question)
            results.append(result)

    if output:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
        click.echo(f"\n✓ Results saved to: {output}")

    # Print summary
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    grounded_count = sum(1 for r in results if r['is_grounded'])

    click.echo(f"\nSummary:")
    click.echo(f"  - Total questions: {len(results)}")
    click.echo(f"  - Avg confidence: {avg_confidence:.2%}")
    click.echo(f"  - Grounded answers: {grounded_count}/{len(results)}")


@cli.command()
def stats():
    """Show corpus statistics."""
    system = initialize_system()
    stats = system.get_corpus_stats()

    click.echo("\nCorpus Statistics:")
    click.echo(f"  - Documents: {stats['num_documents']}")
    click.echo(f"  - Chunks: {stats['num_chunks']}")
    click.echo(f"  - Tables: {stats['num_tables']}")
    click.echo(f"  - Total size: {stats['total_chars']:,} characters\n")


@cli.command()
def version():
    """Show version."""
    click.echo("Office-QA Agent v0.1.0")


if __name__ == "__main__":
    cli()
