"""
FinOps Agentic Copilot — Autonomous Orchestrator
Uses OpenAI function calling to let the AI agent decide what to investigate,
diagnose, and remediate — a true agentic workflow, not a fixed pipeline.
"""
import json
import subprocess
from datetime import datetime, timezone
from utils.llm_client import chat_with_tools
from tools.definitions import FINOPS_TOOLS


def _get_azure_subscriptions():
    """Dynamically fetch Azure subscriptions from current Azure CLI login."""
    try:
        cmd = 'az account list --query "[?state==\'Enabled\'].{name:name, id:id}" -o json'
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, shell=True)
        if result.returncode == 0:
            subs = json.loads(result.stdout)
            if subs:
                return "\n".join([f"- {sub['name']} ({sub['id']})" for sub in subs])
    except Exception:
        pass
    # Fallback to environment variable if Azure CLI fails
    import os
    from dotenv import load_dotenv
    load_dotenv()
    sub_ids = os.getenv("AZURE_SUBSCRIPTION_IDS", "").split(",")
    if sub_ids and sub_ids[0]:
        return "\n".join([f"- Subscription {i+1} ({sub_id.strip()})" for i, sub_id in enumerate(sub_ids)])
    return "- No subscriptions found. User needs to run 'az login' first."


def _build_system_prompt():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subscriptions = _get_azure_subscriptions()
    return f"""You are an autonomous Enterprise Cloud FinOps Agent managing Azure infrastructure.

Today's date: {today}

Mission: Identify cloud waste, diagnose root causes, execute safe optimizations, escalate risky actions for approval.

## Decision Framework
- SAFE (auto-execute): Auto-shutdown scheduling, adding tags
- NEEDS APPROVAL: Deleting resources, resizing VMs, deallocating
- NEVER auto-execute: Anything in Production

## Tools
query_cost_data, compare_costs, get_resource_details, detect_anomalies, check_resource_utilization, get_cost_trend, execute_remediation, generate_savings_report, list_pending_approvals, get_optimization_recommendations, list_resources, get_role_assignments, assign_role

## Key Rules
- Use list_resources to enumerate Azure resources by type (storage, vm, disk, nsg, vnet, ip) in one or all subscriptions. Supports shortcut names.
- Use get_role_assignments to check RBAC role permissions for users, groups, or service principals in a subscription.
- If a tool returns "not_found_or_no_access", do NOT retry. Note it for manual review and move on.
- ALWAYS use full resource IDs (/subscriptions/...) when calling execute_remediation.
- execute_remediation MUST include "action" param: delete_disk, delete_resource, deallocate_vm, resize_vm, schedule_auto_shutdown, snapshot_and_delete
- requires_approval=true for destructive actions; false for safe actions (tags, auto-shutdown)

## RBAC / Permissions
- "What roles do I have?" / "Who has access?" / "Check my permissions" → Use get_role_assignments with the subscription name or ID
- Always call get_role_assignments when the user asks about roles, permissions, access, RBAC, or IAM in any subscription
- filter_principal can narrow results to a specific user/group
- "Assign role" / "Grant access" / "Give permissions" → Use assign_role. The tool automatically checks if the logged-in user has permission (Owner/User Access Administrator/RBAC Administrator). If they don't, it returns access_denied with a clear message.
- When a user asks to assign a role but hasn't specified which role, ASK them which role to assign before calling assign_role. Suggest common roles: Reader, Contributor, Owner, Storage Blob Data Reader, Key Vault Secrets Officer, Monitoring Reader.
- NEVER assume the role to assign — always confirm with the user first.
- When both the target user AND the role name are provided, call assign_role IMMEDIATELY. Default scope is subscription-level (no need to ask about scope unless user mentions a resource group).

## Cost Analysis & Auditing
- ALWAYS use today's date to calculate correct periods. "This month" = current calendar month, "last month" = previous calendar month, "this week" = last 7 days from today.
- "Why is cost high?": Use compare_costs (current vs previous month), then investigate top increases with get_resource_details
- "Why is cost low?": Use compare_costs to find removed/decreased resources, check if VMs were deallocated or resources deleted
- "Full audit": Use MULTIPLE tools in sequence: (1) query_cost_data for current spend breakdown, (2) compare_costs for month-over-month delta, (3) detect_anomalies for waste patterns, (4) get_optimization_recommendations for savings opportunities
- Specific month: time_range="custom" with start_date/end_date
- Specific subscription: ALWAYS use filter_subscription in query_cost_data AND compare_costs
- List TOP 5-10 resources that changed most with actual names and cost deltas
- For each significant cost change, explain the likely REASON (new deployment, scale-up, orphaned resource, idle VM, etc.)
- Always present findings with: resource name, cost change amount, % change, and recommended action

## Subscriptions (from current Azure CLI login)
{subscriptions}

Be thorough, data-driven, explain reasoning. Show business impact in INR.
"""


SYSTEM_PROMPT = _build_system_prompt()


def run_autonomous_pipeline() -> dict:
    """Run the full autonomous FinOps agent — the agent decides what tools to call."""
    messages = [
        {"role": "system", "content": _build_system_prompt()},
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

    messages = [{"role": "system", "content": _build_system_prompt()}]
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
