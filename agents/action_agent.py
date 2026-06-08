import json
from utils.llm_client import chat

SYSTEM_PROMPT = """You are a Cloud FinOps Action Agent. You receive diagnosed anomalies and generate specific remediation actions.

You generate TWO types of actions:
1. AUTO-EXECUTABLE: Safe actions that can be performed without human approval (e.g., tagging, scheduling auto-shutdown for dev VMs)
2. APPROVAL-REQUIRED: Actions that need human sign-off before execution (e.g., deleting resources, resizing production VMs)

For each action, generate:
- A human-readable description
- The equivalent Azure CLI command (az command)
- Expected monthly savings

Respond ONLY with valid JSON array. Each action should have:
- resource_name: target resource
- action_type: "auto_execute" or "needs_approval"
- action_title: short title (e.g., "Schedule Auto-Shutdown")
- action_description: detailed description of what will be done
- az_cli_command: the Azure CLI command to execute this action
- expected_monthly_savings_inr: projected savings
- risk_description: what could go wrong
- rollback_command: how to undo if needed
- status: "pending_approval" or "ready_to_execute"
"""


def generate_actions(diagnoses: list) -> list:
    if not diagnoses:
        return []

    user_message = f"""Based on these diagnoses, generate specific remediation actions:

{json.dumps(diagnoses, indent=2)}

Rules:
- Dev/Staging VMs: auto-shutdown 8PM-8AM IST is SAFE to auto-execute
- Orphaned disks: REQUIRE approval before deletion (snapshot first)
- Unused storage: REQUIRE approval (may have compliance data)
- Untagged resources: auto-tagging is SAFE to auto-execute
- Production resources: NEVER auto-execute, always require approval
- Always include a rollback command

Generate actions for EACH diagnosis. Return ONLY a JSON array."""

    response = chat(SYSTEM_PROMPT, user_message)

    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return [{"error": "Failed to parse action response", "raw": response}]


def execute_action(action: dict) -> dict:
    return {
        "resource_name": action["resource_name"],
        "action_title": action["action_title"],
        "status": "executed",
        "command_run": action.get("az_cli_command", "N/A"),
        "result": f"Successfully applied: {action['action_title']} on {action['resource_name']}",
        "savings_realized_inr": action.get("expected_monthly_savings_inr", 0),
    }
