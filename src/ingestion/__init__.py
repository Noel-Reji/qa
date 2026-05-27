"""Ingestion module."""
from .orchestrator import DocumentCorpus, OfficeQASystem, get_system, initialize_system

__all__ = ["DocumentCorpus", "OfficeQASystem", "get_system", "initialize_system"]
