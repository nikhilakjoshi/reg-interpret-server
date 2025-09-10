"""
Rule Validator Agent

Responsible for validating extracted and classified rules for accuracy,
completeness, and actionability before final synthesis.
"""

from typing import Dict, Any, List
from .base import BaseAgent, AgentResult


class RuleValidator(BaseAgent):
    """
    Validates extracted and classified compliance rules to ensure they are
    accurate, complete, actionable, and properly formatted.
    """

    @property
    def agent_name(self) -> str:
        return "Rule Validator"

    @property
    def description(self) -> str:
        return "Validates rules for accuracy, completeness, and actionability"

    async def process(
        self, input_data: List[Dict[str, Any]], context: Dict[str, Any] = None
    ) -> AgentResult:
        """
        Validate classified compliance rules.

        Args:
            input_data: List of classified rules from Rule Classifier
            context: Previous agent results for additional context

        Returns:
            AgentResult containing validated rules and validation report
        """
        self.log_progress("Starting rule validation...")

        try:
            classified_rules = (
                input_data
                if isinstance(input_data, list)
                else input_data.get("classified_rules", [])
            )

            if not classified_rules:
                self.log_progress("No rules to validate", "warning")
                return AgentResult(
                    success=True,
                    data={"validated_rules": [], "validation_report": {}},
                    metadata={"agent": self.agent_name},
                )

            self.log_progress(f"Validating {len(classified_rules)} rules...")

            validated_rules = []
            validation_issues = []

            # Validate each rule
            for i, rule_data in enumerate(classified_rules):
                validation_result = await self._validate_rule(rule_data, i + 1)

                if validation_result["is_valid"]:
                    validated_rules.append(validation_result["rule"])
                else:
                    validation_issues.extend(validation_result["issues"])

                if (i + 1) % 10 == 0:
                    self.log_progress(
                        f"Validated {i + 1}/{len(classified_rules)} rules"
                    )

            # Perform cross-rule validation
            cross_validation_issues = await self._perform_cross_validation(
                validated_rules
            )
            validation_issues.extend(cross_validation_issues)

            # Generate validation report
            validation_report = self._generate_validation_report(
                len(classified_rules), len(validated_rules), validation_issues
            )

            result_data = {
                "validated_rules": validated_rules,
                "validation_report": validation_report,
                "validation_issues": validation_issues,
            }

            self.log_progress(
                f"Validation completed: {len(validated_rules)}/{len(classified_rules)} rules passed validation"
            )

            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "agent": self.agent_name,
                    "rules_validated": len(validated_rules),
                    "validation_issues": len(validation_issues),
                },
            )

        except Exception as e:
            self.log_progress(f"Rule validation failed: {str(e)}", "error")
            return AgentResult(
                success=False, data=None, errors=[f"Rule validation failed: {str(e)}"]
            )

    async def _validate_rule(
        self, rule_data: Dict[str, Any], rule_number: int
    ) -> Dict[str, Any]:
        """Validate a single rule for accuracy and completeness."""

        original_rule = rule_data.get("original_rule", {})
        classification = rule_data.get("classification", {})

        # Basic structure validation
        structure_issues = self._validate_rule_structure(original_rule, rule_number)

        # Classification validation
        classification_issues = self._validate_classification(
            classification, rule_number
        )

        # Content validation using LLM
        content_validation = await self._validate_rule_content(
            original_rule, classification, rule_number
        )

        all_issues = (
            structure_issues
            + classification_issues
            + content_validation.get("issues", [])
        )

        # Apply any corrections suggested by the LLM
        corrected_rule = content_validation.get("corrected_rule")
        if corrected_rule:
            # Merge corrections with original rule
            enhanced_rule = {**original_rule, **corrected_rule}
        else:
            enhanced_rule = original_rule

        # Determine if rule is valid (no critical issues)
        critical_issues = [
            issue for issue in all_issues if issue.get("severity") == "critical"
        ]
        is_valid = len(critical_issues) == 0

        return {
            "is_valid": is_valid,
            "rule": {
                "original_rule": enhanced_rule,
                "classification": classification,
                "validation_status": "passed" if is_valid else "failed",
                "validation_issues": all_issues,
            },
            "issues": all_issues,
        }

    def _validate_rule_structure(
        self, rule: Dict[str, Any], rule_number: int
    ) -> List[Dict[str, Any]]:
        """Validate the basic structure of a rule."""

        issues = []
        required_fields = [
            "rule_title",
            "rule_description",
            "requirement_type",
            "key_obligations",
            "target_entities",
        ]

        for field in required_fields:
            if not rule.get(field):
                issues.append(
                    {
                        "type": "missing_field",
                        "severity": "critical",
                        "rule_number": rule_number,
                        "field": field,
                        "message": f"Required field '{field}' is missing or empty",
                    }
                )

        # Validate field content quality
        if rule.get("rule_title") and len(rule["rule_title"]) < 10:
            issues.append(
                {
                    "type": "content_quality",
                    "severity": "warning",
                    "rule_number": rule_number,
                    "field": "rule_title",
                    "message": "Rule title is too short (less than 10 characters)",
                }
            )

        if rule.get("rule_description") and len(rule["rule_description"]) < 50:
            issues.append(
                {
                    "type": "content_quality",
                    "severity": "warning",
                    "rule_number": rule_number,
                    "field": "rule_description",
                    "message": "Rule description is too brief (less than 50 characters)",
                }
            )

        return issues

    def _validate_classification(
        self, classification: Dict[str, Any], rule_number: int
    ) -> List[Dict[str, Any]]:
        """Validate the classification of a rule."""

        issues = []
        required_fields = [
            "risk_level",
            "urgency",
            "complexity",
            "implementation_priority",
        ]

        valid_values = {
            "risk_level": ["critical", "high", "medium", "low"],
            "urgency": ["immediate", "high", "medium", "low"],
            "complexity": ["high", "medium", "low"],
            "implementation_priority": ["p1", "p2", "p3", "p4"],
        }

        for field in required_fields:
            value = classification.get(field, "").lower()
            if not value:
                issues.append(
                    {
                        "type": "missing_classification",
                        "severity": "critical",
                        "rule_number": rule_number,
                        "field": field,
                        "message": f"Classification field '{field}' is missing",
                    }
                )
            elif value not in valid_values[field]:
                issues.append(
                    {
                        "type": "invalid_classification",
                        "severity": "critical",
                        "rule_number": rule_number,
                        "field": field,
                        "message": f"Invalid value '{value}' for {field}. Valid values: {valid_values[field]}",
                    }
                )

        return issues

    async def _validate_rule_content(
        self, rule: Dict[str, Any], classification: Dict[str, Any], rule_number: int
    ) -> Dict[str, Any]:
        """Use LLM to validate rule content for accuracy and actionability."""

        prompt = f"""
        Validate this compliance rule for accuracy, completeness, and actionability. Identify any issues and suggest improvements.
        
        Rule to validate:
        Title: {rule.get('rule_title', 'N/A')}
        Description: {rule.get('rule_description', 'N/A')}
        Type: {rule.get('requirement_type', 'N/A')}
        Obligations: {'; '.join(rule.get('key_obligations', []))}
        Target Entities: {'; '.join(rule.get('target_entities', []))}
        Penalties: {'; '.join(rule.get('penalties', []))}
        Documentation Required: {'; '.join(rule.get('documentation_required', []))}
        
        Classification:
        Risk Level: {classification.get('risk_level', 'N/A')}
        Urgency: {classification.get('urgency', 'N/A')}
        Complexity: {classification.get('complexity', 'N/A')}
        
        Provide validation results in this JSON format:
        
        {{
            "validation_result": "pass|fail",
            "issues": [
                {{
                    "type": "accuracy|completeness|actionability|clarity|classification_mismatch",
                    "severity": "critical|warning|info",
                    "field": "field_name",
                    "message": "description of the issue",
                    "suggestion": "suggested improvement"
                }}
            ],
            "corrected_rule": {{
                "rule_title": "improved title if needed",
                "rule_description": "improved description if needed",
                "key_obligations": ["improved obligations if needed"],
                "detection_criteria": ["specific criteria for detecting violations"],
                "red_flags": ["warning signs of potential violations"]
            }},
            "actionability_score": 1-10,
            "clarity_score": 1-10
        }}
        
        Focus on:
        1. Is the rule specific and measurable?
        2. Can an organization actually implement this?
        3. Are the obligations clear and actionable?
        4. Does the classification match the rule content?
        5. Are there missing elements that would make this more actionable?
        """

        system_instruction = """You are a compliance validation expert. Validate rules for practical implementation in organizations. Ensure rules are specific, measurable, and actionable. Always respond with valid JSON."""

        response = await self._call_llm(prompt, system_instruction)
        return self._parse_json_response(response)

    async def _perform_cross_validation(
        self, validated_rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Perform validation across multiple rules to identify conflicts or gaps."""

        if len(validated_rules) < 2:
            return []

        # Sample a subset for cross-validation if there are too many rules
        sample_size = min(len(validated_rules), 20)
        sample_rules = validated_rules[:sample_size]

        rules_summary = ""
        for i, rule_data in enumerate(sample_rules):
            rule = rule_data.get("original_rule", {})
            rules_summary += f"Rule {i+1}: {rule.get('rule_title', 'No title')} - {rule.get('compliance_theme', 'No theme')}\n"

        prompt = f"""
        Analyze these compliance rules for potential conflicts, overlaps, or gaps. Identify any issues that could cause problems during implementation.
        
        Rules to analyze:
        {rules_summary}
        
        Provide analysis in this JSON format:
        
        {{
            "cross_validation_issues": [
                {{
                    "type": "conflict|overlap|gap|inconsistency",
                    "severity": "critical|warning|info",
                    "affected_rules": [1, 2],
                    "message": "description of the issue",
                    "recommendation": "suggested resolution"
                }}
            ],
            "overall_coherence": "high|medium|low",
            "recommendations": ["general recommendation 1", "general recommendation 2"]
        }}
        """

        system_instruction = """You are a compliance systems expert. Identify conflicts, overlaps, and gaps between rules that could cause implementation problems. Always respond with valid JSON."""

        try:
            response = await self._call_llm(prompt, system_instruction)
            parsed = self._parse_json_response(response)
            return parsed.get("cross_validation_issues", [])
        except Exception as e:
            self.log_progress(f"Cross-validation failed: {str(e)}", "warning")
            return []

    def _generate_validation_report(
        self, total_rules: int, valid_rules: int, issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a comprehensive validation report."""

        # Count issues by severity
        critical_count = len([i for i in issues if i.get("severity") == "critical"])
        warning_count = len([i for i in issues if i.get("severity") == "warning"])
        info_count = len([i for i in issues if i.get("severity") == "info"])

        # Count issues by type
        issue_types = {}
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        return {
            "validation_summary": {
                "total_rules_processed": total_rules,
                "rules_passed_validation": valid_rules,
                "rules_failed_validation": total_rules - valid_rules,
                "validation_success_rate": (
                    (valid_rules / total_rules) * 100 if total_rules > 0 else 0
                ),
            },
            "issue_summary": {
                "total_issues": len(issues),
                "critical_issues": critical_count,
                "warning_issues": warning_count,
                "info_issues": info_count,
            },
            "issue_breakdown": issue_types,
            "validation_timestamp": "timestamp_here",  # TODO: Add actual timestamp
            "quality_score": self._calculate_quality_score(
                valid_rules, total_rules, critical_count, warning_count
            ),
        }

    def _calculate_quality_score(
        self,
        valid_rules: int,
        total_rules: int,
        critical_issues: int,
        warning_issues: int,
    ) -> float:
        """Calculate an overall quality score for the rule set."""

        if total_rules == 0:
            return 0.0

        # Base score from validation success rate
        base_score = (valid_rules / total_rules) * 100

        # Deduct points for issues
        critical_penalty = critical_issues * 5
        warning_penalty = warning_issues * 2

        quality_score = max(0, base_score - critical_penalty - warning_penalty)
        return round(quality_score, 2)
