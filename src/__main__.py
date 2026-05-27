"""Main entry point."""

from src.ingestion import initialize_system, get_system
from src.logging import get_logger

logger = get_logger("main")


def main():
    """Main entry point."""
    logger.info("Initializing Office-QA system...")
    system = initialize_system()
    logger.info("System initialized successfully")
    return system


if __name__ == "__main__":
    system = main()
    
    # Example usage
    print("\n=== Office-QA Agent ===\n")
    
    # Ingest sample documents
    from pathlib import Path
    sample_docs = Path("data/corpus")
    if sample_docs.exists():
        print(f"Ingesting documents from {sample_docs}...")
        count = system.ingest_directory(sample_docs)
        print(f"Ingested {count} documents\n")
    
    # Example questions
    questions = [
        "What are the main findings?",
        "What is the total amount?",
        "When was this created?",
    ]
    
    for q in questions:
        print(f"Q: {q}")
        result = system.answer_question(q)
        print(f"A: {result['answer']}")
        print(f"Confidence: {result['confidence']:.1%}\n")
