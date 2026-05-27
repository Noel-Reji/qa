"""Getting Started with Office-QA

This notebook demonstrates basic usage of the Office-QA system.
"""

# %%
# Install (if needed)
# !pip install -e /path/to/office-qa[dev]

# %%
# Imports
from src.ingestion import initialize_system
from src.logging import get_logger
from pathlib import Path

# %%
# Initialize system
print("Initializing Office-QA system...")
system = initialize_system()
print("✓ System initialized")

# %%
# View corpus statistics
stats = system.get_corpus_stats()
print("\nCorpus Statistics:")
print(f"  Documents: {stats['num_documents']}")
print(f"  Chunks: {stats['num_chunks']}")
print(f"  Tables: {stats['num_tables']}")

# %%
# Ask a question
question = "What is the total?"

print(f"\nQuestion: {question}")
print("Reasoning...")

result = system.answer_question(question)

print(f"\nAnswer: {result['answer']}")
print(f"Confidence: {result['confidence']:.1%}")
print(f"Grounded: {result['is_grounded']}")

# %%
# View evidence
print(f"\nEvidence ({len(result['evidence'])} chunks used):")
for i, ev in enumerate(result['evidence'][:3]):
    print(f"\n  {i+1}. {ev['source_document']}")
    print(f"     Relevance: {ev['relevance_score']:.2f}")
    print(f"     Content: {ev['chunk_content'][:100]}...")

# %%
# Batch processing
questions = [
    "What is the total revenue?",
    "What is the profit margin?",
    "Who is the CEO?",
]

print(f"\nProcessing {len(questions)} questions...")
results = system.batch_answer_questions(questions)

for q, r in zip(questions, results):
    print(f"\nQ: {q}")
    print(f"A: {r['answer'][:100]}...")
    print(f"   Confidence: {r['confidence']:.1%}")
