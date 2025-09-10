#!/usr/bin/env python3
"""
Simple test script for the multi-agent rule generation system.
"""

import asyncio
import json
from ai.agents import RuleGenerationOrchestrator


async def test_multi_agent_system():
    """Test the multi-agent rule generation system with sample text."""

    sample_document = """
    REGULATION SAMPLE - FINANCIAL ADVISORY SERVICES
    
    Section 1: Best Interest Standard
    All financial advisors must act in the best interest of their clients when providing investment advice.
    
    Section 2: Disclosure Requirements
    Advisors must disclose all material conflicts of interest, including compensation arrangements that could influence their recommendations.
    
    Section 3: Suitability Requirements
    All investment recommendations must be suitable for the client's financial situation, investment objectives, and risk tolerance.
    
    Section 4: Record Keeping
    Advisors must maintain detailed records of all client interactions and recommendations for a minimum of 5 years.
    
    Section 5: Prohibited Practices
    Advisors are prohibited from:
    - Making misleading statements about investment products
    - Engaging in churning or excessive trading
    - Recommending unsuitable investments
    """

    print("🚀 Testing multi-agent rule generation system...")

    try:
        orchestrator = RuleGenerationOrchestrator()

        print("📄 Processing sample regulation document...")

        message_count = 0
        final_rules = []

        async for message in orchestrator.generate_rules_stream(sample_document, 1):
            message_count += 1

            try:
                parsed = json.loads(message)
                message_type = parsed.get("type", "unknown")

                print(f"🔄 Message {message_count}: {message_type}")

                if message_type == "pipeline_completed":
                    final_rules = parsed.get("data", {}).get("final_rules", [])
                    print(f"✅ Pipeline completed with {len(final_rules)} rules")
                elif message_type == "stage_completed":
                    stage_info = parsed.get("data", {})
                    print(
                        f"   Stage {stage_info.get('stage_name', 'unknown')} completed"
                    )
                elif message_type == "error":
                    print(f"❌ Error: {parsed.get('error', 'Unknown error')}")

            except json.JSONDecodeError:
                print(f"📝 Raw message: {message[:100]}...")

        print(f"\n🎯 Test Results:")
        print(f"   Total messages: {message_count}")
        print(f"   Final rules generated: {len(final_rules)}")

        if final_rules:
            print(f"\n📋 Sample rule:")
            sample_rule = final_rules[0]
            print(f"   Title: {sample_rule.get('rule_title', 'No title')}")
            print(f"   Risk Level: {sample_rule.get('risk_level', 'Unknown')}")
            print(
                f"   Priority: {sample_rule.get('implementation_priority', 'Unknown')}"
            )

        return len(final_rules) > 0

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_multi_agent_system())
    if success:
        print("\n✅ Multi-agent system test passed!")
    else:
        print("\n❌ Multi-agent system test failed!")
