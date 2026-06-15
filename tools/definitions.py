FINOPS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_cost_data",
            "description": "Query Azure cost data for a specific time range and optional filters. Returns aggregated cost data from Azure Cost Management. Supports custom date ranges for historical analysis and month-to-month comparisons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_range": {
                        "type": "string",
                        "enum": ["last_7_days", "last_14_days", "last_30_days", "last_60_days", "last_90_days", "current_week", "previous_week", "current_month", "previous_month", "last_3_months", "last_6_months", "custom"],
                        "description": "Time range to query costs for. Use 'custom' for specific date ranges."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format (required if time_range='custom'). Example: '2026-04-01' for April 1st"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format (required if time_range='custom'). Example: '2026-04-30' for April 30th"
                    },
                    "group_by": {
                        "type": "string",
                        "enum": ["resource", "resource_group", "service", "environment", "owner"],
                        "description": "How to group the cost data"
                    },
                    "filter_environment": {
                        "type": "string",
                        "enum": ["Development", "Staging", "Production", "all"],
                        "description": "Filter by environment tag"
                    },
                    "filter_resource_type": {
                        "type": "string",
                        "description": "Filter by Azure resource type (e.g., Microsoft.Compute/virtualMachines)"
                    },
                    "filter_subscription": {
                        "type": "string",
                        "description": "Filter by specific Azure subscription ID or name. Example: 'ABB-APP-NMG-STAGE' or 'f291555e-6d94-4131-b099-e0c60d420777'"
                    }
                },
                "required": ["time_range", "group_by"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_resource_details",
            "description": "Get detailed information about a specific Azure resource including its current state, tags, configuration, and recent activity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_name": {
                        "type": "string",
                        "description": "Name of the Azure resource"
                    },
                    "include_metrics": {
                        "type": "boolean",
                        "description": "Whether to include CPU/memory utilization metrics"
                    }
                },
                "required": ["resource_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_anomalies",
            "description": "Run anomaly detection on cost data comparing current period to baseline. Uses statistical analysis to find unusual spending patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "baseline_period": {
                        "type": "string",
                        "enum": ["previous_week", "previous_month", "30_day_average"],
                        "description": "Baseline period for comparison"
                    },
                    "sensitivity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Anomaly detection sensitivity (high = more anomalies detected)"
                    },
                    "min_cost_threshold_inr": {
                        "type": "number",
                        "description": "Minimum daily cost to consider (filters out noise)"
                    }
                },
                "required": ["baseline_period", "sensitivity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_resource_utilization",
            "description": "Check CPU, memory, and network utilization for compute resources to identify underutilized or idle resources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_name": {
                        "type": "string",
                        "description": "Name of the compute resource"
                    },
                    "period_days": {
                        "type": "integer",
                        "description": "Number of days to analyze utilization"
                    }
                },
                "required": ["resource_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cost_trend",
            "description": "Get cost trend analysis showing daily costs over time with week-over-week comparison and projection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_name": {
                        "type": "string",
                        "description": "Specific resource name, or 'all' for total"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days for trend analysis"
                    }
                },
                "required": ["resource_name", "days"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_remediation",
            "description": "Execute a remediation action on an Azure resource. Only safe actions (auto-shutdown scheduling, tagging) can be auto-executed. Destructive actions require explicit approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_name": {
                        "type": "string",
                        "description": "Target Azure resource. Use full resource ID (starts with /subscriptions/) from get_resource_details or check_resource_utilization for reliable execution. Short names work but may fail if not unique across subscriptions."
                    },
                    "action": {
                        "type": "string",
                        "enum": ["schedule_auto_shutdown", "add_tags", "resize_vm", "delete_disk", "deallocate_vm", "delete_resource", "snapshot_and_delete"],
                        "description": "The remediation action to take"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Action-specific parameters (e.g., shutdown_time, tags, new_size)",
                        "properties": {
                            "shutdown_time": {"type": "string"},
                            "timezone": {"type": "string"},
                            "tags": {"type": "object"},
                            "new_size": {"type": "string"},
                            "snapshot_name": {"type": "string"}
                        }
                    },
                    "requires_approval": {
                        "type": "boolean",
                        "description": "Whether this action needs human approval before execution"
                    }
                },
                "required": ["resource_name", "action", "requires_approval"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_savings_report",
            "description": "Generate a comprehensive savings report with projections based on identified optimizations and actions taken.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_projections": {
                        "type": "boolean",
                        "description": "Include 30/60/90 day savings projections"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["executive_summary", "detailed", "technical"],
                        "description": "Report format/audience"
                    }
                },
                "required": ["include_projections", "format"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_pending_approvals",
            "description": "List all remediation actions that are pending human approval with their risk assessment and expected savings.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_optimization_recommendations",
            "description": "Get AI-powered optimization recommendations based on usage patterns, Reserved Instance opportunities, and right-sizing analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["right_sizing", "reserved_instances", "spot_instances", "scheduling", "cleanup", "all"],
                        "description": "Category of recommendations"
                    }
                },
                "required": ["category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_costs",
            "description": "Compare costs between two time periods to identify increases, decreases, and new/removed resources. Perfect for month-to-month analysis (e.g., April vs May, January vs February) and explaining why costs changed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period1_start": {
                        "type": "string",
                        "description": "Start date of first period in YYYY-MM-DD format (e.g., '2026-04-01' for April)"
                    },
                    "period1_end": {
                        "type": "string",
                        "description": "End date of first period in YYYY-MM-DD format (e.g., '2026-04-30')"
                    },
                    "period2_start": {
                        "type": "string",
                        "description": "Start date of second period in YYYY-MM-DD format (e.g., '2026-05-01' for May)"
                    },
                    "period2_end": {
                        "type": "string",
                        "description": "End date of second period in YYYY-MM-DD format (e.g., '2026-05-31')"
                    },
                    "group_by": {
                        "type": "string",
                        "enum": ["resource", "resource_group", "service", "environment"],
                        "description": "How to group comparison results"
                    },
                    "min_change_threshold": {
                        "type": "number",
                        "description": "Minimum cost change in currency to report (filters out noise). Default: 100"
                    },
                    "filter_subscription": {
                        "type": "string",
                        "description": "Filter comparison to specific Azure subscription (e.g., 'ABB-APP-NMG-STAGE'). If not provided, compares across all subscriptions."
                    }
                },
                "required": ["period1_start", "period1_end", "period2_start", "period2_end", "group_by"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_resources",
            "description": "List Azure resources by type across one or all subscriptions. Use to answer questions like 'what storage accounts exist', 'list VMs in PROD', 'show all disks'. Supports common shortcuts: 'storage', 'vm', 'disk', 'nsg', 'vnet', 'ip', or full resource type like 'Microsoft.Compute/virtualMachines'. Use 'all' to list all resources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "description": "Azure resource type to list. Accepts shortcuts: 'storage' (storageAccounts), 'vm' (virtualMachines), 'disk' (disks), 'nsg' (networkSecurityGroups), 'vnet' (virtualNetworks), 'ip' (publicIPAddresses), or full type like 'Microsoft.Compute/virtualMachines', or 'all' for all resources."
                    },
                    "filter_subscription": {
                        "type": "string",
                        "description": "Filter to a specific Azure subscription by name (e.g., 'ABB-APP-NMG-STAGE', 'ABB-APP-NMG-PROD-01') or ID. If not provided, searches across all subscriptions."
                    }
                },
                "required": ["resource_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_role_assignments",
            "description": "Get Azure RBAC role assignments for a subscription. Shows who (users, groups, service principals) has what permissions (Owner, Contributor, Reader, custom roles). Use to answer questions like 'what roles do I have', 'who has access to this subscription', 'list permissions in STAGE'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_subscription": {
                        "type": "string",
                        "description": "Azure subscription name (e.g., 'ABB-APP-NMG-STAGE') or ID to check role assignments for. Required."
                    },
                    "filter_principal": {
                        "type": "string",
                        "description": "Optional: filter by user email, display name, or service principal name to see only their role assignments."
                    }
                },
                "required": ["filter_subscription"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assign_role",
            "description": "Assign an Azure RBAC role to a user, group, or service principal in a subscription. Before assigning, this tool automatically checks whether the currently logged-in user has permission to assign roles (Owner or User Access Administrator). If they don't have permission, it returns an access denied error. Use when a user says 'assign role', 'grant access', 'give permissions to', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_principal": {
                        "type": "string",
                        "description": "The user email, display name, or service principal to assign the role to (e.g., 'user@company.com')."
                    },
                    "role_name": {
                        "type": "string",
                        "description": "The Azure role to assign (e.g., 'Reader', 'Contributor', 'Owner', 'Storage Blob Data Reader', 'Key Vault Secrets Officer'). Use standard Azure built-in role names."
                    },
                    "filter_subscription": {
                        "type": "string",
                        "description": "The subscription name or ID where the role should be assigned (e.g., 'ABB-APP-NMG-STAGE')."
                    },
                    "scope": {
                        "type": "string",
                        "description": "Optional: more specific scope for the assignment (e.g., a resource group path '/subscriptions/.../resourceGroups/myRG'). Defaults to subscription-level scope if not provided."
                    }
                },
                "required": ["target_principal", "role_name", "filter_subscription"]
            }
        }
    }
]
