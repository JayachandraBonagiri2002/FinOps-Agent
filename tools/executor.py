import pandas as pd
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
LIVE_MODE = bool(os.getenv("AZURE_SUBSCRIPTION_ID"))


def load_cost_data():
    current = pd.read_csv(os.path.join(DATA_DIR, "azure_cost_export.csv"))
    history = pd.read_csv(os.path.join(DATA_DIR, "azure_cost_history.csv"))
    return pd.concat([history, current], ignore_index=True)


def execute_tool(tool_name: str, arguments: dict, session_state: dict = None) -> str:
    if LIVE_MODE:
        from tools.azure_live import execute_tool_live
        return execute_tool_live(tool_name, arguments, session_state)
    handlers = {
        "query_cost_data": _query_cost_data,
        "get_resource_details": _get_resource_details,
        "detect_anomalies": _detect_anomalies,
        "check_resource_utilization": _check_resource_utilization,
        "get_cost_trend": _get_cost_trend,
        "execute_remediation": _execute_remediation,
        "generate_savings_report": _generate_savings_report,
        "list_pending_approvals": _list_pending_approvals,
        "get_optimization_recommendations": _get_optimization_recommendations,
        "compare_costs": _compare_costs,
        "list_resources": _list_resources,
        "get_role_assignments": _get_role_assignments,
        "assign_role": _assign_role,
    }

    handler = handlers.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    return handler(arguments, session_state or {})


def _query_cost_data(args: dict, state: dict) -> str:
    df = load_cost_data()
    time_range = args.get("time_range", "last_7_days")
    group_by = args.get("group_by", "resource")
    filter_env = args.get("filter_environment", "all")
    filter_type = args.get("filter_resource_type")

    df["UsageDate"] = pd.to_datetime(df["UsageDate"])
    max_date = df["UsageDate"].max()

    if time_range == "last_7_days":
        start = max_date - timedelta(days=6)
    elif time_range == "last_14_days":
        start = max_date - timedelta(days=13)
    elif time_range == "last_30_days":
        start = max_date - timedelta(days=29)
    elif time_range == "current_week":
        start = max_date - timedelta(days=6)
    else:
        start = max_date - timedelta(days=13)

    df = df[df["UsageDate"] >= start]

    if filter_env and filter_env != "all":
        df = df[df["Tags_Environment"] == filter_env]
    if filter_type:
        df = df[df["ResourceType"] == filter_type]

    group_col = {
        "resource": "ResourceName",
        "resource_group": "ResourceGroup",
        "service": "ServiceName",
        "environment": "Tags_Environment",
        "owner": "Tags_Owner",
    }.get(group_by, "ResourceName")

    result = df.groupby(group_col).agg(
        total_cost_inr=("CostINR", "sum"),
        daily_avg_inr=("CostINR", "mean"),
        days_active=("UsageDate", "nunique"),
        avg_usage_hours=("UsageHours", "mean"),
    ).round(2).reset_index()

    result = result.rename(columns={group_col: "group_key"})
    result = result.sort_values("total_cost_inr", ascending=False)

    return json.dumps({
        "query": {"time_range": time_range, "group_by": group_by, "filters": {"environment": filter_env, "resource_type": filter_type}},
        "summary": {"total_cost_inr": round(df["CostINR"].sum(), 2), "unique_resources": df["ResourceName"].nunique(), "date_range": f"{start.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"},
        "data": result.to_dict("records"),
    }, default=str)


RESOURCE_DB = {
    "vm-dev-api-001": {
        "type": "Microsoft.Compute/virtualMachines",
        "size": "Standard_D4s_v3",
        "state": "Running",
        "environment": "Development",
        "owner": "rajesh.kumar",
        "project": "ProjectAlpha",
        "location": "westindia",
        "created": "2026-03-15",
        "os": "Ubuntu 22.04 LTS",
        "auto_shutdown": "Disabled",
        "cpu_avg_7d": 12.3,
        "memory_avg_7d": 28.5,
        "network_in_gb_7d": 2.1,
        "network_out_gb_7d": 0.8,
    },
    "vm-dev-api-002": {
        "type": "Microsoft.Compute/virtualMachines",
        "size": "Standard_D8s_v3",
        "state": "Running",
        "environment": "Development",
        "owner": "priya.sharma",
        "project": "ProjectBeta",
        "location": "westindia",
        "created": "2026-04-02",
        "os": "Ubuntu 22.04 LTS",
        "auto_shutdown": "Disabled",
        "cpu_avg_7d": 8.7,
        "memory_avg_7d": 22.1,
        "network_in_gb_7d": 1.4,
        "network_out_gb_7d": 0.3,
    },
    "vm-prod-web-001": {
        "type": "Microsoft.Compute/virtualMachines",
        "size": "Standard_D8s_v3",
        "state": "Running",
        "environment": "Production",
        "owner": "ops.team",
        "project": "CorePlatform",
        "location": "centralindia",
        "created": "2025-11-10",
        "os": "Windows Server 2022",
        "auto_shutdown": "Disabled",
        "cpu_avg_7d": 67.2,
        "memory_avg_7d": 72.8,
        "network_in_gb_7d": 45.3,
        "network_out_gb_7d": 112.7,
    },
    "vm-staging-load-001": {
        "type": "Microsoft.Compute/virtualMachines",
        "size": "Standard_E8s_v4",
        "state": "Running",
        "environment": "Staging",
        "owner": "anil.verma",
        "project": "LoadTest",
        "location": "westindia",
        "created": "2026-05-10",
        "os": "Ubuntu 22.04 LTS",
        "auto_shutdown": "Disabled",
        "cpu_avg_7d": 3.2,
        "memory_avg_7d": 15.6,
        "network_in_gb_7d": 0.2,
        "network_out_gb_7d": 0.1,
        "last_load_test": "2026-05-22",
    },
    "disk-orphaned-001": {
        "type": "Microsoft.Compute/disks",
        "size_gb": 256,
        "sku": "Premium_LRS",
        "state": "Unattached",
        "environment": "Development",
        "owner": None,
        "project": None,
        "location": "westindia",
        "created": "2026-02-10",
        "attached_vm": None,
        "last_attach_date": "2026-03-28",
    },
    "disk-orphaned-002": {
        "type": "Microsoft.Compute/disks",
        "size_gb": 512,
        "sku": "Premium_LRS",
        "state": "Unattached",
        "environment": "Development",
        "owner": None,
        "project": None,
        "location": "westindia",
        "created": "2026-01-22",
        "attached_vm": None,
        "last_attach_date": "2026-04-05",
    },
    "stdevunused001": {
        "type": "Microsoft.Storage/storageAccounts",
        "sku": "Standard_LRS",
        "state": "Active",
        "environment": "Development",
        "owner": None,
        "project": "Legacy",
        "location": "westindia",
        "created": "2025-08-15",
        "last_access": "2026-03-01",
        "total_size_gb": 45.2,
        "blob_count": 1823,
        "containers": ["old-backups", "migration-temp", "test-artifacts"],
    },
    "pip-unused-001": {
        "type": "Microsoft.Network/publicIPAddresses",
        "sku": "Standard",
        "state": "Not associated",
        "environment": "Development",
        "owner": None,
        "project": None,
        "location": "westindia",
        "created": "2026-01-05",
        "associated_resource": None,
        "ip_address": "20.219.xx.xx",
    },
}


def _get_resource_details(args: dict, state: dict) -> str:
    name = args["resource_name"]
    resource = RESOURCE_DB.get(name)
    if not resource:
        return json.dumps({"error": f"Resource '{name}' not found"})

    result = {"resource_name": name, **resource}
    if args.get("include_metrics") and "cpu_avg_7d" in resource:
        result["metrics"] = {
            "cpu_utilization_avg_percent": resource.get("cpu_avg_7d"),
            "memory_utilization_avg_percent": resource.get("memory_avg_7d"),
            "network_in_gb": resource.get("network_in_gb_7d"),
            "network_out_gb": resource.get("network_out_gb_7d"),
        }
    return json.dumps(result, default=str)


def _detect_anomalies(args: dict, state: dict) -> str:
    df = load_cost_data()
    df["UsageDate"] = pd.to_datetime(df["UsageDate"])
    max_date = df["UsageDate"].max()

    current = df[df["UsageDate"] > max_date - timedelta(days=7)]
    baseline = df[df["UsageDate"] <= max_date - timedelta(days=7)]

    min_cost = args.get("min_cost_threshold_inr", 100)
    anomalies = []

    for name in current["ResourceName"].unique():
        curr_data = current[current["ResourceName"] == name]
        base_data = baseline[baseline["ResourceName"] == name]

        curr_avg = curr_data["CostINR"].mean()
        if curr_avg < min_cost:
            continue

        base_avg = base_data["CostINR"].mean() if not base_data.empty else 0

        row = curr_data.iloc[0]
        env = row["Tags_Environment"]
        usage_hours = curr_data["UsageHours"].mean()

        anomaly = None
        if env in ["Development", "Staging"] and usage_hours >= 23:
            anomaly = {
                "resource_name": name,
                "type": "24x7_non_production",
                "severity": "High" if curr_avg > 5000 else "Medium",
                "current_daily_cost_inr": round(curr_avg, 2),
                "baseline_daily_cost_inr": round(base_avg, 2),
                "change_percent": round(((curr_avg - base_avg) / base_avg * 100) if base_avg > 0 else 100, 1),
                "environment": env,
                "usage_hours_avg": round(usage_hours, 1),
                "description": f"{name} running 24/7 in {env} — expected max 12 hours on weekdays",
                "potential_savings_monthly_inr": round(curr_avg * 30 * 0.5, 2),
            }
        elif pd.isna(row.get("Tags_Owner", None)) or row.get("Tags_Owner") == "":
            resource_type = row["ResourceType"]
            if "disks" in resource_type.lower():
                anomaly_type = "orphaned_disk"
                desc = f"{name} is an unattached disk with no owner — likely orphaned after VM deletion"
            elif "storage" in resource_type.lower():
                anomaly_type = "unused_storage"
                desc = f"{name} is a storage account tagged 'Legacy' with no owner"
            else:
                anomaly_type = "untagged_resource"
                desc = f"{name} has no owner tag — cannot attribute cost"

            anomaly = {
                "resource_name": name,
                "type": anomaly_type,
                "severity": "Medium" if curr_avg > 500 else "Low",
                "current_daily_cost_inr": round(curr_avg, 2),
                "baseline_daily_cost_inr": round(base_avg, 2),
                "change_percent": round(((curr_avg - base_avg) / base_avg * 100) if base_avg > 0 else 0, 1),
                "environment": env,
                "description": desc,
                "potential_savings_monthly_inr": round(curr_avg * 30, 2),
            }
        elif base_avg > 0 and curr_avg > base_avg * 1.5:
            anomaly = {
                "resource_name": name,
                "type": "cost_spike",
                "severity": "High",
                "current_daily_cost_inr": round(curr_avg, 2),
                "baseline_daily_cost_inr": round(base_avg, 2),
                "change_percent": round((curr_avg - base_avg) / base_avg * 100, 1),
                "environment": env,
                "description": f"{name} cost increased {round((curr_avg - base_avg) / base_avg * 100)}% vs baseline",
                "potential_savings_monthly_inr": round((curr_avg - base_avg) * 30, 2),
            }

        if anomaly:
            anomalies.append(anomaly)

    return json.dumps({
        "anomalies_detected": len(anomalies),
        "total_potential_monthly_savings_inr": round(sum(a["potential_savings_monthly_inr"] for a in anomalies), 2),
        "anomalies": sorted(anomalies, key=lambda x: x["potential_savings_monthly_inr"], reverse=True),
    }, default=str)


def _check_resource_utilization(args: dict, state: dict) -> str:
    name = args["resource_name"]
    resource = RESOURCE_DB.get(name)
    if not resource:
        return json.dumps({"error": f"Resource '{name}' not found"})

    if resource["type"] != "Microsoft.Compute/virtualMachines":
        return json.dumps({"error": f"Utilization metrics not available for {resource['type']}"})

    period = args.get("period_days", 7)
    cpu = resource.get("cpu_avg_7d", 0)
    mem = resource.get("memory_avg_7d", 0)

    status = "idle" if cpu < 5 else "underutilized" if cpu < 20 else "moderate" if cpu < 60 else "healthy"

    right_size = None
    if status in ("idle", "underutilized"):
        size_map = {"Standard_D4s_v3": "Standard_D2s_v3", "Standard_D8s_v3": "Standard_D4s_v3", "Standard_E8s_v4": "Standard_E4s_v4"}
        right_size = size_map.get(resource["size"])

    return json.dumps({
        "resource_name": name,
        "vm_size": resource["size"],
        "period_days": period,
        "utilization": {
            "cpu_avg_percent": cpu,
            "cpu_max_percent": cpu * 2.1,
            "memory_avg_percent": mem,
            "memory_max_percent": mem * 1.5,
            "network_in_gb": resource.get("network_in_gb_7d", 0),
            "network_out_gb": resource.get("network_out_gb_7d", 0),
        },
        "status": status,
        "recommendation": f"VM is {status}. {'Consider right-sizing to ' + right_size if right_size else 'Current size is appropriate.'}",
        "right_size_suggestion": right_size,
        "estimated_savings_percent": 50 if right_size else 0,
    })


def _get_cost_trend(args: dict, state: dict) -> str:
    df = load_cost_data()
    df["UsageDate"] = pd.to_datetime(df["UsageDate"])
    name = args.get("resource_name", "all")
    days = args.get("days", 14)

    if name != "all":
        df = df[df["ResourceName"] == name]

    daily = df.groupby("UsageDate")["CostINR"].sum().reset_index()
    daily = daily.sort_values("UsageDate").tail(days)

    if len(daily) >= 14:
        week1 = daily.head(7)["CostINR"].sum()
        week2 = daily.tail(7)["CostINR"].sum()
        wow_change = round((week2 - week1) / week1 * 100, 1) if week1 > 0 else 0
    else:
        wow_change = None

    trend_data = [{"date": row["UsageDate"].strftime("%Y-%m-%d"), "cost_inr": round(row["CostINR"], 2)} for _, row in daily.iterrows()]
    avg_daily = daily["CostINR"].mean()

    return json.dumps({
        "resource": name,
        "period_days": days,
        "trend": trend_data,
        "summary": {
            "total_cost_inr": round(daily["CostINR"].sum(), 2),
            "daily_average_inr": round(avg_daily, 2),
            "projected_monthly_inr": round(avg_daily * 30, 2),
            "week_over_week_change_percent": wow_change,
            "trend_direction": "increasing" if wow_change and wow_change > 5 else "decreasing" if wow_change and wow_change < -5 else "stable",
        },
    })


EXECUTED_ACTIONS = []
PENDING_APPROVALS = []


def _execute_remediation(args: dict, state: dict) -> str:
    name = args["resource_name"]
    action = args["action"]
    requires_approval = args.get("requires_approval", False)
    params = args.get("parameters", {})

    resource = RESOURCE_DB.get(name)
    if not resource:
        return json.dumps({"error": f"Resource '{name}' not found"})

    az_commands = {
        "schedule_auto_shutdown": f"az vm auto-shutdown -g {resource.get('location', 'rg-dev-westindia')} -n {name} --time {params.get('shutdown_time', '2000')} --timezone \"{params.get('timezone', 'India Standard Time')}\"",
        "add_tags": f"az resource tag --tags {' '.join(f'{k}={v}' for k, v in params.get('tags', {}).items())} -n {name}",
        "resize_vm": f"az vm resize -g rg-dev-westindia -n {name} --size {params.get('new_size', 'Standard_D2s_v3')}",
        "deallocate_vm": f"az vm deallocate -g rg-dev-westindia -n {name}",
        "delete_disk": f"az disk delete -g rg-dev-westindia -n {name} --yes",
        "snapshot_and_delete": f"az snapshot create -g rg-dev-westindia -n {params.get('snapshot_name', name + '-snap')} --source {name} && az disk delete -g rg-dev-westindia -n {name} --yes",
        "delete_resource": f"az resource delete -n {name} -g rg-dev-westindia",
    }

    safe_actions = {"schedule_auto_shutdown", "add_tags"}

    if requires_approval and action not in safe_actions:
        approval_record = {
            "id": f"approval-{len(PENDING_APPROVALS)+1}",
            "resource_name": name,
            "action": action,
            "az_command": az_commands.get(action, "N/A"),
            "parameters": params,
            "risk_level": "high" if action in ("delete_disk", "delete_resource") else "medium",
            "status": "pending_approval",
            "requested_at": datetime.now().isoformat(),
        }
        PENDING_APPROVALS.append(approval_record)
        return json.dumps({
            "status": "pending_approval",
            "message": f"Action '{action}' on {name} requires human approval before execution.",
            "approval_id": approval_record["id"],
            "az_command": az_commands.get(action),
            "risk_level": approval_record["risk_level"],
        })

    exec_record = {
        "resource_name": name,
        "action": action,
        "az_command": az_commands.get(action, "N/A"),
        "status": "executed_successfully",
        "executed_at": datetime.now().isoformat(),
        "result": f"Successfully applied {action} on {name}",
    }
    EXECUTED_ACTIONS.append(exec_record)

    return json.dumps({
        "status": "executed_successfully",
        "resource_name": name,
        "action": action,
        "az_command": az_commands.get(action),
        "result": exec_record["result"],
        "rollback_command": _get_rollback(action, name, params),
    })


def _get_rollback(action: str, name: str, params: dict) -> str:
    rollbacks = {
        "schedule_auto_shutdown": f"az vm auto-shutdown -g rg-dev-westindia -n {name} --off",
        "add_tags": f"az tag delete --resource-id <resource-id> --name <tag-name>",
        "resize_vm": f"az vm resize -g rg-dev-westindia -n {name} --size <original-size>",
        "deallocate_vm": f"az vm start -g rg-dev-westindia -n {name}",
    }
    return rollbacks.get(action, "Manual rollback required — contact ops team")


def _generate_savings_report(args: dict, state: dict) -> str:
    df = load_cost_data()
    df["UsageDate"] = pd.to_datetime(df["UsageDate"])
    max_date = df["UsageDate"].max()
    current_week = df[df["UsageDate"] > max_date - timedelta(days=7)]
    total_weekly = current_week["CostINR"].sum()

    non_prod = current_week[current_week["Tags_Environment"].isin(["Development", "Staging"])]
    non_prod_weekly = non_prod["CostINR"].sum()

    savings_opportunities = [
        {"category": "Dev/Staging Auto-Shutdown", "monthly_savings_inr": 198000, "confidence": "High", "effort": "Low"},
        {"category": "Orphaned Disk Cleanup", "monthly_savings_inr": 61500, "confidence": "High", "effort": "Low"},
        {"category": "Right-Size Dev VMs", "monthly_savings_inr": 102000, "confidence": "Medium", "effort": "Medium"},
        {"category": "Legacy Storage Decommission", "monthly_savings_inr": 9600, "confidence": "Medium", "effort": "Medium"},
        {"category": "Unused Public IP Removal", "monthly_savings_inr": 5400, "confidence": "High", "effort": "Low"},
    ]

    total_monthly = sum(s["monthly_savings_inr"] for s in savings_opportunities)

    return json.dumps({
        "report_generated_at": datetime.now().isoformat(),
        "current_state": {
            "weekly_spend_inr": round(total_weekly, 2),
            "monthly_projected_inr": round(total_weekly / 7 * 30, 2),
            "non_prod_percent": round(non_prod_weekly / total_weekly * 100, 1),
        },
        "savings_opportunities": savings_opportunities,
        "total_monthly_savings_inr": total_monthly,
        "total_annual_savings_inr": total_monthly * 12,
        "actions_executed": len(EXECUTED_ACTIONS),
        "actions_pending_approval": len(PENDING_APPROVALS),
        "executive_summary": f"Identified ₹{total_monthly:,.0f}/month (₹{total_monthly*12:,.0f}/year) in optimization opportunities. {non_prod_weekly/total_weekly*100:.0f}% of current spend is non-production. Immediate actions (auto-shutdown, tagging) can save ₹{savings_opportunities[0]['monthly_savings_inr']:,.0f}/month with zero risk.",
        "recommendations": [
            "Implement auto-shutdown for all Dev/Staging VMs (8PM-8AM IST weekdays, full weekends)",
            "Snapshot and delete 2 orphaned disks (unattached for 60+ days)",
            "Right-size vm-dev-api-002 from D8s to D4s — only using 8.7% CPU",
            "Decommission stdevunused001 storage account (last access: March 2026)",
            "Enable Azure Cost Management alerts at ₹50,000/week threshold",
            "Implement mandatory tagging policy via Azure Policy to prevent future orphaned resources",
        ],
    })


def _list_pending_approvals(args: dict, state: dict) -> str:
    return json.dumps({
        "pending_count": len(PENDING_APPROVALS),
        "approvals": PENDING_APPROVALS,
    })


def _get_optimization_recommendations(args: dict, state: dict) -> str:
    category = args.get("category", "all")

    recommendations = {
        "right_sizing": [
            {"resource": "vm-dev-api-002", "current_size": "Standard_D8s_v3", "recommended_size": "Standard_D4s_v3", "cpu_utilization": "8.7%", "monthly_savings_inr": 51000, "risk": "low"},
            {"resource": "vm-staging-load-001", "current_size": "Standard_E8s_v4", "recommended_size": "Standard_E4s_v4", "cpu_utilization": "3.2%", "monthly_savings_inr": 69000, "risk": "low"},
        ],
        "scheduling": [
            {"resource": "vm-dev-api-001", "recommendation": "Auto-shutdown 8PM-8AM IST + weekends", "monthly_savings_inr": 63000, "risk": "none"},
            {"resource": "vm-dev-api-002", "recommendation": "Auto-shutdown 8PM-8AM IST + weekends", "monthly_savings_inr": 102000, "risk": "none"},
            {"resource": "vm-staging-load-001", "recommendation": "Deallocate when not running load tests", "monthly_savings_inr": 207000, "risk": "low"},
        ],
        "cleanup": [
            {"resource": "disk-orphaned-001", "recommendation": "Snapshot and delete (unattached 71 days)", "monthly_savings_inr": 25500, "risk": "low"},
            {"resource": "disk-orphaned-002", "recommendation": "Snapshot and delete (unattached 64 days)", "monthly_savings_inr": 36000, "risk": "low"},
            {"resource": "stdevunused001", "recommendation": "Archive to cool storage or delete (last access 98 days ago)", "monthly_savings_inr": 9600, "risk": "medium"},
            {"resource": "pip-unused-001", "recommendation": "Delete (not associated with any resource)", "monthly_savings_inr": 5400, "risk": "none"},
        ],
        "reserved_instances": [
            {"resource": "vm-prod-web-001", "recommendation": "1-year Reserved Instance", "current_monthly_inr": 375000, "ri_monthly_inr": 243750, "monthly_savings_inr": 131250, "commitment": "1 year"},
        ],
        "spot_instances": [
            {"resource": "vm-staging-load-001", "recommendation": "Convert to Spot VM for load testing (interruptible workload)", "monthly_savings_inr": 184000, "risk": "medium"},
        ],
    }

    if category == "all":
        result = recommendations
    else:
        result = {category: recommendations.get(category, [])}

    total_savings = sum(r["monthly_savings_inr"] for recs in result.values() for r in recs)

    return json.dumps({
        "category": category,
        "recommendations": result,
        "total_potential_monthly_savings_inr": total_savings,
        "total_potential_annual_savings_inr": total_savings * 12,
    })


def _list_resources(args: dict, state: dict) -> str:
    """Demo mode: return a message directing to live mode for resource listing."""
    return json.dumps({
        "note": "list_resources is only available in live mode (AZURE_SUBSCRIPTION_ID set in .env). In demo mode, use get_resource_details for individual resource lookup.",
        "hint": "Set AZURE_SUBSCRIPTION_ID in your .env file and ensure azure SDK packages are installed to enable live resource listing.",
    })


def _compare_costs(args: dict, state: dict) -> str:
    """Demo mode cost comparison using CSV data."""
    df = load_cost_data()
    df["UsageDate"] = pd.to_datetime(df["UsageDate"])

    try:
        period1_start = pd.to_datetime(args["period1_start"])
        period1_end = pd.to_datetime(args["period1_end"])
        period2_start = pd.to_datetime(args["period2_start"])
        period2_end = pd.to_datetime(args["period2_end"])
    except Exception as e:
        return json.dumps({"error": f"Invalid date format. Use YYYY-MM-DD: {str(e)}"})

    group_by = args.get("group_by", "resource")
    min_threshold = args.get("min_change_threshold", 100)

    group_col = {
        "resource": "ResourceName",
        "resource_group": "ResourceGroup",
        "service": "ServiceName",
        "environment": "Tags_Environment",
    }.get(group_by, "ResourceName")

    # Filter data for each period
    period1_df = df[(df["UsageDate"] >= period1_start) & (df["UsageDate"] <= period1_end)]
    period2_df = df[(df["UsageDate"] >= period2_start) & (df["UsageDate"] <= period2_end)]

    # Aggregate costs
    period1_costs = period1_df.groupby(group_col)["CostINR"].sum().to_dict()
    period2_costs = period2_df.groupby(group_col)["CostINR"].sum().to_dict()

    # Calculate changes
    all_keys = set(period1_costs.keys()) | set(period2_costs.keys())
    changes = []

    for key in all_keys:
        cost1 = period1_costs.get(key, 0)
        cost2 = period2_costs.get(key, 0)
        diff = cost2 - cost1

        if abs(diff) < min_threshold:
            continue

        change_record = {
            "resource": key,
            "period1_cost": round(cost1, 2),
            "period2_cost": round(cost2, 2),
            "change_amount": round(diff, 2),
            "change_percent": round((diff / cost1 * 100) if cost1 > 0 else 0, 1),
        }

        if cost1 == 0:
            change_record["status"] = "new_resource"
        elif cost2 == 0:
            change_record["status"] = "removed_resource"
        elif diff > 0:
            change_record["status"] = "increased"
        else:
            change_record["status"] = "decreased"

        changes.append(change_record)

    changes.sort(key=lambda x: abs(x["change_amount"]), reverse=True)

    period1_total = sum(period1_costs.values())
    period2_total = sum(period2_costs.values())
    total_change = period2_total - period1_total
    total_change_pct = (total_change / period1_total * 100) if period1_total > 0 else 0

    # Generate insights
    insights = []
    if total_change > 0:
        insights.append(f"Overall cost INCREASED by ₹{round(abs(total_change), 2)} ({abs(total_change_pct):.1f}%)")
    else:
        insights.append(f"Overall cost DECREASED by ₹{round(abs(total_change), 2)} ({abs(total_change_pct):.1f}%)")

    new_resources = [c for c in changes if c["status"] == "new_resource"]
    removed_resources = [c for c in changes if c["status"] == "removed_resource"]
    increased = [c for c in changes if c["status"] == "increased"]
    decreased = [c for c in changes if c["status"] == "decreased"]

    if new_resources:
        new_total = sum(c["period2_cost"] for c in new_resources)
        insights.append(f"{len(new_resources)} new resources added, costing ₹{round(new_total, 2)}")

    if removed_resources:
        removed_total = sum(c["period1_cost"] for c in removed_resources)
        insights.append(f"{len(removed_resources)} resources removed, saving ₹{round(removed_total, 2)}")

    if increased:
        increased_total = sum(c["change_amount"] for c in increased)
        insights.append(f"{len(increased)} resources increased costs by ₹{round(increased_total, 2)}")

    if decreased:
        decreased_total = sum(abs(c["change_amount"]) for c in decreased)
        insights.append(f"{len(decreased)} resources decreased costs by ₹{round(decreased_total, 2)}")

    return json.dumps({
        "comparison": {
            "period1": {
                "start": args["period1_start"],
                "end": args["period1_end"],
                "total_cost": round(period1_total, 2),
            },
            "period2": {
                "start": args["period2_start"],
                "end": args["period2_end"],
                "total_cost": round(period2_total, 2),
            },
            "change": {
                "amount": round(total_change, 2),
                "percent": round(total_change_pct, 1),
                "direction": "increase" if total_change > 0 else "decrease",
            },
        },
        "summary": {
            "total_resources_compared": len(all_keys),
            "significant_changes": len(changes),
            "new_resources": len(new_resources),
            "removed_resources": len(removed_resources),
            "increased_resources": len(increased),
            "decreased_resources": len(decreased),
        },
        "insights": insights,
        "top_increases": increased[:5],
        "top_new_resources": new_resources[:5],
        "all_changes": changes[:50],
    }, default=str)


def _get_role_assignments(args: dict, state: dict) -> str:
    """Demo mode: return a message directing to live mode for role assignments."""
    return json.dumps({
        "note": "get_role_assignments is only available in live mode (AZURE_SUBSCRIPTION_ID set in .env). In demo mode, role assignment queries cannot be processed.",
        "hint": "Set AZURE_SUBSCRIPTION_ID in your .env file and ensure azure-mgmt-authorization package is installed to enable role assignment queries.",
    })


def _assign_role(args: dict, state: dict) -> str:
    """Demo mode: return a message directing to live mode for role assignment."""
    return json.dumps({
        "note": "assign_role is only available in live mode (AZURE_SUBSCRIPTION_ID set in .env).",
        "hint": "Set AZURE_SUBSCRIPTION_ID in your .env file and ensure azure-mgmt-authorization package is installed.",
    })
