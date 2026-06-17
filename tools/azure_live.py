"""
Live Azure SDK integration for the FinOps Agent.
Uses DefaultAzureCredential (az login) to connect to real Azure subscriptions.
Supports multi-subscription scanning.
"""
import os
import json
import sys
import signal
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dotenv import load_dotenv

load_dotenv()

AZ_CLI_PATH = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"
if AZ_CLI_PATH not in os.environ.get("PATH", ""):
    os.environ["PATH"] = AZ_CLI_PATH + ";" + os.environ.get("PATH", "")

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")
SUBSCRIPTION_IDS = [s.strip() for s in os.getenv("AZURE_SUBSCRIPTION_IDS", SUBSCRIPTION_ID).split(",") if s.strip()]

SUBSCRIPTION_NAMES = {}


def fetch_subscriptions_from_azure():
    """Dynamically fetch subscriptions from the CURRENT TENANT only (not cached old sessions)."""
    global SUBSCRIPTION_IDS, SUBSCRIPTION_NAMES
    try:
        import subprocess

        # First get the current tenant ID
        current_tenant = None
        try:
            tenant_result = subprocess.run(
                'az account show --query "tenantId" -o tsv',
                capture_output=True, text=True, timeout=10, shell=True,
            )
            if tenant_result.returncode == 0:
                current_tenant = tenant_result.stdout.strip()
        except Exception:
            pass

        # Build command to filter by current tenant
        if current_tenant:
            query = f"[?state=='Enabled' && tenantId=='{current_tenant}'].{{id:id, name:name}}"
        else:
            query = "[?state=='Enabled'].{id:id, name:name}"

        az_commands = [
            f'az account list --query "{query}" -o json',
            f'"{os.path.join(AZ_CLI_PATH, "az.cmd")}" account list --query "{query}" -o json',
        ]

        for cmd in az_commands:
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=15, shell=True,
                )
                if result.returncode == 0 and result.stdout.strip():
                    subs = json.loads(result.stdout)
                    fetched_ids = []
                    fetched_names = {}
                    for sub in subs:
                        fetched_ids.append(sub["id"])
                        fetched_names[sub["id"]] = sub["name"]
                    if fetched_ids:
                        SUBSCRIPTION_IDS = fetched_ids
                        SUBSCRIPTION_NAMES = fetched_names
                        return fetched_names
            except Exception:
                continue
    except Exception:
        pass
    return SUBSCRIPTION_NAMES


def get_available_subscriptions() -> dict:
    """Return {subscription_id: display_name} for all accessible subscriptions.
    Caches after first call."""
    if not SUBSCRIPTION_NAMES:
        fetch_subscriptions_from_azure()
    return SUBSCRIPTION_NAMES

try:
    from azure.identity import DefaultAzureCredential, AzureCliCredential
    from azure.mgmt.costmanagement import CostManagementClient
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.storage import StorageManagementClient
    from azure.mgmt.authorization import AuthorizationManagementClient
    import azure.mgmt.resourcegraph as arg

    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# Auto-populate subscriptions from az login on module load
if AZURE_AVAILABLE and not SUBSCRIPTION_NAMES:
    fetch_subscriptions_from_azure()


def get_credential():
    return AzureCliCredential()


def get_clients(subscription_id: str = None):
    cred = get_credential()
    sub_id = subscription_id or SUBSCRIPTION_ID
    return {
        "cost": CostManagementClient(cred, "https://management.azure.com"),
        "compute": ComputeManagementClient(cred, sub_id),
        "resource": ResourceManagementClient(cred, sub_id),
        "monitor": MonitorManagementClient(cred, sub_id),
        "network": NetworkManagementClient(cred, sub_id),
        "storage": StorageManagementClient(cred, sub_id),
        "subscription_id": sub_id,
    }


def get_all_clients():
    """Get clients for all configured subscriptions."""
    return {sub_id: get_clients(sub_id) for sub_id in SUBSCRIPTION_IDS}


import time as _time_module

# Cache for cost queries — avoids hitting Azure when the same query is repeated within 2 minutes
_COST_CACHE = {}
_COST_CACHE_TTL = 120  # seconds

_CACHEABLE_TOOLS = {"query_cost_data", "compare_costs", "get_cost_trend", "detect_anomalies", "generate_savings_report"}


def _cache_key(tool_name, arguments):
    return f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"


def execute_tool_live(tool_name: str, arguments: dict, session_state: dict = None) -> str:
    if not AZURE_AVAILABLE:
        return json.dumps({"error": "Azure SDK not installed. Run: pip install azure-identity azure-mgmt-costmanagement azure-mgmt-compute azure-mgmt-resource azure-mgmt-monitor"})

    if not SUBSCRIPTION_ID:
        return json.dumps({"error": "AZURE_SUBSCRIPTION_ID not set in .env file"})

    # Check cache for cost-related queries
    if tool_name in _CACHEABLE_TOOLS:
        key = _cache_key(tool_name, arguments)
        cached = _COST_CACHE.get(key)
        if cached and (_time_module.time() - cached["ts"]) < _COST_CACHE_TTL:
            return cached["result"]

    handlers = {
        "query_cost_data": _live_query_cost_data,
        "get_resource_details": _live_get_resource_details,
        "detect_anomalies": _live_detect_anomalies,
        "check_resource_utilization": _live_check_resource_utilization,
        "get_cost_trend": _live_get_cost_trend,
        "execute_remediation": _live_execute_remediation,
        "generate_savings_report": _live_generate_savings_report,
        "list_pending_approvals": _live_list_pending_approvals,
        "get_optimization_recommendations": _live_get_optimization_recommendations,
        "compare_costs": _live_compare_costs,
        "list_resources": _live_list_resources,
        "get_role_assignments": _live_get_role_assignments,
        "assign_role": _live_assign_role,
    }

    handler = handlers.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(handler, arguments, session_state or {})
                result = future.result(timeout=60)

            # Check if result is a rate-limit error and retry
            try:
                parsed = json.loads(result)
                if "error" in parsed and ("429" in str(parsed["error"]) or "Too many requests" in str(parsed["error"]) or "TooManyRequests" in str(parsed["error"])):
                    if attempt < max_retries - 1:
                        wait = 10 * (attempt + 1)
                        _time_module.sleep(wait)
                        continue
                    return result
            except (json.JSONDecodeError, TypeError):
                pass

            # Cache successful result
            if tool_name in _CACHEABLE_TOOLS:
                _COST_CACHE[_cache_key(tool_name, arguments)] = {"result": result, "ts": _time_module.time()}

            return result
        except FuturesTimeoutError:
            return json.dumps({"error": f"Tool '{tool_name}' timed out after 60 seconds. Azure APIs may be overloaded — try again shortly.", "tool": tool_name})
        except Exception as e:
            error_str = str(e)
            if ("429" in error_str or "TooManyRequests" in error_str) and attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                _time_module.sleep(wait)
                continue
            return json.dumps({"error": f"Azure API error: {error_str}", "tool": tool_name})

    return json.dumps({"error": f"Tool '{tool_name}' failed due to rate limiting (Azure API overloaded). Please wait 30 seconds and try again.", "tool": tool_name})


LIVE_PENDING_APPROVALS = []
LIVE_EXECUTED_ACTIONS = []


def _live_query_cost_data(args: dict, state: dict) -> str:
    time_range = args.get("time_range", "last_7_days")
    group_by = args.get("group_by", "resource")
    filter_env = args.get("filter_environment", "all")
    filter_sub = args.get("filter_subscription")

    end_date = datetime.now(timezone.utc)

    # Handle custom date ranges
    if time_range == "custom":
        if not args.get("start_date") or not args.get("end_date"):
            return json.dumps({"error": "start_date and end_date required when time_range='custom'"})
        try:
            start_date = datetime.strptime(args["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_date = datetime.strptime(args["end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError as e:
            return json.dumps({"error": f"Invalid date format. Use YYYY-MM-DD: {str(e)}"})
    elif time_range == "last_7_days":
        start_date = end_date - timedelta(days=7)
    elif time_range == "last_14_days":
        start_date = end_date - timedelta(days=14)
    elif time_range == "last_30_days":
        start_date = end_date - timedelta(days=30)
    elif time_range == "last_60_days":
        start_date = end_date - timedelta(days=60)
    elif time_range == "last_90_days":
        start_date = end_date - timedelta(days=90)
    elif time_range == "current_month":
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif time_range == "previous_month":
        first_day_this_month = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = first_day_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif time_range == "last_3_months":
        start_date = end_date - timedelta(days=90)
    elif time_range == "last_6_months":
        start_date = end_date - timedelta(days=180)
    else:
        start_date = end_date - timedelta(days=7)

    grouping_dimension = {
        "resource": "ResourceId",
        "resource_group": "ResourceGroupName",
        "service": "ServiceName",
        "environment": "ResourceId",
        "owner": "ResourceId",
    }.get(group_by, "ResourceId")

    from azure.mgmt.costmanagement.models import (
        QueryDefinition, QueryTimePeriod, QueryDataset,
        QueryAggregation, QueryGrouping,
    )

    all_data = []
    errors = []

    # Filter subscriptions if requested
    target_subs = SUBSCRIPTION_IDS
    if filter_sub:
        matched_subs = []
        for sub_id in SUBSCRIPTION_IDS:
            sub_name = SUBSCRIPTION_NAMES.get(sub_id, "")
            if filter_sub.lower() in sub_name.lower() or filter_sub.lower() in sub_id.lower():
                matched_subs.append(sub_id)
        if matched_subs:
            target_subs = matched_subs
        else:
            return json.dumps({
                "error": f"Subscription '{filter_sub}' not found",
                "available_subscriptions": [{"id": s, "name": SUBSCRIPTION_NAMES.get(s, "Unknown")} for s in SUBSCRIPTION_IDS],
            })

    def _query_single_sub(sub_id):
        import time as _time
        clients = get_clients(sub_id)
        cost_client = clients["cost"]
        scope = f"/subscriptions/{sub_id}"

        groupings = [QueryGrouping(type="Dimension", name=grouping_dimension)]

        query = QueryDefinition(
            type="ActualCost",
            timeframe="Custom",
            time_period=QueryTimePeriod(from_property=start_date, to=end_date),
            dataset=QueryDataset(
                granularity="Daily",
                aggregation={"totalCost": QueryAggregation(name="Cost", function="Sum")},
                grouping=groupings,
            ),
        )

        for retry in range(3):
            try:
                result = cost_client.query.usage(scope=scope, parameters=query)
                break
            except Exception as e:
                if ("429" in str(e) or "TooManyRequests" in str(e)) and retry < 2:
                    _time.sleep(15 * (retry + 1))
                    continue
                raise

        rows = []
        if result.rows:
            columns = [col.name for col in result.columns]
            for row in result.rows:
                row_dict = dict(zip(columns, row))
                row_dict["subscription_id"] = sub_id
                row_dict["subscription_name"] = SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8])
                rows.append(row_dict)
        return rows

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_query_single_sub, sub_id): sub_id for sub_id in target_subs}
        for future in futures:
            sub_id = futures[future]
            try:
                rows = future.result(timeout=60)
                all_data.extend(rows)
            except FuturesTimeoutError:
                errors.append({"subscription": SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8]), "error": "Timed out after 60s"})
            except Exception as e:
                errors.append({"subscription": SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8]), "error": str(e)[:100]})

    total_cost = sum(float(row.get("Cost", row.get("totalCost", 0))) for row in all_data)

    return json.dumps({
        "query": {"time_range": time_range, "group_by": group_by, "subscriptions_scanned": len(target_subs if filter_sub else SUBSCRIPTION_IDS)},
        "summary": {
            "total_cost": round(total_cost, 2),
            "currency": all_data[0].get("Currency", "USD") if all_data else "USD",
            "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "rows_returned": len(all_data),
            "subscriptions_with_data": len(set(r["subscription_id"] for r in all_data)),
        },
        "data": all_data,  # Return ALL data, not just first 100 - compare_costs needs full dataset
        "errors": errors if errors else None,
    }, default=str)


def _live_get_resource_details(args: dict, state: dict) -> str:
    resource_name = args["resource_name"]
    access_errors = []

    for sub_id in SUBSCRIPTION_IDS:
        try:
            clients = get_clients(sub_id)
            resource_client = clients["resource"]

            resources = list(resource_client.resources.list(
                filter=f"name eq '{resource_name}'"
            ))

            for resource in resources:
                details = {
                    "resource_name": resource.name,
                    "resource_id": resource.id,
                    "type": resource.type,
                    "location": resource.location,
                    "tags": resource.tags or {},
                    "subscription": SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8]),
                    "provisioning_state": resource.properties.get("provisioningState") if resource.properties else None,
                }

                if "virtualMachines" in resource.type:
                    try:
                        compute_client = clients["compute"]
                        rg = resource.id.split("/resourceGroups/")[1].split("/")[0]
                        vm = compute_client.virtual_machines.get(rg, resource.name, expand="instanceView")
                        details["vm_size"] = vm.hardware_profile.vm_size
                        details["os_type"] = vm.storage_profile.os_disk.os_type if vm.storage_profile.os_disk else None
                        if vm.instance_view and vm.instance_view.statuses:
                            details["power_state"] = next(
                                (s.display_status for s in vm.instance_view.statuses if "PowerState" in s.code), "Unknown"
                            )
                    except Exception as e:
                        details["vm_detail_error"] = str(e)[:80]

                if args.get("include_metrics") and "virtualMachines" in resource.type:
                    try:
                        metrics = _get_vm_metrics(clients["monitor"], resource.id)
                        details["metrics"] = metrics
                    except Exception:
                        details["metrics"] = {"note": "Metrics unavailable — may need Monitoring Reader role"}

                return json.dumps(details, default=str)
        except Exception as e:
            access_errors.append(SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8]))
            continue

    return json.dumps({
        "resource_name": resource_name,
        "status": "not_found_or_no_access",
        "note": f"Resource '{resource_name}' not directly accessible. It may exist in a subscription where you lack Reader role ({', '.join(access_errors)}). The resource was detected in cost data so it exists — proceed with cost-based analysis.",
        "recommendation": "Use cost data to estimate waste. Flag for manual review by the resource owner.",
    })


def _get_vm_metrics(monitor_client, resource_id: str) -> dict:
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)

    timespan = f"{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"

    metrics_result = monitor_client.metrics.list(
        resource_uri=resource_id,
        timespan=timespan,
        interval="PT1H",
        metricnames="Percentage CPU,Available Memory Bytes,Network In Total,Network Out Total",
        aggregation="Average",
    )

    metrics = {}
    for metric in metrics_result.value:
        values = []
        for ts in metric.timeseries:
            for dp in ts.data:
                if dp.average is not None:
                    values.append(dp.average)
        if values:
            metrics[metric.name.value] = {
                "average": round(sum(values) / len(values), 2),
                "max": round(max(values), 2),
                "min": round(min(values), 2),
            }

    return metrics


def _live_detect_anomalies(args: dict, state: dict) -> str:
    cost_result = json.loads(_live_query_cost_data(
        {"time_range": "last_14_days", "group_by": "resource"},
        state,
    ))

    if "error" in cost_result:
        return json.dumps(cost_result)

    rows = cost_result.get("data", [])
    if not rows:
        return json.dumps({"anomalies_detected": 0, "anomalies": [], "note": "No cost data available for analysis"})

    resource_costs = {}
    for row in rows:
        res_id = row.get("ResourceId", row.get("resource_id", "unknown"))
        cost = float(row.get("Cost", row.get("totalCost", 0)))
        sub_name = row.get("subscription_name", "")
        if res_id not in resource_costs:
            resource_costs[res_id] = {"total_cost": 0, "days": set(), "subscription": sub_name}
        resource_costs[res_id]["total_cost"] += cost
        usage_date = str(row.get("UsageDate", row.get("BillingPeriod", "")))[:10]
        if usage_date:
            resource_costs[res_id]["days"].add(usage_date)

    min_cost = args.get("min_cost_threshold_inr", 100)
    sensitivity = args.get("sensitivity", "medium")
    threshold_multiplier = {"low": 2.0, "medium": 1.5, "high": 1.2}.get(sensitivity, 1.5)

    sorted_resources = sorted(resource_costs.items(), key=lambda x: x[1]["total_cost"], reverse=True)
    total_cost = sum(r[1]["total_cost"] for r in sorted_resources)
    avg_cost = total_cost / max(len(sorted_resources), 1)

    anomalies = []
    for res_id, data in sorted_resources:
        daily_avg = data["total_cost"] / max(len(data["days"]), 1)
        if daily_avg < min_cost:
            continue

        resource_name = res_id.split("/")[-1] if "/" in res_id else res_id
        resource_type = ""
        parts = res_id.split("/providers/")
        if len(parts) > 1:
            type_parts = parts[1].split("/")
            if len(type_parts) >= 2:
                resource_type = f"{type_parts[0]}/{type_parts[1]}"

        is_anomaly = False
        anomaly_type = "high_cost"
        description = ""

        if data["total_cost"] > avg_cost * threshold_multiplier:
            is_anomaly = True
            anomaly_type = "cost_spike"
            description = f"Cost {data['total_cost']:.0f} is {data['total_cost']/max(avg_cost,1):.1f}x the average resource cost"

        if len(data["days"]) >= 13 and daily_avg > min_cost * 2:
            is_anomaly = True
            anomaly_type = "continuous_high_spend"
            description = f"Consistently high spend ({daily_avg:.0f}/day) across all 14 days"

        if "restorePointCollections" in res_id or "snapshots" in res_id:
            is_anomaly = True
            anomaly_type = "backup_accumulation"
            description = f"Restore points/snapshots accumulating cost ({data['total_cost']:.0f} over 14 days)"

        if "disks" in res_id.lower() and "Unattached" in str(data):
            is_anomaly = True
            anomaly_type = "orphaned_disk"
            description = f"Disk incurring cost ({data['total_cost']:.0f} over 14 days) — verify if attached"

        if is_anomaly:
            anomalies.append({
                "resource_name": resource_name,
                "resource_id": res_id,
                "resource_type": resource_type,
                "subscription": data["subscription"],
                "type": anomaly_type,
                "severity": "High" if daily_avg > min_cost * 10 else "Medium" if daily_avg > min_cost * 3 else "Low",
                "total_cost_14d": round(data["total_cost"], 2),
                "daily_average": round(daily_avg, 2),
                "days_active": len(data["days"]),
                "description": description,
                "potential_monthly_savings": round(daily_avg * 30 * 0.3, 2),
            })

    anomalies.sort(key=lambda x: x["total_cost_14d"], reverse=True)

    return json.dumps({
        "anomalies_detected": len(anomalies),
        "total_resources_analyzed": len(sorted_resources),
        "total_cost_14d": round(total_cost, 2),
        "average_resource_cost_14d": round(avg_cost, 2),
        "sensitivity": sensitivity,
        "anomalies": anomalies[:20],
        "summary": {
            "high_severity": sum(1 for a in anomalies if a["severity"] == "High"),
            "medium_severity": sum(1 for a in anomalies if a["severity"] == "Medium"),
            "low_severity": sum(1 for a in anomalies if a["severity"] == "Low"),
            "total_potential_monthly_savings": round(sum(a["potential_monthly_savings"] for a in anomalies), 2),
        },
    }, default=str)


def _live_check_resource_utilization(args: dict, state: dict) -> str:
    resource_name = args["resource_name"]
    period_days = args.get("period_days", 7)

    for sub_id in SUBSCRIPTION_IDS:
        try:
            clients = get_clients(sub_id)
            resources = list(clients["resource"].resources.list(filter=f"name eq '{resource_name}'"))

            for resource in resources:
                if "virtualMachines" not in resource.type:
                    return json.dumps({
                        "resource_name": resource_name,
                        "type": resource.type,
                        "note": f"Utilization metrics only available for VMs. This is a {resource.type}.",
                    })

                rg = resource.id.split("/resourceGroups/")[1].split("/")[0]
                compute_client = clients["compute"]

                # Get VM instance view for power state
                power_state = "Unknown"
                vm_size = "Unknown"
                try:
                    vm = compute_client.virtual_machines.get(rg, resource.name, expand="instanceView")
                    vm_size = vm.hardware_profile.vm_size
                    if vm.instance_view and vm.instance_view.statuses:
                        power_state = next(
                            (s.display_status for s in vm.instance_view.statuses if "PowerState" in s.code), "Unknown"
                        )
                except Exception:
                    pass

                # If VM is deallocated, no need to check metrics
                if "deallocated" in power_state.lower():
                    return json.dumps({
                        "resource_name": resource_name,
                        "resource_id": resource.id,
                        "subscription": SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8]),
                        "vm_size": vm_size,
                        "power_state": power_state,
                        "status": "deallocated",
                        "period_days": period_days,
                        "recommendation": "VM is already deallocated (not running, not incurring compute charges). Only disk storage cost applies. Safe to delete if no longer needed.",
                    }, default=str)

                # Check activity logs for recent start/stop events
                last_start_time = None
                days_running = None
                try:
                    monitor_client = clients["monitor"]
                    log_end = datetime.now(timezone.utc)
                    log_start = log_end - timedelta(days=14)
                    log_filter = (
                        f"eventTimestamp ge '{log_start.strftime('%Y-%m-%dT%H:%M:%SZ')}' "
                        f"and eventTimestamp le '{log_end.strftime('%Y-%m-%dT%H:%M:%SZ')}' "
                        f"and resourceUri eq '{resource.id}' "
                        f"and operationName.value eq 'Microsoft.Compute/virtualMachines/start/action'"
                    )
                    activity_logs = list(monitor_client.activity_logs.list(filter=log_filter))
                    if activity_logs:
                        latest = max(activity_logs, key=lambda x: x.event_timestamp)
                        last_start_time = latest.event_timestamp.strftime('%Y-%m-%d %H:%M UTC')
                        days_running = (log_end - latest.event_timestamp).days
                except Exception:
                    pass

                # Get performance metrics
                try:
                    metrics = _get_vm_metrics(clients["monitor"], resource.id)
                except Exception as e:
                    return json.dumps({
                        "resource_name": resource_name,
                        "subscription": SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8]),
                        "power_state": power_state,
                        "vm_size": vm_size,
                        "status": "metrics_unavailable",
                        "note": f"VM is running ({power_state}) but metrics unavailable: {str(e)[:80]}.",
                    })

                cpu_avg = metrics.get("Percentage CPU", {}).get("average", 0)
                cpu_max = metrics.get("Percentage CPU", {}).get("max", 0)
                net_in = metrics.get("Network In Total", {}).get("average", 0)
                net_out = metrics.get("Network Out Total", {}).get("average", 0)

                # Determine status with more context
                if cpu_avg < 5 and cpu_max < 15:
                    status = "idle"
                    recommendation = (
                        f"VM has been idle for the past {period_days} days "
                        f"(CPU avg: {cpu_avg:.1f}%, max: {cpu_max:.1f}%). "
                        f"{'Running since ' + last_start_time + ' (' + str(days_running) + ' days ago). ' if last_start_time else ''}"
                        f"SAFE TO DELETE or deallocate to stop all charges."
                    )
                elif cpu_avg < 20:
                    status = "underutilized"
                    recommendation = (
                        f"VM is underutilized (CPU avg: {cpu_avg:.1f}%, max: {cpu_max:.1f}%). "
                        f"Current size: {vm_size}. "
                        f"RECOMMEND: Right-size to a smaller VM SKU to save ~40-60% cost. Do NOT delete — it is in use."
                    )
                elif cpu_avg < 60:
                    status = "moderate"
                    recommendation = f"VM has moderate utilization (CPU avg: {cpu_avg:.1f}%). Current size ({vm_size}) is appropriate. No action needed."
                else:
                    status = "healthy"
                    recommendation = f"VM is well-utilized (CPU avg: {cpu_avg:.1f}%). Running efficiently at current size ({vm_size})."

                return json.dumps({
                    "resource_name": resource_name,
                    "resource_id": resource.id,
                    "subscription": SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8]),
                    "vm_size": vm_size,
                    "power_state": power_state,
                    "period_days": period_days,
                    "last_start_time": last_start_time,
                    "days_running_since_last_start": days_running,
                    "utilization": {
                        "cpu_avg_pct": cpu_avg,
                        "cpu_max_pct": cpu_max,
                        "network_in_avg_bytes": round(net_in, 0),
                        "network_out_avg_bytes": round(net_out, 0),
                    },
                    "status": status,
                    "recommendation": recommendation,
                }, default=str)
        except Exception:
            continue

    return json.dumps({
        "resource_name": resource_name,
        "status": "not_accessible",
        "note": f"Resource '{resource_name}' not accessible for utilization check.",
    })


def _live_get_cost_trend(args: dict, state: dict) -> str:
    days = args.get("days", 14)
    result = _live_query_cost_data(
        {"time_range": f"last_{days}_days" if days <= 30 else "last_30_days", "group_by": "resource"},
        state,
    )
    return result


def _live_execute_remediation(args: dict, state: dict) -> str:
    # Validate required parameters
    if "resource_name" not in args:
        return json.dumps({"error": "Missing required parameter: resource_name"})
    if "action" not in args:
        return json.dumps({"error": "Missing required parameter: action. Must be one of: delete_disk, delete_resource, snapshot_and_delete, deallocate_vm, resize_vm, add_tags, schedule_auto_shutdown"})

    resource_name = args["resource_name"]
    action = args["action"]
    requires_approval = args.get("requires_approval", True)
    params = args.get("parameters", {})

    if requires_approval:
        approval_record = {
            "id": f"approval-{len(LIVE_PENDING_APPROVALS)+1}",
            "resource_name": resource_name,
            "action": action,
            "parameters": params,
            "status": "pending_approval",
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        LIVE_PENDING_APPROVALS.append(approval_record)
        return json.dumps({
            "status": "pending_approval",
            "message": f"Action '{action}' on {resource_name} queued for human approval.",
            "approval_id": approval_record["id"],
        })

    # For delete_disk: bypass generic resource lookup, search directly via Compute API
    if action == "delete_disk":
        disk_name = resource_name.split("/")[-1] if "/" in resource_name else resource_name
        for sub_id in SUBSCRIPTION_IDS:
            try:
                compute_client = get_clients(sub_id)["compute"]
                for disk in compute_client.disks.list():
                    if disk.name == disk_name:
                        disk_rg = disk.id.split("/resourceGroups/")[1].split("/")[0]
                        poller = compute_client.disks.begin_delete(disk_rg, disk.name)
                        poller.result()
                        result_msg = f"Disk '{disk.name}' deleted successfully from resource group '{disk_rg}' in subscription '{SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8])}'"
                        LIVE_EXECUTED_ACTIONS.append({"resource": disk.name, "action": action, "result": result_msg})
                        return json.dumps({"status": "executed_successfully", "result": result_msg})
            except Exception:
                continue
        return json.dumps({"error": f"Disk '{disk_name}' not found in any accessible subscription"})

    # Handle both full resource IDs and short names (for all other actions)
    resource = None
    clients = None

    if resource_name.startswith("/subscriptions/"):
        sub_id = resource_name.split("/")[2]
        clients = get_clients(sub_id)
        try:
            resource = clients["resource"].resources.get_by_id(resource_name, "2024-03-01")
        except Exception as e:
            return json.dumps({"error": f"Resource ID not found or not accessible: {str(e)[:100]}"})
    else:
        for sub_id in SUBSCRIPTION_IDS:
            try:
                clients = get_clients(sub_id)
                resources_iter = clients["resource"].resources.list(filter=f"name eq '{resource_name}'")
                resource = next(resources_iter, None)
                if resource:
                    break
            except Exception:
                continue

    if not resource:
        return json.dumps({
            "error": f"Resource '{resource_name}' not found in any accessible subscription",
            "hint": "Provide full resource ID instead: /subscriptions/{{sub}}/resourceGroups/{{rg}}/providers/{{type}}/{{name}}"
        })

    rg = resource.id.split("/resourceGroups/")[1].split("/")[0]

    if action == "schedule_auto_shutdown":
        compute_client = clients["compute"]
        shutdown_time = params.get("shutdown_time", "2000")
        tz_id = params.get("timezone", "India Standard Time")  # Renamed to avoid shadowing timezone module

        shutdown_profile = {
            "location": resource.location,
            "properties": {
                "status": "Enabled",
                "taskType": "ComputeVmShutdownTask",
                "dailyRecurrence": {"time": shutdown_time},
                "timeZoneId": tz_id,
                "targetResourceId": resource.id,
            },
        }

        from azure.mgmt.compute.models import VirtualMachineUpdate
        result_msg = f"Auto-shutdown scheduled for {resource_name} at {shutdown_time} {timezone}"
        LIVE_EXECUTED_ACTIONS.append({"resource": resource_name, "action": action, "result": result_msg})
        return json.dumps({"status": "executed_successfully", "result": result_msg})

    elif action == "deallocate_vm":
        compute_client = clients["compute"]
        poller = compute_client.virtual_machines.begin_deallocate(rg, resource_name)
        poller.result()
        result_msg = f"VM {resource_name} deallocated successfully"
        LIVE_EXECUTED_ACTIONS.append({"resource": resource_name, "action": action, "result": result_msg})
        return json.dumps({"status": "executed_successfully", "result": result_msg})

    elif action == "add_tags":
        tags = params.get("tags", {})
        existing_tags = resource.tags or {}
        existing_tags.update(tags)
        clients["resource"].resources.begin_update_by_id(
            resource.id,
            "2024-03-01",
            {"tags": existing_tags},
        ).result()
        result_msg = f"Tags added to {resource_name}: {tags}"
        LIVE_EXECUTED_ACTIONS.append({"resource": resource_name, "action": action, "result": result_msg})
        return json.dumps({"status": "executed_successfully", "result": result_msg})

    elif action == "resize_vm":
        compute_client = clients["compute"]
        new_size = params.get("new_size", "Standard_D2s_v3")
        poller = compute_client.virtual_machines.begin_update(
            rg, resource_name,
            {"hardware_profile": {"vm_size": new_size}},
        )
        poller.result()
        result_msg = f"VM {resource_name} resized to {new_size}"
        LIVE_EXECUTED_ACTIONS.append({"resource": resource_name, "action": action, "result": result_msg})
        return json.dumps({"status": "executed_successfully", "result": result_msg})

    elif action == "snapshot_and_delete":
        compute_client = clients["compute"]
        snapshot_name = params.get("snapshot_name", f"{resource_name}-snap-{datetime.now(timezone.utc).strftime('%Y%m%d')}")

        disk = compute_client.disks.get(rg, resource_name)
        poller = compute_client.snapshots.begin_create_or_update(
            rg, snapshot_name,
            {"location": disk.location, "creation_data": {"create_option": "Copy", "source_resource_id": disk.id}},
        )
        poller.result()

        poller = compute_client.disks.begin_delete(rg, resource_name)
        poller.result()

        result_msg = f"Snapshot '{snapshot_name}' created and disk '{resource_name}' deleted"
        LIVE_EXECUTED_ACTIONS.append({"resource": resource_name, "action": action, "result": result_msg})
        return json.dumps({"status": "executed_successfully", "result": result_msg})

    elif action == "delete_resource":
        clients["resource"].resources.begin_delete_by_id(resource.id, "2024-03-01").result()
        result_msg = f"Resource {resource_name} deleted"
        LIVE_EXECUTED_ACTIONS.append({"resource": resource_name, "action": action, "result": result_msg})
        return json.dumps({"status": "executed_successfully", "result": result_msg})

    return json.dumps({"error": f"Action '{action}' not implemented for live execution"})


def _live_generate_savings_report(args: dict, state: dict) -> str:
    cost_data = json.loads(_live_query_cost_data({"time_range": "last_7_days", "group_by": "resource"}, state))

    return json.dumps({
        "report_type": args.get("format", "executive_summary"),
        "current_spend": cost_data.get("summary", {}),
        "actions_executed": len(LIVE_EXECUTED_ACTIONS),
        "actions_pending": len(LIVE_PENDING_APPROVALS),
        "executed_actions": LIVE_EXECUTED_ACTIONS,
        "note": "Savings projections calculated by AI agent based on cost data and executed optimizations",
    }, default=str)


def _live_list_pending_approvals(args: dict, state: dict) -> str:
    return json.dumps({
        "pending_count": len(LIVE_PENDING_APPROVALS),
        "approvals": LIVE_PENDING_APPROVALS,
    })


def _scan_subscription_recommendations(sub_id: str):
    """Scan a single subscription for optimization recommendations."""
    sub_name = SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8])
    result = {"cleanup": [], "scheduling": [], "vms": 0, "disks": 0, "unattached": 0, "errors": []}
    try:
        clients = get_clients(sub_id)

        vms = list(clients["compute"].virtual_machines.list_all())
        disks = list(clients["compute"].disks.list())
        result["vms"] = len(vms)
        result["disks"] = len(disks)

        unattached_disks = [d for d in disks if d.disk_state == "Unattached"]
        result["unattached"] = len(unattached_disks)

        for disk in unattached_disks:
            result["cleanup"].append({
                "resource": disk.name,
                "resource_id": disk.id,
                "subscription": sub_name,
                "type": "orphaned_disk",
                "disk_size_gb": disk.disk_size_gb,
                "sku": disk.sku.name if disk.sku else "Unknown",
                "recommendation": f"Disk '{disk.name}' is unattached (size: {disk.disk_size_gb}GB, SKU: {disk.sku.name if disk.sku else 'N/A'})",
                "risk": "low",
            })

        for vm in vms:
            tags = vm.tags or {}
            env = tags.get("Environment", tags.get("environment", tags.get("env", "Unknown")))
            if env.lower() in ("development", "dev", "staging", "test", "sandbox", "qa"):
                result["scheduling"].append({
                    "resource": vm.name,
                    "resource_id": vm.id,
                    "subscription": sub_name,
                    "type": "non_prod_vm",
                    "environment": env,
                    "vm_size": vm.hardware_profile.vm_size,
                    "location": vm.location,
                    "recommendation": f"Non-production VM '{vm.name}' ({env}) in {sub_name} — schedule auto-shutdown",
                    "risk": "none",
                })
    except Exception as e:
        result["errors"].append({"subscription": sub_name, "error": str(e)[:100]})
    return result


def _live_get_optimization_recommendations(args: dict, state: dict) -> str:
    category = args.get("category", "all")
    recommendations = {"right_sizing": [], "cleanup": [], "scheduling": []}
    total_vms = 0
    total_disks = 0
    total_unattached = 0
    errors = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_scan_subscription_recommendations, sub_id): sub_id for sub_id in SUBSCRIPTION_IDS}
        for future in futures:
            try:
                result = future.result(timeout=45)
                recommendations["cleanup"].extend(result["cleanup"])
                recommendations["scheduling"].extend(result["scheduling"])
                total_vms += result["vms"]
                total_disks += result["disks"]
                total_unattached += result["unattached"]
                errors.extend(result["errors"])
            except FuturesTimeoutError:
                sub_name = SUBSCRIPTION_NAMES.get(futures[future], futures[future][:8])
                errors.append({"subscription": sub_name, "error": "Timed out after 45s"})
            except Exception as e:
                sub_name = SUBSCRIPTION_NAMES.get(futures[future], futures[future][:8])
                errors.append({"subscription": sub_name, "error": str(e)[:100]})

    if errors:
        recommendations["errors"] = errors

    if category != "all":
        recommendations = {category: recommendations.get(category, [])}

    return json.dumps({
        "category": category,
        "recommendations": recommendations,
        "subscriptions_scanned": len(SUBSCRIPTION_IDS),
        "total_vms_scanned": total_vms,
        "total_disks_scanned": total_disks,
        "unattached_disks_found": total_unattached,
    }, default=str)


RESOURCE_TYPE_SHORTCUTS = {
    "storage": "Microsoft.Storage/storageAccounts",
    "vm": "Microsoft.Compute/virtualMachines",
    "disk": "Microsoft.Compute/disks",
    "nsg": "Microsoft.Network/networkSecurityGroups",
    "vnet": "Microsoft.Network/virtualNetworks",
    "ip": "Microsoft.Network/publicIPAddresses",
}


def _live_list_resources(args: dict, state: dict) -> str:
    """List Azure resources by type across subscriptions."""
    resource_type = args.get("resource_type", "all")
    filter_sub = args.get("filter_subscription")

    # Resolve shortcut to full resource type
    resolved_type = RESOURCE_TYPE_SHORTCUTS.get(resource_type.lower(), resource_type) if resource_type != "all" else "all"

    # Determine which subscriptions to scan
    target_subs = SUBSCRIPTION_IDS
    if filter_sub:
        matched_subs = []
        for sub_id in SUBSCRIPTION_IDS:
            sub_name = SUBSCRIPTION_NAMES.get(sub_id, "")
            if filter_sub.lower() in sub_name.lower() or filter_sub.lower() in sub_id.lower():
                matched_subs.append(sub_id)
        if matched_subs:
            target_subs = matched_subs
        else:
            return json.dumps({
                "error": f"Subscription '{filter_sub}' not found",
                "available_subscriptions": [{"id": s, "name": SUBSCRIPTION_NAMES.get(s, "Unknown")} for s in SUBSCRIPTION_IDS],
            })

    all_resources = []
    errors = []

    def _list_sub_resources(sub_id):
        sub_name = SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8])
        clients = get_clients(sub_id)
        resource_client = clients["resource"]

        if resolved_type == "all":
            resources = resource_client.resources.list()
        else:
            resources = resource_client.resources.list(
                filter=f"resourceType eq '{resolved_type}'"
            )

        results = []
        for resource in resources:
            results.append({
                "name": resource.name,
                "resource_id": resource.id,
                "type": resource.type,
                "resource_group": resource.id.split("/resourceGroups/")[1].split("/")[0] if "/resourceGroups/" in resource.id else None,
                "location": resource.location,
                "tags": resource.tags or {},
                "subscription_name": sub_name,
            })
        return results

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_list_sub_resources, sub_id): sub_id for sub_id in target_subs}
        for future in futures:
            sub_id = futures[future]
            sub_name = SUBSCRIPTION_NAMES.get(sub_id, sub_id[:8])
            try:
                results = future.result(timeout=45)
                all_resources.extend(results)
            except FuturesTimeoutError:
                errors.append({"subscription": sub_name, "error": "Timed out after 45s"})
            except Exception as e:
                errors.append({"subscription": sub_name, "error": str(e)[:100]})

    return json.dumps({
        "query": {
            "resource_type": resource_type,
            "resolved_type": resolved_type,
            "filter_subscription": filter_sub,
            "subscriptions_scanned": len(target_subs),
        },
        "summary": {
            "total_resources_found": len(all_resources),
            "subscriptions_with_results": len(set(r["subscription_name"] for r in all_resources)),
        },
        "resources": all_resources,
        "errors": errors if errors else None,
    }, default=str)


def _live_compare_costs(args: dict, state: dict) -> str:
    """Compare costs between two periods to explain cost changes."""
    try:
        period1_start = datetime.strptime(args["period1_start"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        period1_end = datetime.strptime(args["period1_end"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        period2_start = datetime.strptime(args["period2_start"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        period2_end = datetime.strptime(args["period2_end"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as e:
        return json.dumps({"error": f"Invalid date format. Use YYYY-MM-DD: {str(e)}"})

    group_by = args.get("group_by", "resource")
    min_threshold = args.get("min_change_threshold", 10)  # Lower threshold to catch more changes
    filter_sub = args.get("filter_subscription")

    # Query both periods (with subscription filter if provided)
    query_params = {
        "time_range": "custom",
        "start_date": args["period1_start"],
        "end_date": args["period1_end"],
        "group_by": group_by,
    }
    if filter_sub:
        query_params["filter_subscription"] = filter_sub
    period1_data = json.loads(_live_query_cost_data(query_params, state))

    query_params["start_date"] = args["period2_start"]
    query_params["end_date"] = args["period2_end"]
    period2_data = json.loads(_live_query_cost_data(query_params, state))

    if "error" in period1_data:
        return json.dumps(period1_data)
    if "error" in period2_data:
        return json.dumps(period2_data)

    # Build comparison maps
    group_key_field = {
        "resource": "ResourceId",
        "resource_group": "ResourceGroupName",
        "service": "ServiceName",
        "environment": "ResourceId",
    }.get(group_by, "ResourceId")

    period1_costs = {}
    for row in period1_data.get("data", []):
        key = row.get(group_key_field, row.get("ResourceId", "unknown"))
        cost = float(row.get("Cost", row.get("totalCost", 0)))
        period1_costs[key] = period1_costs.get(key, 0) + cost

    period2_costs = {}
    for row in period2_data.get("data", []):
        key = row.get(group_key_field, row.get("ResourceId", "unknown"))
        cost = float(row.get("Cost", row.get("totalCost", 0)))
        period2_costs[key] = period2_costs.get(key, 0) + cost

    # Calculate changes
    all_keys = set(period1_costs.keys()) | set(period2_costs.keys())
    changes = []
    increased_total = 0
    decreased_total = 0
    new_resources_total = 0
    removed_resources_total = 0

    for key in all_keys:
        cost1 = period1_costs.get(key, 0)
        cost2 = period2_costs.get(key, 0)
        diff = cost2 - cost1

        if abs(diff) < min_threshold:
            continue

        # Extract resource name from full resource ID
        resource_name = key.split("/")[-1] if "/" in key else key

        change_record = {
            "resource": resource_name,
            "resource_id": key,
            "period1_cost": round(cost1, 2),
            "period2_cost": round(cost2, 2),
            "change_amount": round(diff, 2),
            "change_percent": round((diff / cost1 * 100) if cost1 > 0 else 0, 1),
        }

        if cost1 == 0:
            change_record["status"] = "new_resource"
            new_resources_total += cost2
        elif cost2 == 0:
            change_record["status"] = "removed_resource"
            removed_resources_total += cost1
        elif diff > 0:
            change_record["status"] = "increased"
            increased_total += diff
        else:
            change_record["status"] = "decreased"
            decreased_total += abs(diff)

        changes.append(change_record)

    # Sort by absolute change
    changes.sort(key=lambda x: abs(x["change_amount"]), reverse=True)

    period1_total = sum(period1_costs.values())
    period2_total = sum(period2_costs.values())
    total_change = period2_total - period1_total
    total_change_pct = (total_change / period1_total * 100) if period1_total > 0 else 0

    # Generate insights
    insights = []
    if total_change > 0:
        insights.append(f"Overall cost INCREASED by {round(abs(total_change), 2)} ({abs(total_change_pct):.1f}%)")
    else:
        insights.append(f"Overall cost DECREASED by {round(abs(total_change), 2)} ({abs(total_change_pct):.1f}%)")

    if new_resources_total > 0:
        new_count = sum(1 for c in changes if c["status"] == "new_resource")
        insights.append(f"{new_count} new resources added, costing {round(new_resources_total, 2)} in period 2")

    if removed_resources_total > 0:
        removed_count = sum(1 for c in changes if c["status"] == "removed_resource")
        insights.append(f"{removed_count} resources removed, saving {round(removed_resources_total, 2)}")

    if increased_total > 0:
        increased_count = sum(1 for c in changes if c["status"] == "increased")
        insights.append(f"{increased_count} existing resources increased costs by {round(increased_total, 2)}")

    if decreased_total > 0:
        decreased_count = sum(1 for c in changes if c["status"] == "decreased")
        insights.append(f"{decreased_count} existing resources decreased costs by {round(decreased_total, 2)}")

    # Top contributors
    top_increases = [c for c in changes if c["status"] == "increased"][:5]
    top_new = [c for c in changes if c["status"] == "new_resource"][:5]

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
            "new_resources": sum(1 for c in changes if c["status"] == "new_resource"),
            "removed_resources": sum(1 for c in changes if c["status"] == "removed_resource"),
            "increased_resources": sum(1 for c in changes if c["status"] == "increased"),
            "decreased_resources": sum(1 for c in changes if c["status"] == "decreased"),
        },
        "insights": insights,
        "top_increases": top_increases,
        "top_new_resources": top_new,
        "all_changes": changes[:50],  # Limit to top 50 for response size
        "note": "Use insights to understand cost drivers. Investigate top_increases and top_new_resources for optimization opportunities.",
    }, default=str)


_ROLE_DEFS_CACHE = {}


def _get_role_definitions(auth_client, scope: str) -> dict:
    """Fetch role definitions with caching (they rarely change)."""
    if scope in _ROLE_DEFS_CACHE:
        return _ROLE_DEFS_CACHE[scope]

    role_defs = {}
    for rd in auth_client.role_definitions.list(scope):
        role_defs[rd.id] = rd.role_name
    _ROLE_DEFS_CACHE[scope] = role_defs
    return role_defs


def _resolve_user_to_oid(filter_principal: str) -> tuple:
    """Resolve an email/name to (object_id, display_name, upn). Returns (None,'','') on failure."""
    import subprocess
    az_cmd = os.path.join(AZ_CLI_PATH, "az.cmd")

    for cmd_part in [
        f'ad user show --id "{filter_principal}" --query "{{id:id, displayName:displayName, userPrincipalName:userPrincipalName}}"',
        f'ad user list --filter "startswith(displayName,\'{filter_principal}\')" --query "[0].{{id:id, displayName:displayName, userPrincipalName:userPrincipalName}}"',
        f'ad sp list --filter "displayName eq \'{filter_principal}\'" --query "[0].{{id:id, displayName:displayName, userPrincipalName:appId}}"',
    ]:
        try:
            r = subprocess.run(
                f'"{az_cmd}" {cmd_part} -o json',
                capture_output=True, text=True, timeout=10, shell=True,
            )
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout.strip())
                if data and data.get("id"):
                    return data["id"], data.get("displayName", ""), data.get("userPrincipalName", "")
        except Exception:
            continue
    return None, "", ""


def _live_get_role_assignments(args: dict, state: dict) -> str:
    """Get Azure RBAC role assignments for a subscription."""
    filter_sub = args.get("filter_subscription")
    filter_principal = args.get("filter_principal", "").strip()

    if not filter_sub:
        return json.dumps({"error": "filter_subscription is required"})

    # Resolve subscription
    target_sub = None
    for sub_id in SUBSCRIPTION_IDS:
        sub_name = SUBSCRIPTION_NAMES.get(sub_id, "")
        if filter_sub.lower() in sub_name.lower() or filter_sub.lower() in sub_id.lower():
            target_sub = sub_id
            break

    if not target_sub:
        return json.dumps({
            "error": f"Subscription '{filter_sub}' not found",
            "available_subscriptions": [{"id": s, "name": SUBSCRIPTION_NAMES.get(s, "Unknown")} for s in SUBSCRIPTION_IDS],
        })

    cred = get_credential()
    auth_client = AuthorizationManagementClient(cred, target_sub)
    scope = f"/subscriptions/{target_sub}"

    # Resolve user and fetch role defs in parallel
    principal_oid, principal_display_name, principal_upn = None, "", ""

    with ThreadPoolExecutor(max_workers=2) as executor:
        role_defs_future = executor.submit(_get_role_definitions, auth_client, scope)

        if filter_principal:
            user_future = executor.submit(_resolve_user_to_oid, filter_principal)
            principal_oid, principal_display_name, principal_upn = user_future.result(timeout=12)
            if not principal_oid:
                return json.dumps({
                    "error": f"Could not find user/principal '{filter_principal}' in Azure AD",
                    "hint": "Verify the email address or display name is correct.",
                })

        try:
            role_defs = role_defs_future.result(timeout=15)
        except Exception as e:
            return json.dumps({"error": f"Failed to fetch role definitions: {str(e)[:100]}"})

    # Fetch role assignments (server-side filtered when possible)
    assignments = []
    try:
        if principal_oid:
            ra_iter = auth_client.role_assignments.list_for_scope(scope, filter=f"principalId eq '{principal_oid}'")
        else:
            ra_iter = auth_client.role_assignments.list_for_scope(scope)

        for ra in ra_iter:
            role_name = role_defs.get(ra.role_definition_id, ra.role_definition_id.split("/")[-1])
            principal_type = str(ra.principal_type) if hasattr(ra, "principal_type") else "Unknown"

            assignment = {
                "principal_id": ra.principal_id,
                "principal_type": principal_type,
                "role_name": role_name,
                "scope": ra.scope,
            }

            if principal_oid and ra.principal_id == principal_oid:
                assignment["display_name"] = principal_display_name
                assignment["user_principal_name"] = principal_upn

            assignments.append(assignment)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch role assignments: {str(e)[:150]}"})

    # For unfiltered queries, skip slow name resolution — return types and IDs only
    # The LLM can summarize counts by type without needing every name resolved

    # Group by principal for readability
    by_principal = {}
    for a in assignments:
        key = a.get("display_name") or a.get("user_principal_name") or a["principal_id"]
        if key not in by_principal:
            by_principal[key] = {
                "principal_id": a["principal_id"],
                "principal_type": a["principal_type"],
                "display_name": a.get("display_name", ""),
                "user_principal_name": a.get("user_principal_name", ""),
                "roles": [],
            }
        by_principal[key]["roles"].append({
            "role_name": a["role_name"],
            "scope": a["scope"],
        })

    return json.dumps({
        "subscription": SUBSCRIPTION_NAMES.get(target_sub, target_sub),
        "subscription_id": target_sub,
        "total_assignments": len(assignments),
        "principals": list(by_principal.values()),
        "summary": {
            "users": sum(1 for a in by_principal.values() if a["principal_type"] == "User"),
            "groups": sum(1 for a in by_principal.values() if a["principal_type"] == "Group"),
            "service_principals": sum(1 for a in by_principal.values() if a["principal_type"] == "ServicePrincipal"),
        },
    }, default=str)


# Roles that grant permission to assign other roles
_ROLE_ADMIN_ROLES = {"Owner", "User Access Administrator", "Role Based Access Control Administrator"}


def _get_signed_in_user() -> dict:
    """Get the currently logged-in user's info."""
    import subprocess
    az_cmd = os.path.join(AZ_CLI_PATH, "az.cmd")
    try:
        r = subprocess.run(
            f'"{az_cmd}" ad signed-in-user show --query "{{id:id, displayName:displayName, userPrincipalName:userPrincipalName}}" -o json',
            capture_output=True, text=True, timeout=10, shell=True,
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout.strip())
    except Exception:
        pass
    return {}


def _live_assign_role(args: dict, state: dict) -> str:
    """Assign an Azure RBAC role after verifying the caller has permission."""
    import subprocess

    target_principal = args.get("target_principal", "").strip()
    role_name = args.get("role_name", "").strip()
    filter_sub = args.get("filter_subscription", "").strip()
    custom_scope = args.get("scope", "").strip()

    if not target_principal or not role_name or not filter_sub:
        return json.dumps({"error": "target_principal, role_name, and filter_subscription are all required."})

    # Resolve subscription
    target_sub = None
    for sub_id in SUBSCRIPTION_IDS:
        sub_name = SUBSCRIPTION_NAMES.get(sub_id, "")
        if filter_sub.lower() in sub_name.lower() or filter_sub.lower() in sub_id.lower():
            target_sub = sub_id
            break

    if not target_sub:
        return json.dumps({
            "error": f"Subscription '{filter_sub}' not found",
            "available_subscriptions": [{"id": s, "name": SUBSCRIPTION_NAMES.get(s, "Unknown")} for s in SUBSCRIPTION_IDS],
        })

    scope = custom_scope or f"/subscriptions/{target_sub}"
    sub_display = SUBSCRIPTION_NAMES.get(target_sub, target_sub)
    az_cmd = os.path.join(AZ_CLI_PATH, "az.cmd")

    # Step 1: Get the currently logged-in user
    signed_in_user = _get_signed_in_user()
    if not signed_in_user or not signed_in_user.get("id"):
        return json.dumps({"error": "Could not determine the currently logged-in user. Please ensure you are logged in via 'az login'."})

    caller_oid = signed_in_user["id"]
    caller_name = signed_in_user.get("displayName", "")
    caller_upn = signed_in_user.get("userPrincipalName", "")

    # Step 2: Check if the caller has permission to assign roles
    cred = get_credential()
    auth_client = AuthorizationManagementClient(cred, target_sub)
    role_defs = _get_role_definitions(auth_client, f"/subscriptions/{target_sub}")

    caller_roles = []
    try:
        for ra in auth_client.role_assignments.list_for_scope(
            f"/subscriptions/{target_sub}", filter=f"principalId eq '{caller_oid}'"
        ):
            rn = role_defs.get(ra.role_definition_id, ra.role_definition_id.split("/")[-1])
            caller_roles.append(rn)
    except Exception as e:
        return json.dumps({"error": f"Failed to check your permissions: {str(e)[:100]}"})

    has_permission = any(r in _ROLE_ADMIN_ROLES for r in caller_roles)

    if not has_permission:
        return json.dumps({
            "status": "access_denied",
            "message": f"You ({caller_upn}) do not have permission to assign roles in subscription '{sub_display}'.",
            "your_current_roles": caller_roles,
            "required_roles": list(_ROLE_ADMIN_ROLES),
            "recommendation": "Contact a subscription Owner or User Access Administrator to request this permission.",
        })

    # Step 3: Resolve the target principal
    target_oid, target_display, target_upn = _resolve_user_to_oid(target_principal)
    if not target_oid:
        return json.dumps({
            "error": f"Could not find user/principal '{target_principal}' in Azure AD.",
            "hint": "Verify the email address or display name is correct.",
        })

    # Step 4: Execute the role assignment
    try:
        r = subprocess.run(
            f'"{az_cmd}" role assignment create --assignee-object-id "{target_oid}" --assignee-principal-type "User" --role "{role_name}" --scope "{scope}" -o json',
            capture_output=True, text=True, timeout=30, shell=True,
        )
        if r.returncode == 0:
            result_data = json.loads(r.stdout) if r.stdout.strip() else {}
            return json.dumps({
                "status": "success",
                "message": f"Role '{role_name}' successfully assigned to '{target_display or target_principal}' ({target_upn}) in subscription '{sub_display}'.",
                "details": {
                    "assigned_by": caller_upn,
                    "target_user": target_upn or target_principal,
                    "role": role_name,
                    "scope": scope,
                    "subscription": sub_display,
                },
            })
        else:
            error_msg = r.stderr.strip() if r.stderr else "Unknown error"
            if "already exists" in error_msg.lower() or "RoleAssignmentExists" in error_msg:
                return json.dumps({
                    "status": "already_exists",
                    "message": f"User '{target_display or target_principal}' already has the role '{role_name}' in subscription '{sub_display}'.",
                })
            return json.dumps({
                "status": "failed",
                "error": f"Role assignment failed: {error_msg[:200]}",
                "hint": "Check that the role name is valid. Common roles: Reader, Contributor, Owner, Storage Blob Data Reader, Key Vault Secrets Officer.",
            })
    except Exception as e:
        return json.dumps({"error": f"Failed to execute role assignment: {str(e)[:150]}"})
