"""
FinOps Agentic Copilot — FastAPI Backend
Exposes the orchestrator, tools, and dashboard data as REST endpoints.
"""
import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

# Add project root to path so we can import existing modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from orchestrator import run_conversational, run_autonomous_pipeline
from tools.executor import execute_tool, PENDING_APPROVALS, EXECUTED_ACTIONS, LIVE_MODE

if LIVE_MODE:
    from tools.azure_live import LIVE_PENDING_APPROVALS, LIVE_EXECUTED_ACTIONS
else:
    LIVE_PENDING_APPROVALS = []
    LIVE_EXECUTED_ACTIONS = []

app = FastAPI(title="FinOps Agentic Copilot API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session state
conversation_history: list = []
tool_calls_log: list = []


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ApprovalAction(BaseModel):
    index: int
    action: str  # "approve" or "reject"


@app.get("/api/health")
def health():
    return {"status": "ok", "live_mode": LIVE_MODE, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/status")
def status():
    all_approvals = PENDING_APPROVALS + (LIVE_PENDING_APPROVALS if LIVE_MODE else [])
    executed_count = len(EXECUTED_ACTIONS) + (len(LIVE_EXECUTED_ACTIONS) if LIVE_MODE else 0)
    return {
        "live_mode": LIVE_MODE,
        "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID", "")[:8] + "..." if os.getenv("AZURE_SUBSCRIPTION_ID") else None,
        "tool_calls_count": len(tool_calls_log),
        "executed_actions": executed_count,
        "pending_approvals": len(all_approvals),
    }


@app.get("/api/subscriptions")
def get_subscriptions():
    options = [{"name": "All Subscriptions", "value": "all"}]
    if LIVE_MODE:
        try:
            cmd = r'"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" account list --query "[].{id:id, name:name, state:state}" -o json'
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, shell=True)
            if result.returncode == 0:
                all_subs = json.loads(result.stdout)
                for sub in all_subs:
                    if sub.get("state") == "Enabled":
                        options.append({"name": sub["name"], "value": sub["name"]})
        except Exception:
            pass
    return {"subscriptions": options}


@app.post("/api/chat")
def chat(req: ChatRequest):
    global conversation_history, tool_calls_log
    try:
        response, tool_calls, conversation_history = run_conversational(
            req.message, conversation_history
        )
        tool_calls_log.extend(tool_calls)
        return {
            "response": response,
            "tool_calls": tool_calls,
            "tool_calls_count": len(tool_calls),
            "reasoning_steps": len(set(t["iteration"] for t in tool_calls)) if tool_calls else 0,
        }
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate" in error_msg.lower():
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a moment and try again.")
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/api/scan")
def full_scan():
    global tool_calls_log
    try:
        result = run_autonomous_pipeline()
        tool_calls_log.extend(result["tool_calls"])
        return {
            "response": result["response"],
            "tool_calls": result["tool_calls"],
            "iterations": result["iterations"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/approvals")
def get_approvals():
    all_approvals = PENDING_APPROVALS + (LIVE_PENDING_APPROVALS if LIVE_MODE else [])
    return {"approvals": all_approvals}


@app.post("/api/approvals/action")
def handle_approval(req: ApprovalAction):
    all_approvals = PENDING_APPROVALS + (LIVE_PENDING_APPROVALS if LIVE_MODE else [])
    if req.index < 0 or req.index >= len(all_approvals):
        raise HTTPException(status_code=404, detail="Approval not found")

    approval = all_approvals[req.index]

    if req.action == "approve":
        result = execute_tool("execute_remediation", {
            "resource_name": approval["resource_name"],
            "action": approval["action"],
            "requires_approval": False,
            "parameters": approval.get("parameters", {}),
        })
        # Remove from lists
        if approval in PENDING_APPROVALS:
            PENDING_APPROVALS.remove(approval)
        if LIVE_MODE and approval in LIVE_PENDING_APPROVALS:
            LIVE_PENDING_APPROVALS.remove(approval)
        return {"status": "approved", "result": json.loads(result)}
    elif req.action == "reject":
        if approval in PENDING_APPROVALS:
            PENDING_APPROVALS.remove(approval)
        if LIVE_MODE and approval in LIVE_PENDING_APPROVALS:
            LIVE_PENDING_APPROVALS.remove(approval)
        return {"status": "rejected"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")


@app.get("/api/trace")
def get_trace():
    return {
        "tool_calls": tool_calls_log,
        "total_calls": len(tool_calls_log),
        "iterations": len(set(t["iteration"] for t in tool_calls_log)) if tool_calls_log else 0,
    }


@app.delete("/api/trace")
def clear_trace():
    global tool_calls_log
    tool_calls_log = []
    return {"status": "cleared"}


@app.get("/api/dashboard")
def get_dashboard():
    import pandas as pd
    data_dir = Path(__file__).resolve().parent.parent / "data"
    try:
        df = pd.read_csv(data_dir / "azure_cost_export.csv")
        df_hist = pd.read_csv(data_dir / "azure_cost_history.csv")
        df_all = pd.concat([df_hist, df], ignore_index=True)
        df_all["UsageDate"] = pd.to_datetime(df_all["UsageDate"])

        total_weekly = float(df["CostINR"].sum())
        total_prev = float(df_hist[df_hist["UsageDate"] >= "2026-05-25"]["CostINR"].sum())
        change = ((total_weekly - total_prev) / total_prev * 100) if total_prev > 0 else 0

        non_prod_df = df[df["Tags_Environment"].isin(["Development", "Staging"])]
        overrun_hours = non_prod_df["UsageHours"].clip(upper=24) - 12
        overrun_hours = overrun_hours.clip(lower=0)
        hourly_rate = non_prod_df["CostINR"] / non_prod_df["UsageHours"].replace(0, 1)
        auto_shutdown_savings = float((overrun_hours * hourly_rate).sum() / 7 * 30)
        idle_resource_savings = float(total_weekly * 0.08 / 7 * 30)
        potential_savings = auto_shutdown_savings + idle_resource_savings

        # Daily trend
        daily = df_all.groupby(df_all["UsageDate"].dt.strftime("%Y-%m-%d"))["CostINR"].sum().reset_index()
        daily.columns = ["date", "cost"]

        # By environment
        env_data = df.groupby("Tags_Environment")["CostINR"].sum().reset_index()
        env_data.columns = ["environment", "cost"]

        # By resource
        res_data = df.groupby("ResourceName")["CostINR"].sum().reset_index().sort_values("CostINR", ascending=False)
        res_data.columns = ["resource", "cost"]

        # Usage hours
        non_prod = df[df["Tags_Environment"].isin(["Development", "Staging"])]
        usage = non_prod.groupby("ResourceName")["UsageHours"].mean().reset_index()
        usage.columns = ["resource", "hours"]

        # Week-over-week
        current_week = df.groupby("ResourceName")["CostINR"].sum().reset_index()
        current_week.columns = ["resource", "this_week"]
        prev_week = df_hist[df_hist["UsageDate"] >= "2026-05-25"].groupby("ResourceName")["CostINR"].sum().reset_index()
        prev_week.columns = ["resource", "last_week"]
        comparison = current_week.merge(prev_week, on="resource", how="outer").fillna(0)
        comparison["change_pct"] = ((comparison["this_week"] - comparison["last_week"]) / comparison["last_week"] * 100).round(1)
        comparison["change_pct"] = comparison["change_pct"].replace([float('inf'), float('-inf')], 100)

        return {
            "kpis": {
                "weekly_spend": total_weekly,
                "monthly_projection": total_weekly / 7 * 30,
                "resources_tracked": int(df["ResourceName"].nunique()),
                "potential_savings": potential_savings,
                "change_pct": round(change, 1),
            },
            "daily_trend": daily.to_dict(orient="records"),
            "by_environment": env_data.to_dict(orient="records"),
            "by_resource": res_data.to_dict(orient="records"),
            "usage_hours": usage.to_dict(orient="records"),
            "comparison": comparison.to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conversation/reset")
def reset_conversation():
    global conversation_history, tool_calls_log
    conversation_history = []
    tool_calls_log = []
    return {"status": "reset"}


# --- Serve Frontend UI ---
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
