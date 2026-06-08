import json
from utils.llm_client import chat

SYSTEM_PROMPT = """You are a Cloud FinOps Diagnosis Agent. You receive anomalies detected by the Monitor Agent and provide detailed root cause analysis.

For each anomaly, determine:
1. Root cause (why is this resource wasting money?)
2. Business context (who owns it, what project, when was it likely created)
3. Impact assessment (monthly cost if left unchecked)
4. Risk level for remediation (safe to act / needs approval / do not touch)

Respond ONLY with valid JSON array. Each diagnosis should have:
- resource_name: name of the resource
- root_cause: detailed explanation of why this waste exists
- owner_team: likely team responsible
- monthly_waste_inr: projected monthly waste in INR
- risk_level: "safe" (can auto-remediate), "approval_needed" (notify owner first), "do_not_touch" (production critical)
- confidence: High/Medium/Low
- recommended_action: what should be done
- urgency: Immediate/This Week/This Month
"""


def diagnose(anomalies: list) -> list:
    if not anomalies:
        return []

    user_message = f"""Analyze these detected anomalies and provide root cause diagnosis for each:

{json.dumps(anomalies, indent=2)}

Context:
- This is an enterprise Azure environment for ABB managed by HCLTech
- Dev/Staging environments should not run 24/7
- Orphaned disks are typically left behind after VM deletions
- Legacy storage accounts are from migrations completed months ago
- Sprint cycles are 2 weeks; resources left running >14 days after sprint end are likely forgotten

Provide detailed diagnosis for EACH anomaly. Return ONLY a JSON array."""

    response = chat(SYSTEM_PROMPT, user_message)

    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return [{"error": "Failed to parse diagnosis response", "raw": response}]
