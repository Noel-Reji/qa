#!/bin/bash

# Office-QA Quick Start Script

set -e

echo "=== Office-QA System Setup ==="
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e . > /dev/null 2>&1
echo "✓ Dependencies installed"

# Setup environment
if [ ! -f ".env" ]; then
    echo "Setting up .env file..."
    cp .env.example .env
    echo "⚠ Please edit .env with your API keys"
    echo ""
fi

# Create necessary directories
mkdir -p data/corpus data/indices data/results logs data/traces
echo "✓ Directories created"

# Run sample
echo ""
echo "=== Testing System ==="
echo ""

# Ingest sample document
echo "Ingesting sample document..."
python -c "
from src.ingestion import initialize_system
system = initialize_system()
count = system.ingest_directory('data/corpus')
stats = system.get_corpus_stats()
print(f'✓ Ingested {count} documents')
print(f'  - Chunks: {stats[\"num_chunks\"]}')
" || echo "⚠ Ingestion demo skipped (might need API key)"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env with your settings (especially LLM_API_KEY)"
echo "2. Run: python -m src.cli ingest data/corpus"
echo "3. Run: python -m src.cli ask 'Your question?'"
echo ""
echo "For more examples, see USAGE.md"
