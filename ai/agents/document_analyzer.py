"""
Document Analyzer Agent

Responsible for analyzing regulatory documents to understand their structure,
key sections, and overall compliance focus areas.
"""

import re
from typing import Dict, Any, List
from .base import BaseAgent, AgentResult


class DocumentAnalyzer(BaseAgent):
    """
    Analyzes regulatory documents to extract structural information,
    key sections, and identify compliance focus areas.
    """

    @property
    def agent_name(self) -> str:
        return "Document Analyzer"

    @property
    def description(self) -> str:
        return "Analyzes document structure and identifies key compliance sections"

    async def process(
        self, input_data: str, context: Dict[str, Any] = None
    ) -> AgentResult:
        """
        Analyze a regulatory document.

        Args:
            input_data: The full text of the regulatory document
            context: Additional context (not used for first agent)

        Returns:
            AgentResult containing document analysis
        """
        self.log_progress("Starting document analysis...")

        try:
            # Basic document statistics
            doc_stats = self._calculate_document_stats(input_data)
            self.log_progress(
                f"Document contains {doc_stats['word_count']} words in {doc_stats['section_count']} sections"
            )

            # Extract key sections using LLM
            analysis = await self._analyze_document_structure(input_data)

            # Identify compliance themes
            themes = await self._identify_compliance_themes(input_data)

            result_data = {
                "document_stats": doc_stats,
                "structure_analysis": analysis,
                "compliance_themes": themes,
                "processed_text": input_data,
            }

            self.log_progress("Document analysis completed successfully")

            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "agent": self.agent_name,
                    "processing_time": "analysis_time_here",  # TODO: Add timing
                },
            )

        except Exception as e:
            self.log_progress(f"Document analysis failed: {str(e)}", "error")
            return AgentResult(
                success=False, data=None, errors=[f"Document analysis failed: {str(e)}"]
            )

    def _calculate_document_stats(self, text: str) -> Dict[str, Any]:
        """Calculate basic statistics about the document."""

        # Word count
        words = re.findall(r"\b\w+\b", text)
        word_count = len(words)

        # Estimate sections (look for numbered sections, headers, etc.)
        section_patterns = [
            r"^\d+\.",  # 1. Section
            r"^Section \d+",  # Section 1
            r"^Article \d+",  # Article 1
            r"^Part [IVX]+",  # Part I, Part II, etc.
            r"^[A-Z][A-Z\s]{10,}$",  # ALL CAPS HEADERS
        ]

        section_count = 0
        for line in text.split("\n"):
            line = line.strip()
            for pattern in section_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    section_count += 1
                    break

        return {
            "word_count": word_count,
            "section_count": max(section_count, 1),  # At least 1 section
            "character_count": len(text),
            "line_count": len(text.split("\n")),
        }

    async def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """Use LLM to analyze document structure."""

        prompt = f"""
        Analyze the structure of this regulatory document and provide a JSON response with the following structure:

        {{
            "document_type": "regulation|policy|guideline|standard|other",
            "main_sections": [
                {{
                    "title": "section title",
                    "summary": "brief summary of section content",
                    "compliance_relevance": "high|medium|low"
                }}
            ],
            "key_definitions": [
                {{
                    "term": "defined term",
                    "definition": "definition text"
                }}
            ],
            "regulatory_authority": "name of issuing authority",
            "effective_date": "date if mentioned",
            "scope": "what entities/activities this applies to"
        }}

        Document text:
        {text[:4000]}...
        """

        system_instruction = """You are an expert regulatory analyst. Analyze documents to identify their structure, key sections, and compliance relevance. Always respond with valid JSON."""

        response = await self._call_llm(prompt, system_instruction)
        return self._parse_json_response(response)

    async def _identify_compliance_themes(self, text: str) -> List[Dict[str, Any]]:
        """Identify major compliance themes in the document."""

        prompt = f"""
        Identify the major compliance themes in this regulatory document. Provide a JSON response with this structure:

        {{
            "themes": [
                {{
                    "theme": "theme name (e.g., data protection, financial reporting, safety)",
                    "description": "description of this compliance area",
                    "importance": "high|medium|low",
                    "keywords": ["keyword1", "keyword2", "keyword3"],
                    "typical_violations": ["common violation type 1", "common violation type 2"]
                }}
            ]
        }}

        Focus on themes that would require specific compliance rules or monitoring.

        Document text:
        {text[:4000]}...
        """

        system_instruction = """You are a compliance expert. Identify themes that organizations need to monitor and create rules for. Always respond with valid JSON."""

        response = await self._call_llm(prompt, system_instruction)
        parsed = self._parse_json_response(response)
        return parsed.get("themes", [])
