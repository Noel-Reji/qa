"""Structured logging and tracing system."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from loguru import logger as loguru_logger


class ReasoningTraceLevel(str, Enum):
    """Levels for reasoning trace events."""
    QUERY_UNDERSTANDING = "query_understanding"
    RETRIEVAL = "retrieval"
    RERANKING = "reranking"
    EVIDENCE_VALIDATION = "evidence_validation"
    COMPUTATION = "computation"
    REASONING = "reasoning"
    VERIFICATION = "verification"
    DECISION = "decision"
    ERROR = "error"


@dataclass
class RetrievalTrace:
    """Trace for retrieval operations."""
    query: str
    strategy: str
    num_chunks_retrieved: int
    retrieval_scores: list[float]
    retrieval_time_ms: float
    sources: list[str]
    metadata: Dict[str, Any]


@dataclass
class ReasoningTrace:
    """Trace for reasoning operations."""
    step: int
    level: ReasoningTraceLevel
    description: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    latency_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionTrace:
    """Complete execution trace for an answer."""
    query_id: str
    timestamp: str
    query: str
    question_type: str
    retrieval_traces: list[RetrievalTrace]
    reasoning_traces: list[ReasoningTrace]
    final_answer: str
    confidence_score: float
    total_latency_ms: float
    total_tokens: int
    estimated_cost: float
    sources_used: list[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['retrieval_traces'] = [asdict(t) for t in self.retrieval_traces]
        data['reasoning_traces'] = [asdict(t) for t in self.reasoning_traces]
        return data

    def to_json(self) -> str:
        """Convert to JSON."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class TraceLogger:
    """Logger for execution traces."""

    def __init__(self, trace_dir: Path):
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.current_trace: Optional[ExecutionTrace] = None

    def start_trace(self, query_id: str, query: str, question_type: str) -> None:
        """Start a new execution trace."""
        self.current_trace = ExecutionTrace(
            query_id=query_id,
            timestamp=datetime.utcnow().isoformat(),
            query=query,
            question_type=question_type,
            retrieval_traces=[],
            reasoning_traces=[],
            final_answer="",
            confidence_score=0.0,
            total_latency_ms=0.0,
            total_tokens=0,
            estimated_cost=0.0,
            sources_used=[],
            metadata={},
        )

    def add_retrieval_trace(self, trace: RetrievalTrace) -> None:
        """Add retrieval trace."""
        if self.current_trace:
            self.current_trace.retrieval_traces.append(trace)

    def add_reasoning_trace(self, trace: ReasoningTrace) -> None:
        """Add reasoning trace."""
        if self.current_trace:
            self.current_trace.reasoning_traces.append(trace)

    def finalize_trace(
        self,
        final_answer: str,
        confidence_score: float,
        total_latency_ms: float,
        total_tokens: int,
        estimated_cost: float,
        sources_used: list[str],
    ) -> Optional[ExecutionTrace]:
        """Finalize and save trace."""
        if not self.current_trace:
            return None

        self.current_trace.final_answer = final_answer
        self.current_trace.confidence_score = confidence_score
        self.current_trace.total_latency_ms = total_latency_ms
        self.current_trace.total_tokens = total_tokens
        self.current_trace.estimated_cost = estimated_cost
        self.current_trace.sources_used = sources_used

        trace_file = self.trace_dir / f"{self.current_trace.query_id}.json"
        with open(trace_file, 'w') as f:
            f.write(self.current_trace.to_json())

        trace = self.current_trace
        self.current_trace = None
        return trace


class SystemLogger:
    """Main system logger with structured output."""

    def __init__(self, name: str, log_dir: Path, log_level: str = "INFO"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Remove default handler
        loguru_logger.remove()

        # Console handler
        loguru_logger.add(
            sys.stdout,
            format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level=log_level,
        )

        # File handler
        log_file = self.log_dir / f"{name}.log"
        loguru_logger.add(
            str(log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            rotation="100 MB",
        )

        # JSON handler for structured logging
        json_log_file = self.log_dir / f"{name}_structured.jsonl"
        loguru_logger.add(
            lambda msg: self._json_sink(msg, json_log_file),
            format="{message}",
            level=log_level,
            serialize=False,
        )

        self.logger = loguru_logger.bind(name=name)
        self.trace_logger = TraceLogger(self.log_dir / "traces")

    def _json_sink(self, message, json_log_file: Path) -> None:
        """Sink for JSON logging."""
        try:
            # Only log structured records
            if hasattr(message, 'record'):
                record = message.record
                log_entry = {
                    "timestamp": record["time"].isoformat(),
                    "level": record["level"].name,
                    "logger": record["name"],
                    "function": record["function"],
                    "line": record["line"],
                    "message": record["message"],
                }
                with open(json_log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            loguru_logger.error(f"Failed to write JSON log: {e}")

    def debug(self, msg: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(msg, **kwargs)

    def start_trace(self, query_id: str, query: str, question_type: str = "general") -> None:
        """Start execution trace."""
        self.trace_logger.start_trace(query_id, query, question_type)
        self.info(f"Started trace for query: {query_id}")

    def add_retrieval_trace(self, trace: RetrievalTrace) -> None:
        """Add retrieval trace."""
        self.trace_logger.add_retrieval_trace(trace)

    def add_reasoning_trace(self, trace: ReasoningTrace) -> None:
        """Add reasoning trace."""
        self.trace_logger.add_reasoning_trace(trace)

    def finalize_trace(
        self,
        final_answer: str,
        confidence_score: float,
        total_latency_ms: float,
        total_tokens: int,
        estimated_cost: float,
        sources_used: list[str],
    ) -> Optional[ExecutionTrace]:
        """Finalize trace."""
        return self.trace_logger.finalize_trace(
            final_answer, confidence_score, total_latency_ms, total_tokens, estimated_cost, sources_used
        )


# Global logger instances
_loggers: Dict[str, SystemLogger] = {}


def get_logger(name: str, log_dir: Path = Path("logs"), log_level: str = "INFO") -> SystemLogger:
    """Get or create logger."""
    if name not in _loggers:
        _loggers[name] = SystemLogger(name, log_dir, log_level)
    return _loggers[name]
