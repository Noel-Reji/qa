"""Multi-stage reasoning agent for document QA."""

import time
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass

from src.utils import (
    Question,
    Answer,
    Evidence,
    Chunk,
    generate_id,
    Timer,
)
from src.config import settings
from src.logging import get_logger, ReasoningTrace, ReasoningTraceLevel, RetrievalTrace
from src.retrieval import HybridRetriever
from src.sql_engine import TableReasoningEngine, ComputationEngine
from src.parsing import DocumentParsingEngine

logger = get_logger("reasoning")


class QuestionType(str, Enum):
    """Types of questions."""
    FACTUAL = "factual"
    NUMERICAL = "numerical"
    COMPARATIVE = "comparative"
    TEMPORAL = "temporal"
    MULTI_HOP = "multi_hop"
    TABLE_REASONING = "table_reasoning"


@dataclass
class ReasoningContext:
    """Context for reasoning."""
    question: Question
    retrieved_chunks: List[Chunk]
    evidence: List[Evidence]
    reasoning_steps: List[str]
    confidence_scores: List[float]
    metadata: Dict[str, Any]


class QueryUnderstandingStage:
    """Stage 1: Query Understanding."""

    def __init__(self):
        self.logger = logger

    def execute(self, question: str) -> Dict[str, Any]:
        """Understand the query."""
        result = {
            "question": question,
            "question_type": self._classify_type(question),
            "entities": self._extract_entities(question),
            "keywords": self._extract_keywords(question),
            "requires_computation": self._detect_computation(question),
            "requires_table_reasoning": self._detect_table_reasoning(question),
            "temporal_scope": self._detect_temporal_scope(question),
        }

        self.logger.debug(f"Query understanding: {result}")
        return result

    def _classify_type(self, question: str) -> str:
        """Classify question type."""
        q_lower = question.lower()

        if any(word in q_lower for word in ["compare", "difference", "vs", "than"]):
            return QuestionType.COMPARATIVE.value
        elif any(word in q_lower for word in ["when", "date", "time", "year", "month"]):
            return QuestionType.TEMPORAL.value
        elif any(word in q_lower for word in ["how many", "count", "total", "sum", "average"]):
            return QuestionType.NUMERICAL.value
        elif any(word in q_lower for word in ["table", "data", "row", "column", "cell"]):
            return QuestionType.TABLE_REASONING.value
        else:
            return QuestionType.FACTUAL.value

    def _extract_entities(self, question: str) -> List[str]:
        """Extract named entities."""
        # Simple entity extraction - can be improved with NER
        entities = []
        # Look for capitalized words
        for word in question.split():
            if word[0].isupper() and len(word) > 2:
                entities.append(word)
        return entities

    def _extract_keywords(self, question: str) -> List[str]:
        """Extract keywords."""
        keywords = []
        stop_words = {"the", "a", "an", "and", "or", "is", "are", "what", "who", "when", "where", "why"}
        for word in question.lower().split():
            if word not in stop_words and len(word) > 2:
                keywords.append(word)
        return keywords

    def _detect_computation(self, question: str) -> bool:
        """Detect if computation is needed."""
        keywords = ["calculate", "compute", "sum", "average", "total", "percentage", "ratio"]
        return any(keyword in question.lower() for keyword in keywords)

    def _detect_table_reasoning(self, question: str) -> bool:
        """Detect if table reasoning is needed."""
        keywords = ["table", "data", "row", "column", "cell", "across", "within"]
        return any(keyword in question.lower() for keyword in keywords)

    def _detect_temporal_scope(self, question: str) -> Optional[str]:
        """Detect temporal scope."""
        if "2024" in question or "2025" in question:
            return "recent"
        elif "historical" in question.lower():
            return "historical"
        return None


class RetrievalPlanningStage:
    """Stage 2: Retrieval Planning."""

    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        self.logger = logger

    def execute(self, query: str, query_context: Dict[str, Any]) -> List[Chunk]:
        """Plan and execute retrieval."""
        retrieval_start = time.time()

        # Choose retrieval strategy based on query type
        question_type = query_context.get("question_type")
        is_table_question = query_context.get("requires_table_reasoning", False)

        # Retrieve with appropriate strategy
        if is_table_question:
            top_k = settings.retrieval.top_k * 2  # Get more candidates for table QA
        else:
            top_k = settings.retrieval.top_k

        with Timer() as timer:
            chunks = self.retriever.retrieve(query, top_k=top_k)

        retrieval_time = timer.elapsed_ms

        self.logger.info(f"Retrieved {len(chunks)} chunks in {retrieval_time:.1f}ms")

        return chunks


class EvidenceValidationStage:
    """Stage 3: Evidence Validation."""

    def __init__(self):
        self.logger = logger
        self.confidence_threshold = settings.reasoning.confidence_threshold

    def execute(self, query: str, chunks: List[Chunk]) -> List[Evidence]:
        """Validate and rank evidence."""
        evidence_list = []

        for chunk in chunks:
            # Convert chunk to evidence
            evidence = Evidence(
                chunk_id=chunk.chunk_id,
                chunk_content=chunk.content,
                relevance_score=chunk.retrieval_score,
                source_document=chunk.metadata.filename,
                page_number=chunk.metadata.page_numbers[0] if chunk.metadata.page_numbers else None,
                is_table=chunk.chunk_type.value == "table",
                grounding_confidence=self._compute_grounding_confidence(query, chunk),
            )

            # Only include evidence that meets confidence threshold
            if evidence.grounding_confidence >= self.confidence_threshold:
                evidence_list.append(evidence)

        # Sort by combined score
        evidence_list.sort(
            key=lambda e: 0.6 * e.relevance_score + 0.4 * e.grounding_confidence,
            reverse=True
        )

        self.logger.info(f"Validated {len(evidence_list)} evidence chunks")
        return evidence_list

    def _compute_grounding_confidence(self, query: str, chunk: Chunk) -> float:
        """Compute grounding confidence score."""
        # Simple heuristic - can be improved
        query_words = set(query.lower().split())
        chunk_words = set(chunk.content.lower().split())
        
        overlap = len(query_words & chunk_words)
        if not query_words:
            return 1.0
        
        confidence = min(1.0, overlap / len(query_words))
        return confidence


class ComputationStage:
    """Stage 4: Computation."""

    def __init__(self):
        self.logger = logger
        self.table_engine = TableReasoningEngine()
        self.compute_engine = ComputationEngine()

    def execute(
        self,
        query: str,
        evidence: List[Evidence],
        query_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Perform computations if needed."""
        if not query_context.get("requires_computation"):
            return None

        result = {
            "computation_type": None,
            "result": None,
            "reasoning": [],
        }

        # Check if any evidence contains tables
        for ev in evidence:
            if ev.is_table:
                result["computation_type"] = "table_reasoning"
                # Table reasoning would go here
                self.logger.debug("Table reasoning detected")

        # Try numerical computation on text
        numbers_result = self.compute_engine.extract_and_compute(
            " ".join(e.chunk_content for e in evidence)
        )

        if numbers_result:
            result["computation_type"] = "numerical"
            result["result"] = numbers_result
            result["reasoning"].append(f"Extracted {len(numbers_result['numbers'])} numbers")

        return result if result["computation_type"] else None


class ReasoningStage:
    """Stage 5: Reasoning and Answer Synthesis."""

    def __init__(self):
        self.logger = logger

    def execute(
        self,
        query: str,
        evidence: List[Evidence],
        computation_result: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float, List[str]]:
        """Synthesize answer from evidence."""
        reasoning_steps = []

        if not evidence:
            return "I could not find sufficient evidence to answer this question.", 0.0, reasoning_steps

        # Build answer from evidence
        answer_parts = []
        sources = set()

        for ev in evidence:
            answer_parts.append(ev.chunk_content)
            sources.add(ev.source_document)
            reasoning_steps.append(f"Used evidence from: {ev.source_document}")

        # Combine evidence
        combined_context = " ".join(answer_parts)

        # Generate answer (simplified - would use LLM in production)
        answer = self._generate_answer(query, combined_context, computation_result)
        confidence = self._compute_confidence(evidence, computation_result)

        reasoning_steps.append(f"Confidence score: {confidence:.2f}")

        self.logger.info(f"Generated answer with confidence: {confidence:.2f}")

        return answer, confidence, reasoning_steps

    def _generate_answer(
        self,
        query: str,
        context: str,
        computation_result: Optional[Dict[str, Any]]
    ) -> str:
        """Generate answer text."""
        # This is a placeholder - would use LLM in production
        if computation_result:
            if computation_result.get("computation_type") == "numerical":
                numbers = computation_result["result"]["numbers"]
                if numbers:
                    return f"Based on the documents, the answer involves: {numbers}"

        # Return context-based answer
        if context:
            sentences = context.split(".")
            return sentences[0] if sentences else "No answer found."

        return "I could not generate an answer."

    def _compute_confidence(
        self,
        evidence: List[Evidence],
        computation_result: Optional[Dict[str, Any]]
    ) -> float:
        """Compute confidence score."""
        if not evidence:
            return 0.0

        avg_relevance = sum(e.relevance_score for e in evidence) / len(evidence)
        avg_grounding = sum(e.grounding_confidence for e in evidence) / len(evidence)

        base_confidence = 0.7 * avg_relevance + 0.3 * avg_grounding

        if computation_result:
            base_confidence *= 1.1  # Boost confidence for computation-based answers
            base_confidence = min(1.0, base_confidence)

        return base_confidence


class VerificationStage:
    """Stage 6: Verification."""

    def __init__(self):
        self.logger = logger

    def execute(
        self,
        answer: str,
        evidence: List[Evidence],
        confidence: float
    ) -> Dict[str, Any]:
        """Verify answer consistency."""
        result = {
            "is_grounded": True,
            "consistency_score": 1.0,
            "warnings": [],
        }

        # Check if answer is grounded in evidence
        if not evidence:
            result["is_grounded"] = False
            result["warnings"].append("No evidence found for answer")

        # Check confidence level
        if confidence < settings.reasoning.confidence_threshold:
            result["warnings"].append(f"Low confidence: {confidence:.2f}")

        # Check for hallucinations
        if settings.reasoning.hallucination_check:
            if not evidence and confidence > 0.5:
                result["is_grounded"] = False
                result["warnings"].append("Potential hallucination detected")

        return result


class MultiStageReasoningAgent:
    """Main multi-stage reasoning agent."""

    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        self.logger = logger

        # Initialize stages
        self.query_understanding = QueryUnderstandingStage()
        self.retrieval_planning = RetrievalPlanningStage(retriever)
        self.evidence_validation = EvidenceValidationStage()
        self.computation = ComputationStage()
        self.reasoning = ReasoningStage()
        self.verification = VerificationStage()

    def answer_question(self, question_text: str) -> Answer:
        """Answer a question through multi-stage reasoning."""
        question_id = generate_id("q")
        start_time = time.time()

        # Stage 1: Query Understanding
        query_context = self.query_understanding.execute(question_text)
        self.logger.info(f"Stage 1 - Query understanding: {query_context['question_type']}")

        # Stage 2: Retrieval Planning
        retrieved_chunks = self.retrieval_planning.execute(question_text, query_context)
        self.logger.info(f"Stage 2 - Retrieved {len(retrieved_chunks)} chunks")

        # Stage 3: Evidence Validation
        evidence = self.evidence_validation.execute(question_text, retrieved_chunks)
        self.logger.info(f"Stage 3 - Validated {len(evidence)} evidence chunks")

        # Stage 4: Computation
        computation_result = self.computation.execute(question_text, evidence, query_context)
        if computation_result:
            self.logger.info(f"Stage 4 - Computation: {computation_result['computation_type']}")

        # Stage 5: Reasoning
        answer_text, confidence, reasoning_steps = self.reasoning.execute(
            question_text, evidence, computation_result
        )
        self.logger.info(f"Stage 5 - Generated answer with confidence: {confidence:.2f}")

        # Stage 6: Verification
        verification = self.verification.execute(answer_text, evidence, confidence)
        self.logger.info(f"Stage 6 - Verification complete: is_grounded={verification['is_grounded']}")

        # Compile final answer
        total_time = (time.time() - start_time) * 1000

        answer = Answer(
            answer_id=question_id,
            query=question_text,
            answer_text=answer_text,
            confidence_score=confidence,
            evidence=evidence,
            reasoning_steps=reasoning_steps,
            is_grounded=verification["is_grounded"],
            metadata={
                "question_type": query_context["question_type"],
                "total_time_ms": total_time,
                "verification": verification,
                "computation_result": computation_result,
            }
        )

        self.logger.info(f"Question answered in {total_time:.1f}ms")

        return answer
