"""Evaluation and benchmarking system."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from src.utils import EvaluationResult, Answer
from src.config import settings
from src.logging import get_logger

logger = get_logger("evaluation")


class EvaluationMetrics:
    """Metrics for evaluation."""

    @staticmethod
    def exact_match(predicted: str, expected: str) -> bool:
        """Check exact match."""
        return predicted.strip().lower() == expected.strip().lower()

    @staticmethod
    def semantic_similarity(predicted: str, expected: str) -> float:
        """Compute semantic similarity."""
        # Placeholder - would use embedding similarity or semantic matching
        # For now, use simple word overlap
        pred_words = set(predicted.lower().split())
        exp_words = set(expected.lower().split())

        if not exp_words:
            return 1.0 if not pred_words else 0.0

        intersection = len(pred_words & exp_words)
        union = len(pred_words | exp_words)

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def retrieval_recall(retrieved_docs: List[str], expected_docs: List[str]) -> float:
        """Compute retrieval recall."""
        if not expected_docs:
            return 1.0

        found = sum(1 for doc in expected_docs if doc in retrieved_docs)
        return found / len(expected_docs)

    @staticmethod
    def grounding_score(answer: Answer) -> float:
        """Compute grounding score."""
        if not answer.evidence:
            return 0.0

        avg_confidence = sum(e.grounding_confidence for e in answer.evidence) / len(answer.evidence)
        return avg_confidence


class BenchmarkEvaluator:
    """Evaluator for benchmarks."""

    def __init__(self, results_dir: Path = None):
        self.results_dir = Path(results_dir or settings.evaluation.results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.metrics = EvaluationMetrics()

    def evaluate_answer(
        self,
        answer: Answer,
        expected_answer: Optional[str] = None,
        expected_sources: Optional[List[str]] = None,
    ) -> EvaluationResult:
        """Evaluate a single answer."""
        result = EvaluationResult(
            query_id=answer.answer_id,
            question=answer.query,
            expected_answer=expected_answer,
            generated_answer=answer.answer_text,
        )

        # Exact match
        if expected_answer:
            result.exact_match = self.metrics.exact_match(
                answer.answer_text, expected_answer
            )

        # Semantic similarity
        if expected_answer:
            result.semantic_similarity = self.metrics.semantic_similarity(
                answer.answer_text, expected_answer
            )

        # Retrieval recall
        if expected_sources:
            retrieved_sources = [e.source_document for e in answer.evidence]
            result.retrieval_recall = self.metrics.retrieval_recall(
                retrieved_sources, expected_sources
            )

        # Grounding score
        result.grounding_score = self.metrics.grounding_score(answer)

        # Cost and latency
        metadata = answer.metadata or {}
        result.latency_ms = metadata.get("total_time_ms", 0.0)
        result.token_count = metadata.get("token_count", 0)
        result.estimated_cost = metadata.get("estimated_cost", 0.0)

        return result

    def evaluate_batch(
        self,
        answers: List[Answer],
        benchmark_data: List[Dict[str, Any]]
    ) -> List[EvaluationResult]:
        """Evaluate a batch of answers."""
        results = []

        for answer, expected in zip(answers, benchmark_data):
            result = self.evaluate_answer(
                answer,
                expected.get("expected_answer"),
                expected.get("expected_sources"),
            )
            results.append(result)

        return results

    def compute_aggregate_metrics(self, results: List[EvaluationResult]) -> Dict[str, float]:
        """Compute aggregate metrics."""
        if not results:
            return {}

        metrics = {
            "total_queries": len(results),
            "accuracy": sum(1 for r in results if r.exact_match) / len(results),
            "avg_semantic_similarity": sum(r.semantic_similarity for r in results) / len(results),
            "avg_retrieval_recall": sum(r.retrieval_recall for r in results) / len(results),
            "avg_grounding_score": sum(r.grounding_score for r in results) / len(results),
            "avg_latency_ms": sum(r.latency_ms for r in results) / len(results),
            "total_tokens": sum(r.token_count for r in results),
            "total_estimated_cost": sum(r.estimated_cost for r in results),
            "errors": sum(1 for r in results if r.error is not None),
        }

        return metrics

    def save_results(self, results: List[EvaluationResult], benchmark_name: str) -> Path:
        """Save evaluation results."""
        output_file = self.results_dir / f"{benchmark_name}_results.jsonl"

        with open(output_file, 'w') as f:
            for result in results:
                f.write(json.dumps(asdict(result)) + '\n')

        logger.info(f"Saved results to {output_file}")

        # Save aggregate metrics
        metrics = self.compute_aggregate_metrics(results)
        metrics_file = self.results_dir / f"{benchmark_name}_metrics.json"

        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Saved metrics to {metrics_file}")

        return output_file

    def print_results(self, results: List[EvaluationResult]) -> None:
        """Print evaluation results."""
        metrics = self.compute_aggregate_metrics(results)

        print("\n" + "=" * 60)
        print("EVALUATION RESULTS")
        print("=" * 60)
        print(f"Total Queries: {metrics.get('total_queries', 0)}")
        print(f"Accuracy (Exact Match): {metrics.get('accuracy', 0):.2%}")
        print(f"Avg Semantic Similarity: {metrics.get('avg_semantic_similarity', 0):.2f}")
        print(f"Avg Retrieval Recall: {metrics.get('avg_retrieval_recall', 0):.2f}")
        print(f"Avg Grounding Score: {metrics.get('avg_grounding_score', 0):.2f}")
        print(f"Avg Latency (ms): {metrics.get('avg_latency_ms', 0):.1f}")
        print(f"Total Tokens: {metrics.get('total_tokens', 0)}")
        print(f"Total Cost (USD): ${metrics.get('total_estimated_cost', 0):.4f}")
        print(f"Errors: {metrics.get('errors', 0)}")
        print("=" * 60 + "\n")
