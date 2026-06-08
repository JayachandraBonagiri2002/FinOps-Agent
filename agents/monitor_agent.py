import pandas as pd
import json
from utils.llm_client import chat

SYSTEM_PROMPT = """You are a Cloud FinOps Monitor Agent. Your job is to analyze Azure cost data and detect anomalies and waste.

You look for:
1. VMs running 24/7 in non-production environments (Dev, Staging, Test)
2. Orphaned disks (disks with no owner tag or not attached to any VM)
3. Unused resources (storage accounts, public IPs with no activity)
4. Cost spikes (resources costing significantly more than expected)
5. Untagged resources (missing Owner or Project tags)

Respond ONLY with valid JSON array of anomalies found. Each anomaly should have:
- resource_name: name of the resource
- resource_type: type of resource
- environment: Dev/Staging/Prod
- anomaly_type: one of [24x7_non_prod, orphaned_resource, unused_resource, cost_spike, untagged_resource]
- daily_cost_inr: daily cost in INR
- weekly_cost_inr: weekly cost in INR
- monthly_projected_inr: projected monthly cost
- owner: owner if known, else "Unknown"
- severity: High/Medium/Low
- description: brief description of the issue
"""


def analyze_costs(csv_path: str) -> list:
    df = pd.read_csv(csv_path)

    summary = []
    for name, group in df.groupby("ResourceName"):
        row = group.iloc[0]
        total_cost = group["CostINR"].sum()
        daily_avg = group["CostINR"].mean()
        summary.append({
            "resource_name": name,
            "resource_type": row["ResourceType"],
            "environment": row["Tags_Environment"],
            "owner": row["Tags_Owner"] if pd.notna(row["Tags_Owner"]) else "Unknown",
            "project": row["Tags_Project"] if pd.notna(row["Tags_Project"]) else "Unknown",
            "location": row["Location"],
            "service": row["ServiceName"],
            "daily_avg_cost_inr": round(daily_avg, 2),
            "total_7day_cost_inr": round(total_cost, 2),
            "days_running": len(group),
            "avg_usage_hours": group["UsageHours"].mean(),
        })

    user_message = f"""Analyze the following Azure resource cost summary for the past 7 days and identify all anomalies and waste:

{json.dumps(summary, indent=2)}

Key context:
- Non-production VMs running 24 hours/day are wasteful (should be 10-12 hours on weekdays only)
- Disks with no owner are likely orphaned
- Storage accounts tagged "Legacy" with no project are candidates for deletion
- Public IPs with no owner are likely unused
- Any resource costing >₹5000/day in Dev/Staging deserves scrutiny

Return ONLY a JSON array of anomalies."""

    response = chat(SYSTEM_PROMPT, user_message)

    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return [{"error": "Failed to parse monitor response", "raw": response}]
