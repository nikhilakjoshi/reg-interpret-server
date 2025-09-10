"""
Rule Extractor Agent

Responsible for extracting specific compliance rules and requirements
from regulatory documents based on the document analysis.
"""

from typing import Dict, Any, List
from .base import BaseAgent, AgentResult


class RuleExtractor(BaseAgent):
    """
    Extracts specific compliance rules and requirements from regulatory text
    based on the structure and themes identified by the Document Analyzer.
    """

    @property
    def agent_name(self) -> str:
        return "Rule Extractor"

    @property
    def description(self) -> str:
        return (
            "Extracts specific compliance rules and requirements from regulatory text"
        )

    async def process(
        self, input_data: str, context: Dict[str, Any] = None
    ) -> AgentResult:
        """
        Extract compliance rules from the document.

        Args:
            input_data: The full text of the regulatory document
            context: Document analysis results from previous agent

        Returns:
            AgentResult containing extracted rules
        """
        self.log_progress("Starting rule extraction...")

        try:
            # Get document analysis context
            doc_analysis = context.get("document_analysis", {}) if context else {}
            themes = doc_analysis.get("compliance_themes", [])
            structure = doc_analysis.get("structure_analysis", {})

            self.log_progress(f"Extracting rules for {len(themes)} compliance themes")

            # Extract rules for each compliance theme
            extracted_rules = []

            for theme in themes:
                theme_rules = await self._extract_theme_rules(
                    input_data, theme, structure
                )
                extracted_rules.extend(theme_rules)
                self.log_progress(
                    f"Extracted {len(theme_rules)} rules for theme: {theme.get('theme', 'Unknown')}"
                )

            # Extract general compliance requirements
            general_rules = await self._extract_general_requirements(
                input_data, structure
            )
            extracted_rules.extend(general_rules)

            self.log_progress(f"Total rules extracted: {len(extracted_rules)}")

            result_data = {
                "extracted_rules": extracted_rules,
                "extraction_summary": {
                    "total_rules": len(extracted_rules),
                    "themes_processed": len(themes),
                    "general_requirements": len(general_rules),
                },
            }

            self.log_progress("Rule extraction completed successfully")

            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "agent": self.agent_name,
                    "rules_extracted": len(extracted_rules),
                },
            )

        except Exception as e:
            self.log_progress(f"Rule extraction failed: {str(e)}", "error")
            return AgentResult(
                success=False, data=None, errors=[f"Rule extraction failed: {str(e)}"]
            )

    async def _extract_theme_rules(
        self, text: str, theme: Dict[str, Any], structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract rules specific to a compliance theme."""

        theme_name = theme.get("theme", "Unknown")
        keywords = theme.get("keywords", [])

        prompt = f"""
        Extract specific compliance rules related to the theme "{theme_name}" from this regulatory document.
        
        Theme description: {theme.get("description", "")}
        Key terms to look for: {", ".join(keywords)}
        
        For each rule you find, provide a JSON response with this structure:
        
        {{
            "rules": [
                {{
                    "rule_title": "descriptive title for the rule",
                    "rule_description": "detailed description of what must be done",
                    "compliance_theme": "{theme_name}",
                    "requirement_type": "mandatory|recommended|prohibited",
                    "target_entities": ["who this applies to"],
                    "key_obligations": ["specific obligation 1", "specific obligation 2"],
                    "deadlines": ["any time requirements or deadlines"],
                    "penalties": ["consequences for non-compliance"],
                    "exceptions": ["any exceptions or exemptions"],
                    "documentation_required": ["what documentation is needed"],
                    "monitoring_required": true/false,
                    "source_section": "which section of the regulation this comes from",
                    "legal_basis": "the specific legal authority or requirement"
                }}
            ]
        }}
        
        Focus only on actionable compliance requirements. Ignore general principles or background information.
        
        Document text:
        {text[:6000]}...
        """

        system_instruction = f"""You are a compliance expert specializing in {theme_name}. Extract only specific, actionable compliance rules that organizations must follow. Each rule should be concrete and measurable. Always respond with valid JSON."""

        response = await self._call_llm(prompt, system_instruction)
        parsed = self._parse_json_response(response)
        return parsed.get("rules", [])

    async def _extract_general_requirements(
        self, text: str, structure: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract general compliance requirements that don't fit specific themes."""

        prompt = f"""
        Extract general compliance requirements from this regulatory document that apply broadly across the organization.
        
        Look for:
        - Record keeping requirements
        - Reporting obligations
        - Notification requirements
        - Training requirements
        - Audit requirements
        - Governance requirements
        
        Provide a JSON response with this structure:
        
        {{
            "rules": [
                {{
                    "rule_title": "descriptive title for the rule",
                    "rule_description": "detailed description of what must be done",
                    "compliance_theme": "general",
                    "requirement_type": "mandatory|recommended|prohibited",
                    "target_entities": ["who this applies to"],
                    "key_obligations": ["specific obligation 1", "specific obligation 2"],
                    "deadlines": ["any time requirements or deadlines"],
                    "penalties": ["consequences for non-compliance"],
                    "exceptions": ["any exceptions or exemptions"],
                    "documentation_required": ["what documentation is needed"],
                    "monitoring_required": true/false,
                    "source_section": "which section of the regulation this comes from",
                    "legal_basis": "the specific legal authority or requirement"
                }}
            ]
        }}
        
        Document text:
        {text[:6000]}...
        """

        system_instruction = """You are a regulatory compliance expert. Extract general compliance requirements that organizations must implement across their operations. Focus on operational requirements like reporting, record-keeping, and governance. Always respond with valid JSON."""

        response = await self._call_llm(prompt, system_instruction)
        parsed = self._parse_json_response(response)
        return parsed.get("rules", [])
