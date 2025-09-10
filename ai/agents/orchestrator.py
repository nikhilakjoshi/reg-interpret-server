"""
Rule Generation Orchestrator

Coordinates the multi-agent pipeline for generating compliance rules from
regulatory documents with streaming progress updates.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, AsyncGenerator
from .base import BaseAgent, AgentResult
from .document_analyzer import DocumentAnalyzer
from .rule_extractor import RuleExtractor
from .rule_classifier import RuleClassifier
from .rule_validator import RuleValidator
from .rule_synthesizer import RuleSynthesizer

logger = logging.getLogger(__name__)


class RuleGenerationOrchestrator:
    """
    Orchestrates the multi-agent rule generation pipeline with streaming progress updates.

    Pipeline stages:
    1. Document Analysis - Understand document structure and themes
    2. Rule Extraction - Extract specific compliance requirements
    3. Rule Classification - Classify rules by risk, urgency, etc.
    4. Rule Validation - Validate accuracy and completeness
    5. Rule Synthesis - Create final actionable rules
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the orchestrator with all agents.

        Args:
            model_name: Google Gemini model to use for all agents
        """
        self.model_name = model_name
        self.agents = {
            "document_analyzer": DocumentAnalyzer(model_name),
            "rule_extractor": RuleExtractor(model_name),
            "rule_classifier": RuleClassifier(model_name),
            "rule_validator": RuleValidator(model_name),
            "rule_synthesizer": RuleSynthesizer(model_name),
        }
        self.logger = logging.getLogger(__name__)

    async def generate_rules_stream(
        self, document_text: str, policy_space_id: int
    ) -> AsyncGenerator[str, None]:
        """
        Generate compliance rules from a document with streaming progress updates.

        Args:
            document_text: The full text of the regulatory document
            policy_space_id: ID of the policy space for context

        Yields:
            JSON-formatted progress updates and final results
        """

        self.logger.info(
            f"Starting multi-agent rule generation for policy space {policy_space_id}"
        )

        try:
            # Initialize pipeline context
            context = {
                "policy_space_id": policy_space_id,
                "pipeline_status": "starting",
                "total_stages": 5,
                "current_stage": 0,
            }

            # Send initial status
            yield self._format_progress_message(
                "pipeline_started",
                {
                    "message": "Starting multi-agent rule generation pipeline",
                    "total_stages": 5,
                    "agents": list(self.agents.keys()),
                },
            )

            # Stage 1: Document Analysis
            yield self._format_progress_message(
                "stage_started",
                {
                    "stage": 1,
                    "stage_name": "document_analysis",
                    "agent": "Document Analyzer",
                    "message": "Analyzing document structure and compliance themes...",
                },
            )

            doc_analysis_result = await self.agents["document_analyzer"].process(
                document_text
            )

            if not doc_analysis_result.success:
                yield self._format_error_message(
                    "Document analysis failed", doc_analysis_result.errors
                )
                return

            context["document_analysis"] = doc_analysis_result.data

            yield self._format_progress_message(
                "stage_completed",
                {
                    "stage": 1,
                    "stage_name": "document_analysis",
                    "result_summary": {
                        "themes_identified": len(
                            doc_analysis_result.data.get("compliance_themes", [])
                        ),
                        "document_sections": doc_analysis_result.data.get(
                            "document_stats", {}
                        ).get("section_count", 0),
                        "document_type": doc_analysis_result.data.get(
                            "structure_analysis", {}
                        ).get("document_type", "unknown"),
                    },
                },
            )

            # Stage 2: Rule Extraction
            yield self._format_progress_message(
                "stage_started",
                {
                    "stage": 2,
                    "stage_name": "rule_extraction",
                    "agent": "Rule Extractor",
                    "message": "Extracting specific compliance rules and requirements...",
                },
            )

            rule_extraction_result = await self.agents["rule_extractor"].process(
                document_text, context
            )

            if not rule_extraction_result.success:
                yield self._format_error_message(
                    "Rule extraction failed", rule_extraction_result.errors
                )
                return

            context["rule_extraction"] = rule_extraction_result.data
            extracted_rules = rule_extraction_result.data.get("extracted_rules", [])

            yield self._format_progress_message(
                "stage_completed",
                {
                    "stage": 2,
                    "stage_name": "rule_extraction",
                    "result_summary": {
                        "rules_extracted": len(extracted_rules),
                        "themes_processed": rule_extraction_result.data.get(
                            "extraction_summary", {}
                        ).get("themes_processed", 0),
                    },
                },
            )

            # Stage 3: Rule Classification
            yield self._format_progress_message(
                "stage_started",
                {
                    "stage": 3,
                    "stage_name": "rule_classification",
                    "agent": "Rule Classifier",
                    "message": "Classifying rules by risk level, urgency, and implementation priority...",
                },
            )

            rule_classification_result = await self.agents["rule_classifier"].process(
                extracted_rules, context
            )

            if not rule_classification_result.success:
                yield self._format_error_message(
                    "Rule classification failed", rule_classification_result.errors
                )
                return

            context["rule_classification"] = rule_classification_result.data
            classified_rules = rule_classification_result.data.get(
                "classified_rules", []
            )
            classification_summary = rule_classification_result.data.get(
                "classification_summary", {}
            )

            yield self._format_progress_message(
                "stage_completed",
                {
                    "stage": 3,
                    "stage_name": "rule_classification",
                    "result_summary": {
                        "rules_classified": len(classified_rules),
                        "high_priority_rules": classification_summary.get(
                            "high_priority_count", 0
                        ),
                        "critical_risk_rules": classification_summary.get(
                            "risk_distribution", {}
                        ).get("critical", 0),
                    },
                },
            )

            # Stage 4: Rule Validation
            yield self._format_progress_message(
                "stage_started",
                {
                    "stage": 4,
                    "stage_name": "rule_validation",
                    "agent": "Rule Validator",
                    "message": "Validating rules for accuracy, completeness, and actionability...",
                },
            )

            rule_validation_result = await self.agents["rule_validator"].process(
                classified_rules, context
            )

            if not rule_validation_result.success:
                yield self._format_error_message(
                    "Rule validation failed", rule_validation_result.errors
                )
                return

            context["rule_validation"] = rule_validation_result.data
            validated_rules = rule_validation_result.data.get("validated_rules", [])
            validation_report = rule_validation_result.data.get("validation_report", {})

            yield self._format_progress_message(
                "stage_completed",
                {
                    "stage": 4,
                    "stage_name": "rule_validation",
                    "result_summary": {
                        "rules_validated": len(validated_rules),
                        "validation_success_rate": validation_report.get(
                            "validation_summary", {}
                        ).get("validation_success_rate", 0),
                        "quality_score": validation_report.get("quality_score", 0),
                    },
                },
            )

            # Stage 5: Rule Synthesis
            yield self._format_progress_message(
                "stage_started",
                {
                    "stage": 5,
                    "stage_name": "rule_synthesis",
                    "agent": "Rule Synthesizer",
                    "message": "Synthesizing final actionable compliance rules...",
                },
            )

            rule_synthesis_result = await self.agents["rule_synthesizer"].process(
                validated_rules, context
            )

            if not rule_synthesis_result.success:
                yield self._format_error_message(
                    "Rule synthesis failed", rule_synthesis_result.errors
                )
                return

            context["rule_synthesis"] = rule_synthesis_result.data
            final_rules = rule_synthesis_result.data.get("final_rules", [])
            synthesis_summary = rule_synthesis_result.data.get("synthesis_summary", {})

            yield self._format_progress_message(
                "stage_completed",
                {
                    "stage": 5,
                    "stage_name": "rule_synthesis",
                    "result_summary": {
                        "final_rules_generated": len(final_rules),
                        "completeness_score": synthesis_summary.get(
                            "synthesis_overview", {}
                        ).get("average_rule_completeness", 0),
                        "implementation_phases": synthesis_summary.get(
                            "implementation_overview", {}
                        ).get("estimated_implementation_phases", {}),
                    },
                },
            )

            # Generate final pipeline summary
            pipeline_summary = self._generate_pipeline_summary(context)

            # Send final results
            yield self._format_progress_message(
                "pipeline_completed",
                {
                    "message": "Multi-agent rule generation completed successfully",
                    "pipeline_summary": pipeline_summary,
                    "final_rules": final_rules,
                    "total_rules_generated": len(final_rules),
                },
            )

            self.logger.info(
                f"Pipeline completed successfully: {len(final_rules)} rules generated"
            )

        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            yield self._format_error_message("Pipeline execution failed", [str(e)])

    def _format_progress_message(self, message_type: str, data: Dict[str, Any]) -> str:
        """Format a progress message as JSON."""
        message = {
            "type": message_type,
            "timestamp": "timestamp_here",  # TODO: Add actual timestamp
            "data": data,
        }
        return json.dumps(message) + "\n"

    def _format_error_message(self, error_message: str, errors: List[str]) -> str:
        """Format an error message as JSON."""
        message = {
            "type": "error",
            "timestamp": "timestamp_here",  # TODO: Add actual timestamp
            "error": error_message,
            "details": errors,
        }
        return json.dumps(message) + "\n"

    def _generate_pipeline_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive summary of the entire pipeline execution."""

        summary = {
            "execution_overview": {
                "total_stages_completed": 5,
                "pipeline_success": True,
                "processing_time": "timing_here",  # TODO: Add actual timing
            }
        }

        # Document analysis summary
        if "document_analysis" in context:
            doc_data = context["document_analysis"]
            summary["document_analysis"] = {
                "document_stats": doc_data.get("document_stats", {}),
                "themes_identified": len(doc_data.get("compliance_themes", [])),
                "document_type": doc_data.get("structure_analysis", {}).get(
                    "document_type", "unknown"
                ),
            }

        # Rule extraction summary
        if "rule_extraction" in context:
            extract_data = context["rule_extraction"]
            summary["rule_extraction"] = extract_data.get("extraction_summary", {})

        # Classification summary
        if "rule_classification" in context:
            class_data = context["rule_classification"]
            summary["rule_classification"] = class_data.get(
                "classification_summary", {}
            )

        # Validation summary
        if "rule_validation" in context:
            valid_data = context["rule_validation"]
            summary["rule_validation"] = valid_data.get("validation_report", {})

        # Synthesis summary
        if "rule_synthesis" in context:
            synth_data = context["rule_synthesis"]
            summary["rule_synthesis"] = synth_data.get("synthesis_summary", {})

        return summary
