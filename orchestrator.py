"""
FinOps Agentic Copilot — Autonomous Orchestrator
Uses OpenAI function calling to let the AI agent decide what to investigate,
diagnose, and remediate — a true agentic workflow, not a fixed pipeline.
"""
import json
from utils.llm_client import chat_with_tools
from tools.definitions import FINOPS_TOOLS

SYSTEM_PROMPT = """You are an autonomous Enterprise Cloud FinOps Agent managing Azure infrastructure for ABB (managed by HCLTech).

Mission: Identify cloud waste, diagnose root causes, execute safe optimizations, escalate risky actions for approval.

## Decision Framework
- SAFE (auto-execute): Auto-shutdown scheduling, adding tags
- NEEDS APPROVAL: Deleting resources, resizing VMs, deallocating
- NEVER auto-execute: Anything in Production

## Tools
query_cost_data, compare_costs, get_resource_details, detect_anomalies, check_resource_utilization, get_cost_trend, execute_remediation, generate_savings_report, list_pending_approvals, get_optimization_recommendations, list_resources

## Key Rules
- Use list_resources to enumerate Azure resources by type (storage, vm, disk, nsg, vnet, ip) in one or all subscriptions. Supports shortcut names.
- If a tool returns "not_found_or_no_access", do NOT retry. Note it for manual review and move on.
- ALWAYS use full resource IDs (/subscriptions/...) when calling execute_remediation.
- execute_remediation MUST include "action" param: delete_disk, delete_resource, deallocate_vm, resize_vm, schedule_auto_shutdown, snapshot_and_delete
- requires_approval=true for destructive actions; false for safe actions (tags, auto-shutdown)

## Cost Analysis
- "Why is cost high?": Use compare_costs (current vs previous month), investigate top increases
- Specific month: time_range="custom" with start_date/end_date
- Specific subscription: ALWAYS use filter_subscription in query_cost_data AND compare_costs
- List TOP 5-10 resources that changed most with actual names and cost deltas

## Subscriptions
- ABB-APP-NMG-DEV (35385e49-ebf7-46c4-98da-04f2d3dfa146)
- ABB-APP-NMG-PROD-01 (a4159714-6672-4c01-8e27-0c4c3569e7d5)
- ABB-APP-NMG-PROD-APM (ba3d8367-6849-475f-a8fe-558b2d1d9d3e)
- ABB-APP-NMG-STAGE (f291555e-6d94-4131-b099-e0c60d420777)
- ABB-MGMT (ce543a1a-5f5a-455f-9ded-0d5f8cd06f6f)

Be thorough, data-driven, explain reasoning. Show business impact in INR.
"""


def run_autonomous_pipeline() -> dict:
    """Run the full autonomous FinOps agent — the agent decides what tools to call."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": """Run a comprehensive FinOps optimization cycle:

1. Scan current costs and detect all anomalies
2. For the top anomalies, investigate resource utilization and trends
3. Execute safe optimizations (auto-shutdown, tagging) immediately
4. Queue risky actions (deletions, resizing) for my approval
5. Generate a savings report with projections

Be thorough — check every resource that looks wasteful. Show me the numbers."""},
    ]

    final_response, tool_calls = chat_with_tools(messages, FINOPS_TOOLS, max_iterations=15)
    return {"response": final_response, "tool_calls": tool_calls, "iterations": len(set(t["iteration"] for t in tool_calls))}


def run_conversational(user_query: str, conversation_history: list = None) -> tuple:
    """Handle a conversational query from the user with full tool access."""
    if conversation_history is None:
        conversation_history = []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_query})

    final_response, tool_calls = chat_with_tools(messages, FINOPS_TOOLS, max_iterations=10)

    conversation_history.append({"role": "user", "content": user_query})
    conversation_history.append({"role": "assistant", "content": final_response})

    return final_response, tool_calls, conversation_history


if __name__ == "__main__":
    print("=" * 60)
    print("FINOPS AGENTIC COPILOT — AUTONOMOUS RUN")
    print("=" * 60)
    result = run_autonomous_pipeline()
    print(f"\nAgent completed in {result['iterations']} iterations")
    print(f"Tool calls made: {len(result['tool_calls'])}")
    print("\nTools used:")
    for tc in result["tool_calls"]:
        print(f"  [{tc['iteration']}] {tc['tool']}({json.dumps(tc['arguments'], indent=None)[:80]})")
    print("\n" + "=" * 60)
    print("AGENT RESPONSE:")
    print("=" * 60)
    print(result["response"])
