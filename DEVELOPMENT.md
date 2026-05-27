# Development Guide

## Setting Up Development Environment

### Prerequisites
- Python 3.10+
- Git
- Virtual environment tool (venv)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/Noel-Reji/qa.git
cd qa

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,ui]"

# Setup pre-commit hooks (optional)
pre-commit install
```

### Quick Setup Script

```bash
bash setup.sh
```

## Project Structure

```
office-qa/
├── src/
│   ├── config/              # Configuration management
│   │   ├── settings.py      # Settings dataclass
│   │   └── __init__.py
│   │
│   ├── parsing/             # Document parsing
│   │   ├── document_parser.py
│   │   └── __init__.py
│   │
│   ├── retrieval/           # Retrieval system
│   │   ├── hybrid_retriever.py
│   │   └── __init__.py
│   │
│   ├── sql_engine/          # SQL & table reasoning
│   │   ├── table_engine.py
│   │   └── __init__.py
│   │
│   ├── reasoning/           # Multi-stage agent
│   │   ├── multi_stage_agent.py
│   │   └── __init__.py
│   │
│   ├── evaluation/          # Benchmarking
│   │   ├── evaluator.py
│   │   └── __init__.py
│   │
│   ├── logging/             # Logging & tracing
│   │   ├── trace_logger.py
│   │   └── __init__.py
│   │
│   ├── utils/               # Utilities & models
│   │   ├── data_models.py
│   │   ├── helpers.py
│   │   └── __init__.py
│   │
│   ├── ingestion/           # Orchestration
│   │   ├── orchestrator.py
│   │   └── __init__.py
│   │
│   ├── cli.py               # CLI interface
│   ├── __main__.py          # Entry point
│   └── __init__.py
│
├── tests/                   # Unit tests
│   └── test_core.py
│
├── notebooks/               # Jupyter notebooks
│   └── 01_getting_started.py
│
├── data/
│   ├── corpus/              # Input documents
│   ├── indices/             # Retrieval indices
│   ├── results/             # Evaluation results
│   └── traces/              # Execution traces
│
├── pyproject.toml           # Project metadata
├── .env.example             # Environment template
├── setup.sh                 # Setup script
├── Dockerfile               # Docker build
├── docker-compose.yml       # Docker compose
├── .gitignore               # Git ignore
├── README.md                # Project README
├── ARCHITECTURE.md          # Architecture guide
├── USAGE.md                 # Usage guide
├── CONFIG.md                # Configuration reference
└── LICENSE                  # MIT License
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_core.py::TestDataModels -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/ --line-length=100

# Lint
ruff check src/ tests/

# Type checking
mypy src/

# All checks
bash scripts/check_code_quality.sh
```

### Local Testing

```bash
# Ingest sample data
python -m src.cli ingest data/corpus

# Test query
python -m src.cli ask "What is the total?"

# Run batch
echo -e "What is revenue?\nWho is CEO?" | python -m src.cli batch /dev/stdin
```

## Adding New Features

### Adding a New Parsing Format

1. Create parser class in `src/parsing/document_parser.py`:

```python
class CustomDocumentParser(DocumentParser):
    def parse(self, file_path: Path) -> Optional[Document]:
        # Implement parsing
        pass
```

2. Register in `DocumentParsingEngine.__init__()`:

```python
self.parsers[DocumentType.CUSTOM] = CustomDocumentParser()
```

3. Add tests in `tests/test_parsing.py`

### Adding a New Reasoning Stage

1. Create stage class in `src/reasoning/multi_stage_agent.py`:

```python
class CustomStage:
    def execute(self, input_data):
        # Implement stage logic
        pass
```

2. Add to pipeline in `MultiStageReasoningAgent.answer_question()`

3. Add logging for traceability

4. Add tests

### Adding a New LLM Provider

1. Update `src/config/settings.py` - add provider to choices

2. Create adapter in `src/llm/` (new module):

```python
class GeminiAdapter:
    def generate(self, prompt, max_tokens):
        # Implement Gemini API call
        pass
```

3. Update reasoning stages to use adapter

4. Test with sample queries

## Testing Guidelines

### Unit Tests

```python
class TestMyFeature:
    def test_basic_functionality(self):
        # Arrange
        input_data = ...
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result == expected
```

### Integration Tests

```python
def test_end_to_end_question_answering():
    system = initialize_system()
    system.ingest_directory("data/corpus")
    
    result = system.answer_question("What is total?")
    assert result['confidence'] > 0.5
    assert result['is_grounded']
```

### Benchmark Tests

```python
def test_performance():
    system = initialize_system()
    system.ingest_directory("data/corpus")
    
    import time
    start = time.time()
    result = system.answer_question("What is total?")
    latency = time.time() - start
    
    assert latency < 1.0  # Should be under 1 second
```

## Documentation

### Adding Documentation

1. Update relevant `.md` files
2. Add docstrings to new functions/classes
3. Include usage examples
4. Document configuration options

### Docstring Format

```python
def my_function(arg1: str, arg2: int) -> Dict[str, Any]:
    """Brief description.
    
    Longer description explaining the function behavior,
    edge cases, and usage.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When validation fails
        
    Example:
        >>> result = my_function("test", 42)
        >>> print(result)
    """
    pass
```

## Performance Optimization

### Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run code to profile
system = initialize_system()
system.answer_question("What is total?")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Memory Profiling

```bash
pip install memory-profiler
python -m memory_profiler src/main.py
```

## Debugging

### Enable Debug Logging

```python
import logging
from src.logging import get_logger

logger = get_logger("debug", log_level="DEBUG")
logger.debug("Debug information")
```

### Interactive Debugging

```python
import pdb

# Set breakpoint
pdb.set_trace()

# Or use Python 3.7+ syntax
breakpoint()
```

### Execution Traces

Traces are automatically saved to `data/traces/` with full information about:
- Retrieval scores and results
- Reasoning steps
- Computation results
- Confidence scores
- Token usage
- Latency

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest tests/
      - run: black --check src/
      - run: ruff check src/
```

## Release Process

1. Update version in `src/__init__.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.1.0`
4. Push: `git push --tags`
5. Build distribution: `python -m build`
6. Upload to PyPI: `twine upload dist/*`

## Common Development Tasks

### Add Dependencies

```bash
# Edit pyproject.toml
# Add to [project] dependencies section
pip install -e .
```

### Update Configuration Options

1. Edit `src/config/settings.py`
2. Add to appropriate config class
3. Update `.env.example`
4. Document in `CONFIG.md`

### Add Logging

```python
from src.logging import get_logger

logger = get_logger(__name__)
logger.info("Message")
logger.error("Error occurred")
```

### Add Metrics

```python
from src.evaluation import BenchmarkEvaluator

evaluator = BenchmarkEvaluator()
# Add custom metric methods as needed
```

## Troubleshooting Development

### Import Errors

```bash
# Reinstall package in editable mode
pip install -e . --force-reinstall
```

### Cache Issues

```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete

# Clear build artifacts
rm -rf build/ dist/ *.egg-info/
```

### Dependency Conflicts

```bash
# Start fresh
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Contributing Guidelines

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes with descriptive messages
4. Add/update tests
5. Run code quality checks
6. Push to fork: `git push origin feature/my-feature`
7. Create Pull Request

## Code Review Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] No breaking changes (or documented)
- [ ] Performance impact considered
- [ ] Security implications checked
- [ ] Works with existing codebase

## Resources

- [Python Best Practices](https://peps.python.org/pep-0008/)
- [Type Hints](https://docs.python.org/3/library/typing.html)
- [Testing with Pytest](https://docs.pytest.org/)
- [Git Workflow](https://guides.github.com/introduction/flow/)

---

For questions or issues, open a GitHub issue or discussion.
