import json
from utils.llm_client import chat

SYSTEM_PROMPT = """You are a Cloud FinOps Reporting Agent. You generate executive-level savings reports based on actions taken by the FinOps Agent system.

Your reports should be:
- Clear and concise
- Business-focused (highlight ₹ saved, not technical details)
- Include trend analysis
- Recommend next steps

Respond with a JSON object containing:
- summary: 2-3 sentence executive summary
- total_monthly_savings_inr: total projected monthly savings
- total_annual_savings_inr: annualized savings
- actions_taken: count of actions executed
- actions_pending: count of actions awaiting approval
- top_savings_opportunities: array of top 3 items with resource_name and savings_inr
- recommendations: array of 3-5 strategic recommendations
- risk_items: any items flagged as risky that need attention
"""


def generate_report(anomalies: list, diagnoses: list, actions: list, executed: list) -> dict:
    user_message = f"""Generate an executive FinOps savings report based on this agent pipeline run:

## Anomalies Detected
{json.dumps(anomalies, indent=2)}

## Diagnoses
{json.dumps(diagnoses, indent=2)}

## Actions Generated
{json.dumps(actions, indent=2)}

## Actions Executed
{json.dumps(executed, indent=2)}

Context:
- This is a weekly automated run for ABB's Azure environment managed by HCLTech
- Currency is INR (₹)
- The goal is to show business stakeholders the value of autonomous FinOps
- Be specific with numbers and resource names

Return ONLY a JSON object with the report."""

    response = chat(SYSTEM_PROMPT, user_message)

    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "Failed to parse report response", "raw": response}
