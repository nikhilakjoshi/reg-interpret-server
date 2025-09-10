"""
Rule Synthesizer Agent

Responsible for synthesizing validated rules into final, actionable compliance
rules with enhanced metadata, monitoring guidelines, and implementation guidance.
"""

from typing import Dict, Any, List
from .base import BaseAgent, AgentResult


class RuleSynthesizer(BaseAgent):
    """
    Synthesizes validated compliance rules into final, actionable rules with
    comprehensive metadata, implementation guidance, and monitoring instructions.
    """

    @property
    def agent_name(self) -> str:
        return "Rule Synthesizer"

    @property
    def description(self) -> str:
        return "Synthesizes validated rules into final, actionable compliance rules"

    async def process(
        self, input_data: List[Dict[str, Any]], context: Dict[str, Any] = None
    ) -> AgentResult:
        """
        Synthesize validated rules into final compliance rules.

        Args:
            input_data: List of validated rules from Rule Validator
            context: Previous agent results for additional context

        Returns:
            AgentResult containing final synthesized rules
        """
        self.log_progress("Starting rule synthesis...")

        try:
            validated_rules = (
                input_data
                if isinstance(input_data, list)
                else input_data.get("validated_rules", [])
            )

            if not validated_rules:
                self.log_progress("No validated rules to synthesize", "warning")
                return AgentResult(
                    success=True,
                    data={"final_rules": []},
                    metadata={"agent": self.agent_name},
                )

            self.log_progress(f"Synthesizing {len(validated_rules)} validated rules...")

            # Group rules by theme and priority for better synthesis
            grouped_rules = self._group_rules_for_synthesis(validated_rules)

            synthesized_rules = []

            # Process each group
            for group_name, rules_group in grouped_rules.items():
                self.log_progress(
                    f"Synthesizing {len(rules_group)} rules for group: {group_name}"
                )

                group_synthesized = await self._synthesize_rule_group(
                    rules_group, group_name
                )
                synthesized_rules.extend(group_synthesized)

            # Add final enhancements to all rules
            final_rules = await self._add_final_enhancements(synthesized_rules, context)

            # Generate synthesis summary
            synthesis_summary = self._generate_synthesis_summary(
                final_rules, validated_rules
            )

            result_data = {
                "final_rules": final_rules,
                "synthesis_summary": synthesis_summary,
            }

            self.log_progress(
                f"Synthesis completed: {len(final_rules)} final rules generated"
            )

            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "agent": self.agent_name,
                    "rules_synthesized": len(final_rules),
                },
            )

        except Exception as e:
            self.log_progress(f"Rule synthesis failed: {str(e)}", "error")
            return AgentResult(
                success=False, data=None, errors=[f"Rule synthesis failed: {str(e)}"]
            )

    def _group_rules_for_synthesis(
        self, validated_rules: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group rules by theme and priority for more coherent synthesis."""

        groups = {}

        for rule_data in validated_rules:
            rule = rule_data.get("original_rule", {})
            classification = rule_data.get("classification", {})

            # Determine grouping key
            theme = rule.get("compliance_theme", "general")
            priority = classification.get("implementation_priority", "p4")

            # Create group key
            group_key = f"{theme}_{priority}"

            if group_key not in groups:
                groups[group_key] = []

            groups[group_key].append(rule_data)

        return groups

    async def _synthesize_rule_group(
        self, rules_group: List[Dict[str, Any]], group_name: str
    ) -> List[Dict[str, Any]]:
        """Synthesize a group of related rules."""

        if len(rules_group) == 1:
            # Single rule - enhance it directly
            return [await self._synthesize_single_rule(rules_group[0])]

        # Multiple rules - check for consolidation opportunities
        return await self._synthesize_multiple_rules(rules_group, group_name)

    async def _synthesize_single_rule(
        self, rule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize a single rule with comprehensive enhancements."""

        rule = rule_data.get("original_rule", {})
        classification = rule_data.get("classification", {})

        prompt = f"""
        Transform this validated compliance rule into a comprehensive, actionable final rule with all necessary implementation details.
        
        Original Rule:
        Title: {rule.get('rule_title', '')}
        Description: {rule.get('rule_description', '')}
        Type: {rule.get('requirement_type', '')}
        Obligations: {'; '.join(rule.get('key_obligations', []))}
        Target Entities: {'; '.join(rule.get('target_entities', []))}
        Penalties: {'; '.join(rule.get('penalties', []))}
        
        Classification:
        Risk Level: {classification.get('risk_level', '')}
        Priority: {classification.get('implementation_priority', '')}
        Complexity: {classification.get('complexity', '')}
        
        Create a comprehensive final rule with this JSON structure:
        
        {{
            "rule_id": "unique_identifier",
            "rule_title": "clear, actionable title",
            "rule_description": "comprehensive description",
            "compliance_theme": "theme category",
            "requirement_type": "mandatory|recommended|prohibited",
            "risk_level": "critical|high|medium|low",
            "implementation_priority": "p1|p2|p3|p4",
            "target_entities": ["specific entities this applies to"],
            "key_obligations": ["specific, measurable obligations"],
            "implementation_guidance": {{
                "steps": ["step 1", "step 2", "step 3"],
                "required_resources": ["resource 1", "resource 2"],
                "estimated_timeline": "time estimate",
                "success_criteria": ["criteria 1", "criteria 2"]
            }},
            "monitoring_requirements": {{
                "frequency": "continuous|daily|weekly|monthly|quarterly|annual",
                "methods": ["monitoring method 1", "monitoring method 2"],
                "metrics": ["metric 1", "metric 2"],
                "reporting_requirements": ["report 1", "report 2"]
            }},
            "violation_detection": {{
                "detection_criteria": ["criteria 1", "criteria 2"],
                "red_flags": ["warning sign 1", "warning sign 2"],
                "detection_methods": ["method 1", "method 2"],
                "escalation_triggers": ["trigger 1", "trigger 2"]
            }},
            "compliance_evidence": {{
                "required_documentation": ["doc 1", "doc 2"],
                "audit_trail_requirements": ["requirement 1", "requirement 2"],
                "record_retention": "retention period",
                "documentation_standards": ["standard 1", "standard 2"]
            }},
            "penalties_and_consequences": {{
                "regulatory_penalties": ["penalty 1", "penalty 2"],
                "business_consequences": ["consequence 1", "consequence 2"],
                "remediation_requirements": ["requirement 1", "requirement 2"]
            }},
            "stakeholder_responsibilities": {{
                "primary_owner": "role/department",
                "supporting_roles": ["role 1", "role 2"],
                "escalation_path": ["level 1", "level 2", "level 3"],
                "training_requirements": ["training 1", "training 2"]
            }},
            "technology_requirements": {{
                "automation_opportunities": ["opportunity 1", "opportunity 2"],
                "system_requirements": ["system 1", "system 2"],
                "integration_points": ["integration 1", "integration 2"],
                "data_requirements": ["data 1", "data 2"]
            }},
            "source_information": {{
                "regulation_source": "{rule.get('source_section', '')}",
                "legal_basis": "{rule.get('legal_basis', '')}",
                "last_updated": "date",
                "version": "1.0"
            }}
        }}
        """

        system_instruction = """You are a compliance implementation expert. Create comprehensive, actionable compliance rules that organizations can directly implement. Include all necessary details for successful compliance monitoring and implementation. Always respond with valid JSON."""

        response = await self._call_llm(prompt, system_instruction)
        parsed = self._parse_json_response(response)

        return parsed

    async def _synthesize_multiple_rules(
        self, rules_group: List[Dict[str, Any]], group_name: str
    ) -> List[Dict[str, Any]]:
        """Synthesize multiple related rules, checking for consolidation opportunities."""

        # For now, synthesize each rule individually
        # In a more advanced implementation, we could identify consolidation opportunities
        synthesized_rules = []

        for rule_data in rules_group:
            synthesized_rule = await self._synthesize_single_rule(rule_data)
            synthesized_rules.append(synthesized_rule)

        return synthesized_rules

    async def _add_final_enhancements(
        self, synthesized_rules: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Add final enhancements to all synthesized rules."""

        enhanced_rules = []

        for i, rule in enumerate(synthesized_rules):
            # Add unique IDs
            rule["rule_id"] = f"RULE_{i+1:03d}"

            # Add metadata from context if available
            if context:
                doc_analysis = context.get("document_analysis", {})
                if doc_analysis:
                    rule["source_information"]["document_type"] = doc_analysis.get(
                        "structure_analysis", {}
                    ).get("document_type", "unknown")
                    rule["source_information"]["regulatory_authority"] = (
                        doc_analysis.get("structure_analysis", {}).get(
                            "regulatory_authority", "unknown"
                        )
                    )

            # Add synthesis metadata
            rule["synthesis_metadata"] = {
                "created_by": "AI Rule Generation System",
                "synthesis_version": "1.0",
                "quality_assurance": "multi-agent-validated",
                "last_reviewed": "auto-generated",
            }

            enhanced_rules.append(rule)

        return enhanced_rules

    def _generate_synthesis_summary(
        self, final_rules: List[Dict[str, Any]], original_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a summary of the synthesis process."""

        if not final_rules:
            return {}

        # Count rules by various dimensions
        risk_distribution = {}
        priority_distribution = {}
        theme_distribution = {}

        for rule in final_rules:
            # Risk level distribution
            risk_level = rule.get("risk_level", "unknown")
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1

            # Priority distribution
            priority = rule.get("implementation_priority", "unknown")
            priority_distribution[priority] = priority_distribution.get(priority, 0) + 1

            # Theme distribution
            theme = rule.get("compliance_theme", "unknown")
            theme_distribution[theme] = theme_distribution.get(theme, 0) + 1

        # Calculate implementation timeline estimates
        high_priority_rules = len(
            [r for r in final_rules if r.get("implementation_priority") in ["p1", "p2"]]
        )
        critical_rules = len(
            [r for r in final_rules if r.get("risk_level") == "critical"]
        )

        return {
            "synthesis_overview": {
                "total_final_rules": len(final_rules),
                "original_rules_processed": len(original_rules),
                "synthesis_success_rate": 100.0,  # All validated rules were synthesized
                "average_rule_completeness": self._calculate_completeness_score(
                    final_rules
                ),
            },
            "rule_distribution": {
                "risk_levels": risk_distribution,
                "implementation_priorities": priority_distribution,
                "compliance_themes": theme_distribution,
            },
            "implementation_overview": {
                "high_priority_rules": high_priority_rules,
                "critical_risk_rules": critical_rules,
                "estimated_implementation_phases": self._estimate_implementation_phases(
                    final_rules
                ),
                "key_stakeholder_groups": self._identify_key_stakeholders(final_rules),
            },
            "quality_indicators": {
                "rules_with_monitoring": len(
                    [r for r in final_rules if r.get("monitoring_requirements")]
                ),
                "rules_with_automation": len(
                    [
                        r
                        for r in final_rules
                        if r.get("technology_requirements", {}).get(
                            "automation_opportunities"
                        )
                    ]
                ),
                "rules_with_complete_guidance": len(
                    [
                        r
                        for r in final_rules
                        if r.get("implementation_guidance", {}).get("steps")
                    ]
                ),
            },
        }

    def _calculate_completeness_score(self, rules: List[Dict[str, Any]]) -> float:
        """Calculate average completeness score for the rule set."""

        if not rules:
            return 0.0

        total_score = 0
        required_sections = [
            "implementation_guidance",
            "monitoring_requirements",
            "violation_detection",
            "compliance_evidence",
            "stakeholder_responsibilities",
        ]

        for rule in rules:
            rule_score = 0
            for section in required_sections:
                if rule.get(section):
                    rule_score += 1

            total_score += (rule_score / len(required_sections)) * 100

        return round(total_score / len(rules), 2)

    def _estimate_implementation_phases(
        self, rules: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Estimate implementation phases based on rule priorities."""

        phases = {
            "phase_1_immediate": 0,  # P1 rules
            "phase_2_short_term": 0,  # P2 rules
            "phase_3_medium_term": 0,  # P3 rules
            "phase_4_long_term": 0,  # P4 rules
        }

        for rule in rules:
            priority = rule.get("implementation_priority", "p4")
            if priority == "p1":
                phases["phase_1_immediate"] += 1
            elif priority == "p2":
                phases["phase_2_short_term"] += 1
            elif priority == "p3":
                phases["phase_3_medium_term"] += 1
            else:
                phases["phase_4_long_term"] += 1

        return phases

    def _identify_key_stakeholders(self, rules: List[Dict[str, Any]]) -> List[str]:
        """Identify key stakeholder groups across all rules."""

        stakeholders = set()

        for rule in rules:
            responsibilities = rule.get("stakeholder_responsibilities", {})
            primary_owner = responsibilities.get("primary_owner")
            if primary_owner:
                stakeholders.add(primary_owner)

            supporting_roles = responsibilities.get("supporting_roles", [])
            stakeholders.update(supporting_roles)

        return list(stakeholders)
