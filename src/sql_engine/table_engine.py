"""SQL engine for table reasoning and numerical computations."""

import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import json

from src.utils import generate_id, Timer
from src.config import settings
from src.logging import get_logger

logger = get_logger("sql_engine")


class SQLQueryExecutor:
    """Executes SQL queries on table data."""

    def __init__(self, engine_type: str = "duckdb"):
        self.engine_type = engine_type
        self.tables: Dict[str, pd.DataFrame] = {}
        self.connection = None
        self._init_engine()

    def _init_engine(self):
        """Initialize SQL engine."""
        if self.engine_type == "duckdb":
            try:
                import duckdb
                self.connection = duckdb.connect(settings.sql.db_path)
                logger.info("Initialized DuckDB engine")
            except ImportError:
                logger.error("duckdb not installed")
        elif self.engine_type == "sqlite":
            import sqlite3
            self.connection = sqlite3.connect(settings.sql.db_path)
            logger.info("Initialized SQLite engine")

    def load_table(self, table_name: str, data: pd.DataFrame) -> None:
        """Load a table into the engine."""
        self.tables[table_name] = data

        if self.connection:
            if self.engine_type == "duckdb":
                self.connection.register(table_name, data)
            elif self.engine_type == "sqlite":
                data.to_sql(table_name, self.connection, if_exists='replace', index=False)

        logger.info(f"Loaded table: {table_name} ({len(data)} rows, {len(data.columns)} cols)")

    def execute_query(self, query: str, timeout: Optional[float] = None) -> Optional[pd.DataFrame]:
        """Execute a SQL query."""
        try:
            if not self.connection:
                logger.error("Database connection not initialized")
                return None

            with Timer() as timer:
                if self.engine_type == "duckdb":
                    result = self.connection.execute(query).fetchdf()
                elif self.engine_type == "sqlite":
                    result = pd.read_sql(query, self.connection)
                else:
                    result = None

            if result is not None:
                logger.info(f"Query executed in {timer.elapsed_ms:.1f}ms, returned {len(result)} rows")
                if settings.sql.enable_query_logging:
                    logger.info(f"SQL: {query[:200]}...")

            return result

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return None

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()


class TableReasoningEngine:
    """Engine for reasoning over tables."""

    def __init__(self):
        self.executor = SQLQueryExecutor(engine_type=settings.sql.engine_type)
        self.extracted_tables: Dict[str, pd.DataFrame] = {}

    def extract_table_from_text(self, text: str) -> Optional[pd.DataFrame]:
        """Extract table from markdown or text format."""
        try:
            # Try parsing as CSV/TSV
            lines = text.strip().split('\n')
            if len(lines) < 2:
                return None

            # Try to parse lines as table
            data = []
            for line in lines:
                # Split by multiple spaces or pipes
                if '|' in line:
                    row = [cell.strip() for cell in line.split('|')]
                else:
                    row = line.split()

                if row:
                    data.append(row)

            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                logger.info(f"Extracted table: {df.shape[0]} rows, {df.shape[1]} columns")
                return df

            return None

        except Exception as e:
            logger.debug(f"Failed to extract table: {e}")
            return None

    def infer_question_type(self, question: str) -> str:
        """Infer if question requires table reasoning."""
        keywords = [
            "sum", "total", "average", "mean", "count", "max", "min",
            "calculate", "compute", "how many", "what is the",
            "percentage", "ratio", "compare", "between",
            "group", "sorted", "order"
        ]

        question_lower = question.lower()
        for keyword in keywords:
            if keyword in question_lower:
                return "numerical"

        return "text"

    def generate_sql_from_question(self, question: str, table_name: str) -> Optional[str]:
        """Generate SQL query from natural language question."""
        # This is a simplified version - in production, use more sophisticated NL-to-SQL
        question_lower = question.lower()

        queries = {
            "sum": f"SELECT SUM(*) FROM {table_name}",
            "count": f"SELECT COUNT(*) FROM {table_name}",
            "average": f"SELECT AVG(*) FROM {table_name}",
            "max": f"SELECT MAX(*) FROM {table_name}",
            "min": f"SELECT MIN(*) FROM {table_name}",
        }

        for keyword, query_template in queries.items():
            if keyword in question_lower:
                logger.info(f"Generated SQL for '{keyword}': {query_template}")
                return query_template

        return None

    def reason_over_table(
        self,
        question: str,
        table_data: pd.DataFrame,
        table_name: str = "data"
    ) -> Dict[str, Any]:
        """Reason over a table to answer a question."""
        result = {
            "question": question,
            "table_name": table_name,
            "answer": None,
            "reasoning": [],
            "computation": None,
            "error": None,
        }

        try:
            # Load table
            self.executor.load_table(table_name, table_data)

            # Infer question type
            question_type = self.infer_question_type(question)
            result["reasoning"].append(f"Question type: {question_type}")

            # Try to generate and execute SQL
            sql_query = self.generate_sql_from_question(question, table_name)

            if sql_query:
                result["computation"] = sql_query
                query_result = self.executor.execute_query(sql_query)

                if query_result is not None:
                    result["answer"] = query_result.to_dict()
                    result["reasoning"].append(f"Executed SQL query: {sql_query}")
                else:
                    result["error"] = "SQL execution failed"
            else:
                # Fallback to pandas operations
                answer = self._fallback_pandas_reasoning(question, table_data)
                result["answer"] = answer
                result["reasoning"].append("Used fallback pandas reasoning")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Table reasoning failed: {e}")

        return result

    def _fallback_pandas_reasoning(self, question: str, df: pd.DataFrame) -> Any:
        """Fallback to pandas for basic operations."""
        question_lower = question.lower()

        try:
            if "sum" in question_lower:
                return float(df.sum().sum())
            elif "count" in question_lower:
                return len(df)
            elif "average" in question_lower or "mean" in question_lower:
                return float(df.mean().mean())
            elif "max" in question_lower:
                return float(df.max().max())
            elif "min" in question_lower:
                return float(df.min().min())
        except Exception as e:
            logger.debug(f"Pandas fallback failed: {e}")

        return None


class ComputationEngine:
    """Engine for numerical computations."""

    @staticmethod
    def safe_eval(expression: str, context: Dict[str, Any] = None) -> Optional[float]:
        """Safely evaluate mathematical expression."""
        if context is None:
            context = {}

        try:
            # Only allow safe operations
            allowed_names = {"__builtins__": {}, **context}
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return float(result)
        except Exception as e:
            logger.debug(f"Expression evaluation failed: {e}")
            return None

    @staticmethod
    def extract_and_compute(text: str) -> Optional[Dict[str, Any]]:
        """Extract numbers and perform basic computations."""
        from src.utils import extract_numbers

        numbers = extract_numbers(text)
        if not numbers:
            return None

        result = {
            "numbers": numbers,
            "sum": sum(numbers),
            "count": len(numbers),
            "avg": sum(numbers) / len(numbers) if numbers else 0,
            "max": max(numbers) if numbers else None,
            "min": min(numbers) if numbers else None,
        }

        return result
