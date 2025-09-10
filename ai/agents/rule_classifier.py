"""
Rule Classifier Agent

Responsible for classifying and categorizing extracted rules by risk level,
urgency, compliance type, and other organizational dimensions.
"""

from typing import Dict, Any, List
from .base import BaseAgent, AgentResult


class RuleClassifier(BaseAgent):
    """
    Classifies extracted compliance rules by various dimensions including
    risk level, urgency, compliance type, and organizational impact.
    """

    @property
    def agent_name(self) -> str:
        return "Rule Classifier"

    @property
    def description(self) -> str:
        return "Classifies rules by risk level, urgency, and organizational impact"

    async def process(
        self, input_data: List[Dict[str, Any]], context: Dict[str, Any] = None
    ) -> AgentResult:
        """
        Classify extracted compliance rules.

        Args:
            input_data: List of extracted rules from Rule Extractor
            context: Previous agent results for additional context

        Returns:
            AgentResult containing classified rules
        """
        self.log_progress("Starting rule classification...")

        try:
            extracted_rules = (
                input_data
                if isinstance(input_data, list)
                else input_data.get("extracted_rules", [])
            )

            if not extracted_rules:
                self.log_progress("No rules to classify", "warning")
                return AgentResult(
                    success=True,
                    data={"classified_rules": []},
                    metadata={"agent": self.agent_name},
                )

            self.log_progress(f"Classifying {len(extracted_rules)} rules...")

            classified_rules = []

            # Process rules in batches for efficiency
            batch_size = 5
            for i in range(0, len(extracted_rules), batch_size):
                batch = extracted_rules[i : i + batch_size]
                classified_batch = await self._classify_rule_batch(batch)
                classified_rules.extend(classified_batch)
                self.log_progress(
                    f"Classified batch {i//batch_size + 1}/{(len(extracted_rules) + batch_size - 1)//batch_size}"
                )

            # Generate classification summary
            classification_summary = self._generate_classification_summary(
                classified_rules
            )

            result_data = {
                "classified_rules": classified_rules,
                "classification_summary": classification_summary,
            }

            self.log_progress(
                f"Classification completed: {len(classified_rules)} rules classified"
            )

            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "agent": self.agent_name,
                    "rules_classified": len(classified_rules),
                },
            )

        except Exception as e:
            self.log_progress(f"Rule classification failed: {str(e)}", "error")
            return AgentResult(
                success=False,
                data=None,
                errors=[f"Rule classification failed: {str(e)}"],
            )

    async def _classify_rule_batch(
        self, rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Classify a batch of rules."""

        rules_text = ""
        for i, rule in enumerate(rules):
            rules_text += f"Rule {i+1}:\n"
            rules_text += f"Title: {rule.get('rule_title', 'No title')}\n"
            rules_text += (
                f"Description: {rule.get('rule_description', 'No description')}\n"
            )
            rules_text += f"Type: {rule.get('requirement_type', 'Unknown')}\n"
            rules_text += f"Obligations: {'; '.join(rule.get('key_obligations', []))}\n"
            rules_text += f"Penalties: {'; '.join(rule.get('penalties', []))}\n\n"

        prompt = f"""
        Classify these compliance rules across multiple dimensions. For each rule, provide comprehensive classification information.
        
        Classify each rule with the following structure:
        
        {{
            "classified_rules": [
                {{
                    "original_rule": {{
                        "rule_title": "original title",
                        "rule_description": "original description",
                        "compliance_theme": "original theme",
                        "requirement_type": "original type",
                        "target_entities": ["original entities"],
                        "key_obligations": ["original obligations"],
                        "deadlines": ["original deadlines"],
                        "penalties": ["original penalties"],
                        "exceptions": ["original exceptions"],
                        "documentation_required": ["original docs"],
                        "monitoring_required": true/false,
                        "source_section": "original section",
                        "legal_basis": "original basis"
                    }},
                    "classification": {{
                        "risk_level": "critical|high|medium|low",
                        "urgency": "immediate|high|medium|low",
                        "complexity": "high|medium|low",
                        "business_impact": "high|medium|low",
                        "implementation_difficulty": "hard|medium|easy",
                        "monitoring_frequency": "continuous|daily|weekly|monthly|quarterly|annual",
                        "organizational_scope": "enterprise-wide|departmental|role-specific",
                        "compliance_type": "regulatory|operational|governance|reporting|data|financial|safety|environmental",
                        "automation_potential": "high|medium|low|none",
                        "stakeholder_groups": ["legal", "it", "hr", "finance", "operations", "management"],
                        "geographic_scope": "global|regional|country-specific|local",
                        "industry_specificity": "general|industry-specific",
                        "violation_detection": {{
                            "detection_method": "automated|manual|hybrid",
                            "detection_indicators": ["indicator1", "indicator2"],
                            "red_flags": ["flag1", "flag2"]
                        }},
                        "implementation_priority": "p1|p2|p3|p4",
                        "estimated_effort": "low|medium|high|very-high"
                    }}
                }}
            ]
        }}
        
        Classification Guidelines:
        - Risk Level: Critical (severe legal/financial consequences), High (significant impact), Medium (moderate impact), Low (minimal impact)
        - Urgency: Immediate (implement now), High (within 30 days), Medium (within 90 days), Low (within 1 year)
        - Implementation Priority: P1 (critical), P2 (high), P3 (medium), P4 (low)
        
        Rules to classify:
        {rules_text}
        """

        system_instruction = """You are a compliance risk assessment expert. Classify rules comprehensively across all dimensions to help organizations prioritize implementation and monitoring. Consider legal consequences, business impact, and implementation complexity. Always respond with valid JSON."""

        response = await self._call_llm(prompt, system_instruction)
        parsed = self._parse_json_response(response)
        return parsed.get("classified_rules", [])

    def _generate_classification_summary(
        self, classified_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a summary of the classification results."""

        if not classified_rules:
            return {}

        # Count rules by various classification dimensions
        risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        urgency_counts = {"immediate": 0, "high": 0, "medium": 0, "low": 0}
        priority_counts = {"p1": 0, "p2": 0, "p3": 0, "p4": 0}
        compliance_types = {}

        for rule_data in classified_rules:
            classification = rule_data.get("classification", {})

            # Risk level counts
            risk_level = classification.get("risk_level", "").lower()
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1

            # Urgency counts
            urgency = classification.get("urgency", "").lower()
            if urgency in urgency_counts:
                urgency_counts[urgency] += 1

            # Priority counts
            priority = classification.get("implementation_priority", "").lower()
            if priority in priority_counts:
                priority_counts[priority] += 1

            # Compliance type counts
            comp_type = classification.get("compliance_type", "unknown")
            compliance_types[comp_type] = compliance_types.get(comp_type, 0) + 1

        return {
            "total_rules": len(classified_rules),
            "risk_distribution": risk_counts,
            "urgency_distribution": urgency_counts,
            "priority_distribution": priority_counts,
            "compliance_type_distribution": compliance_types,
            "high_priority_count": risk_counts["critical"] + risk_counts["high"],
            "immediate_action_count": urgency_counts["immediate"]
            + urgency_counts["high"],
        }
