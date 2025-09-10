"""
Multi-Agent Rule Generation System

This module implements a sophisticated multi-agent approach for generating
compliance rules from regulatory documents, replacing the simple 0-shot prompt
with a pipeline of specialized AI agents.
"""

from .base import BaseAgent
from .document_analyzer import DocumentAnalyzer
from .rule_extractor import RuleExtractor
from .rule_classifier import RuleClassifier
from .rule_validator import RuleValidator
from .rule_synthesizer import RuleSynthesizer
from .orchestrator import RuleGenerationOrchestrator

__all__ = [
    "BaseAgent",
    "DocumentAnalyzer",
    "RuleExtractor",
    "RuleClassifier",
    "RuleValidator",
    "RuleSynthesizer",
    "RuleGenerationOrchestrator",
]
