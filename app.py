import streamlit as st
import json
import time
import os
import importlib
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dotenv import load_dotenv

# Force reload tool modules so Streamlit picks up code changes without full restart
import tools.azure_live
import tools.executor
import tools.definitions
import utils.llm_client
import orchestrator
importlib.reload(tools.azure_live)
importlib.reload(tools.definitions)
importlib.reload(tools.executor)
importlib.reload(utils.llm_client)
importlib.reload(orchestrator)

from orchestrator import run_autonomous_pipeline, run_conversational
from tools.executor import execute_tool, PENDING_APPROVALS, EXECUTED_ACTIONS, LIVE_MODE

load_dotenv()

# Import live mode approvals if in live mode
if LIVE_MODE:
    from tools.azure_live import LIVE_PENDING_APPROVALS, LIVE_EXECUTED_ACTIONS
else:
    LIVE_PENDING_APPROVALS = []
    LIVE_EXECUTED_ACTIONS = []

st.set_page_config(
    page_title="FinOps Agentic Copilot",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .tool-call-box { background: #1a1f2e; border-left: 3px solid #4CAF50; padding: 10px; margin: 5px 0; border-radius: 4px; font-size: 0.85em; }
    .tool-call-box.pending { border-left-color: #FF9800; }
    .agent-thinking { background: #1a2332; border: 1px solid #2196F3; padding: 12px; border-radius: 8px; margin: 8px 0; }
    .savings-highlight { background: linear-gradient(135deg, #1b5e20, #2e7d32); padding: 20px; border-radius: 12px; text-align: center; }
    .metric-card { background: #1a1f2e; padding: 15px; border-radius: 8px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def _load_subscriptions():
    """Fetch subscriptions from Azure based on logged-in user. Cached for 5 min."""
    if LIVE_MODE:
        try:
            import subprocess
            cmd = r'"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd" account list --query "[].{id:id, name:name, state:state}" -o json'
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, shell=True)
            if result.returncode == 0:
                all_subs = json.loads(result.stdout)
                options = {"All Subscriptions": "all"}
                for sub in all_subs:
                    if sub.get("state") == "Enabled":
                        options[sub["name"]] = sub["name"]
                if len(options) > 1:
                    return options
        except Exception:
            pass
    return {"All Subscriptions": "all"}

SUBSCRIPTION_OPTIONS = _load_subscriptions()

# Session state init
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "tool_calls_log" not in st.session_state:
    st.session_state.tool_calls_log = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "approvals" not in st.session_state:
    st.session_state.approvals = []
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "chat"
if "show_scan_selector" not in st.session_state:
    st.session_state.show_scan_selector = False

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    st.title("FinOps Agentic Copilot")
    st.caption("Autonomous Cloud Cost Optimization")
    if LIVE_MODE:
        st.success(f"🟢 LIVE — Connected to Azure")
        st.caption(f"Subscription: {os.getenv('AZURE_SUBSCRIPTION_ID', '')[:8]}...")
    else:
        st.warning("🟡 DEMO MODE — Using simulated data")
    st.divider()

    st.markdown("### 🧠 Agentic Architecture")
    st.markdown("""
<div style="background: linear-gradient(135deg, #1a1f3e, #0d1117); border: 1px solid #30363d; border-radius: 12px; padding: 16px; font-size: 0.78em;">

<div style="text-align:center; background: linear-gradient(90deg, #6366f1, #8b5cf6); border-radius: 8px; padding: 8px; margin-bottom: 8px;">
<strong style="color:#fff;">👤 User / Natural Language</strong>
</div>

<div style="text-align:center; color:#666; font-size:1.2em;">⬇ ⬆</div>

<div style="text-align:center; background: linear-gradient(90deg, #0ea5e9, #06b6d4); border-radius: 8px; padding: 8px; margin-bottom: 8px;">
<strong style="color:#fff;">🧠 GPT-4.1-mini Reasoning Engine</strong><br>
<span style="color:#e0f2fe; font-size:0.85em;">Autonomous Planning • Multi-step Reasoning</span>
</div>

<div style="text-align:center; color:#666; font-size:1.2em;">⬇ Function Calling ⬆ Results</div>

<div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 10px; margin-bottom: 8px;">
<div style="text-align:center; color:#58a6ff; font-weight:bold; margin-bottom: 6px;">🔧 13 Azure Tools</div>
<div style="display:flex; flex-wrap:wrap; gap:4px; justify-content:center;">
<span style="background:#1f6feb33; color:#58a6ff; padding:2px 6px; border-radius:4px; font-size:0.8em;">Cost Query</span>
<span style="background:#1f6feb33; color:#58a6ff; padding:2px 6px; border-radius:4px; font-size:0.8em;">Compare</span>
<span style="background:#1f6feb33; color:#58a6ff; padding:2px 6px; border-radius:4px; font-size:0.8em;">Utilization</span>
<span style="background:#1f6feb33; color:#58a6ff; padding:2px 6px; border-radius:4px; font-size:0.8em;">Anomalies</span>
<span style="background:#238636; color:#7ee787; padding:2px 6px; border-radius:4px; font-size:0.8em;">Remediate</span>
<span style="background:#238636; color:#7ee787; padding:2px 6px; border-radius:4px; font-size:0.8em;">List</span>
</div>
</div>

<div style="text-align:center; color:#666; font-size:1.2em;">⬇ Actions ⬆ Data</div>

<div style="display:flex; gap:6px; margin-bottom:8px;">
<div style="flex:1; text-align:center; background:#0d419d; border-radius:6px; padding:6px;">
<span style="color:#fff; font-size:0.8em;">☁️ Azure<br>Cost Mgmt</span>
</div>
<div style="flex:1; text-align:center; background:#0d419d; border-radius:6px; padding:6px;">
<span style="color:#fff; font-size:0.8em;">⚙️ Azure<br>Compute</span>
</div>
<div style="flex:1; text-align:center; background:#0d419d; border-radius:6px; padding:6px;">
<span style="color:#fff; font-size:0.8em;">📊 Azure<br>Monitor</span>
</div>
</div>

<div style="text-align:center; background: linear-gradient(90deg, #da3633, #f85149); border-radius: 8px; padding: 8px;">
<strong style="color:#fff;">🛡️ Human-in-the-Loop Gate</strong><br>
<span style="color:#ffd7d5; font-size:0.85em;">Safe → Auto | Risky → Approval Queue</span>
</div>

</div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("### 🔧 Tools Available")
    tool_names = ["query_cost_data", "compare_costs", "get_resource_details", "detect_anomalies", "check_resource_utilization", "get_cost_trend", "execute_remediation", "generate_savings_report", "list_pending_approvals", "get_optimization_recommendations", "list_resources", "get_role_assignments", "assign_role"]
    for t in tool_names:
        st.markdown(f"- `{t}`")
    st.caption("✨ NEW: RBAC query + role assignment with permission checks")

    st.divider()
    st.markdown("### 📊 Session Stats")
    st.metric("Tool Calls Made", len(st.session_state.tool_calls_log))
    executed_count = len(EXECUTED_ACTIONS) + (len(LIVE_EXECUTED_ACTIONS) if LIVE_MODE else 0)
    pending_count = len(PENDING_APPROVALS) + len(st.session_state.get("approvals", [])) + (len(LIVE_PENDING_APPROVALS) if LIVE_MODE else 0)
    st.metric("Actions Executed", executed_count)
    st.metric("Pending Approvals", pending_count)
    st.divider()
    st.caption("Built for HCLTech–OpenAI Agentic AI Hackathon")
    st.caption("Track 2: Enterprise Operations")
    st.caption("Powered by GPT-4.1-mini + Function Calling")


# Main tabs
tab_chat, tab_dashboard, tab_approvals, tab_agent_trace = st.tabs([
    "💬 Chat with Agent", "📊 Cost Dashboard", "✅ Approval Queue", "🔍 Agent Trace"
])


# TAB 1: Conversational Agent
with tab_chat:
    st.header("💬 FinOps Agent — Ask Me Anything")
    st.markdown("*I can analyze your Azure costs, investigate waste, execute optimizations, and answer questions about your cloud spend.*")

    # Quick action buttons
    col1, col2, col3, col4 = st.columns(4)

    clicked_prompt = None
    with col1:
        if st.button("🔍 Full Scan", use_container_width=True):
            st.session_state.show_scan_selector = True
    with col2:
        if st.button("📈 Cost Trends", use_container_width=True):
            clicked_prompt = "Show me cost trends for the last 2 weeks. Which resources are increasing?"
    with col3:
        if st.button("🗑️ Find Waste", use_container_width=True):
            clicked_prompt = "Find all orphaned, unused, or idle resources that are wasting money."
    with col4:
        if st.button("💡 Recommendations", use_container_width=True):
            clicked_prompt = "Give me all optimization recommendations — right-sizing, scheduling, Reserved Instances, and cleanup."

    # Subscription selector for Full Scan
    if st.session_state.show_scan_selector:
        st.markdown("---")
        st.markdown("#### Select subscription to scan")
        scan_cols = st.columns([3, 1])
        with scan_cols[0]:
            selected_sub = st.selectbox(
                "Choose a subscription",
                options=list(SUBSCRIPTION_OPTIONS.keys()),
                index=0,
                label_visibility="collapsed",
            )
        with scan_cols[1]:
            if st.button("▶ Run Scan", type="primary", use_container_width=True):
                st.session_state.show_scan_selector = False
                sub_value = SUBSCRIPTION_OPTIONS[selected_sub]
                if sub_value == "all":
                    clicked_prompt = "Run a full FinOps optimization scan across ALL subscriptions — detect all anomalies, check utilization, and recommend actions."
                else:
                    clicked_prompt = f"Run a full FinOps optimization scan on subscription '{sub_value}' only — detect anomalies, check utilization, and recommend actions. Use filter_subscription='{sub_value}' in all tool calls."

    st.divider()

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
            if "tool_calls" in msg and msg["tool_calls"]:
                with st.expander(f"🔧 Agent used {len(msg['tool_calls'])} tools", expanded=False):
                    for tc in msg["tool_calls"]:
                        st.markdown(f"""<div class="tool-call-box">
                        <strong>🔧 {tc['tool']}</strong><br>
                        <code>{json.dumps(tc['arguments'], indent=None)[:120]}</code>
                        </div>""", unsafe_allow_html=True)

    # Chat input
    user_input = st.chat_input("Ask about your Azure costs, or tell me to optimize something...")

    if clicked_prompt:
        user_input = clicked_prompt

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.status("🧠 Agent thinking...", expanded=True) as status:
                st.write("Analyzing your request and determining which tools to use...")

                try:
                    response, tool_calls, st.session_state.conversation_history = run_conversational(
                        user_input, st.session_state.conversation_history
                    )

                    st.session_state.tool_calls_log.extend(tool_calls)

                    if tool_calls:
                        st.write(f"✅ Agent used **{len(tool_calls)} tool calls** across **{len(set(t['iteration'] for t in tool_calls))} reasoning steps**")
                        for tc in tool_calls:
                            st.write(f"  → `{tc['tool']}` — iteration {tc['iteration']}")

                    status.update(label="✅ Agent complete", state="complete")

                except Exception as e:
                    status.update(label="❌ Error occurred", state="error")
                    error_msg = str(e)
                    if "429" in error_msg or "rate" in error_msg.lower():
                        response = """⚠️ **OpenAI API Rate Limit Exceeded**

You've made too many requests in a short time. This is a temporary issue.

**What to do:**
1. Wait 1-2 minutes
2. Try your request again
3. If it persists, wait 5 minutes

**To avoid this:**
- Space out your requests (wait 10-15 seconds between queries)
- Avoid clicking buttons multiple times rapidly
- Use simpler queries when possible

The rate limit resets automatically after a few minutes."""
                    else:
                        response = f"❌ An error occurred: {error_msg}\n\nPlease try again or simplify your request."
                    st.error(response)

            st.markdown(response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "tool_calls": tool_calls,
        })
        st.rerun()


# TAB 2: Cost Dashboard
with tab_dashboard:
    st.header("📊 Real-Time Cost Dashboard")

    try:
        df = pd.read_csv("data/azure_cost_export.csv")
        df_hist = pd.read_csv("data/azure_cost_history.csv")
        df_all = pd.concat([df_hist, df], ignore_index=True)
        df_all["UsageDate"] = pd.to_datetime(df_all["UsageDate"])

        # KPI Row
        total_weekly = df["CostINR"].sum()
        total_prev = df_hist[df_hist["UsageDate"] >= "2026-05-25"]["CostINR"].sum()
        change = ((total_weekly - total_prev) / total_prev * 100) if total_prev > 0 else 0

        # Compute potential savings dynamically
        non_prod_df = df[df["Tags_Environment"].isin(["Development", "Staging"])]
        overrun_hours = non_prod_df["UsageHours"].clip(upper=24) - 12  # hours above 12h recommended
        overrun_hours = overrun_hours.clip(lower=0)
        hourly_rate = non_prod_df["CostINR"] / non_prod_df["UsageHours"].replace(0, 1)
        auto_shutdown_savings = (overrun_hours * hourly_rate).sum() / 7 * 30  # project to monthly
        idle_resource_savings = total_weekly * 0.08 / 7 * 30  # ~8% of spend is typically idle/orphaned
        potential_savings = auto_shutdown_savings + idle_resource_savings

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("This Week Spend", f"₹{total_weekly:,.0f}", f"{change:+.1f}% vs last week")
        k2.metric("Monthly Projection", f"₹{total_weekly/7*30:,.0f}")
        k3.metric("Resources Tracked", df["ResourceName"].nunique())
        k4.metric("Potential Savings", f"₹{potential_savings:,.0f}/mo", "Auto-shutdown + idle cleanup")

        st.divider()

        # Charts
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.subheader("Daily Cost Trend (3 weeks)")
            daily = df_all.groupby("UsageDate")["CostINR"].sum().reset_index()
            fig = px.area(daily, x="UsageDate", y="CostINR",
                         labels={"CostINR": "Daily Cost (₹)", "UsageDate": "Date"},
                         color_discrete_sequence=["#4CAF50"])
            fig.update_layout(template="plotly_dark", height=350,
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

        with col_chart2:
            st.subheader("Cost by Environment")
            env_data = df.groupby("Tags_Environment")["CostINR"].sum().reset_index()
            fig2 = px.pie(env_data, values="CostINR", names="Tags_Environment",
                         color_discrete_sequence=["#FF5722", "#4CAF50", "#2196F3"])
            fig2.update_layout(template="plotly_dark", height=350,
                             paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

        col_chart3, col_chart4 = st.columns(2)

        with col_chart3:
            st.subheader("Cost by Resource")
            res_data = df.groupby("ResourceName")["CostINR"].sum().reset_index().sort_values("CostINR", ascending=True)
            fig3 = px.bar(res_data, x="CostINR", y="ResourceName", orientation="h",
                         labels={"CostINR": "Weekly Cost (₹)", "ResourceName": "Resource"},
                         color_discrete_sequence=["#2196F3"])
            fig3.update_layout(template="plotly_dark", height=350,
                             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig3, use_container_width=True)

        with col_chart4:
            st.subheader("Usage Hours (Avg) — Dev/Staging")
            non_prod = df[df["Tags_Environment"].isin(["Development", "Staging"])]
            usage = non_prod.groupby("ResourceName")["UsageHours"].mean().reset_index()
            fig4 = go.Figure()
            fig4.add_trace(go.Bar(x=usage["ResourceName"], y=usage["UsageHours"], name="Actual", marker_color="#FF5722"))
            fig4.add_hline(y=12, line_dash="dash", line_color="#4CAF50", annotation_text="Recommended Max (12h)")
            fig4.update_layout(template="plotly_dark", height=350, yaxis_title="Avg Hours/Day",
                             paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig4, use_container_width=True)

        # Week-over-week comparison
        st.subheader("📈 Week-over-Week Resource Cost Comparison")
        current_week = df.groupby("ResourceName")["CostINR"].sum().reset_index()
        current_week.columns = ["ResourceName", "This Week"]
        prev_week = df_hist[df_hist["UsageDate"] >= "2026-05-25"].groupby("ResourceName")["CostINR"].sum().reset_index()
        prev_week.columns = ["ResourceName", "Last Week"]
        comparison = current_week.merge(prev_week, on="ResourceName", how="outer").fillna(0)
        comparison["Change %"] = ((comparison["This Week"] - comparison["Last Week"]) / comparison["Last Week"] * 100).round(1)
        comparison["Change %"] = comparison["Change %"].replace([float('inf'), float('-inf')], 100)
        st.dataframe(comparison.style.format({"This Week": "₹{:,.0f}", "Last Week": "₹{:,.0f}", "Change %": "{:+.1f}%"}), use_container_width=True)

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")


# TAB 3: Approval Queue
with tab_approvals:
    st.header("✅ Human-in-the-Loop Approval Queue")
    st.markdown("*Actions below require your approval before execution. The agent has determined these are too risky to auto-execute.*")
    st.divider()

    # Combine approvals from both demo mode and live mode
    all_approvals = PENDING_APPROVALS + st.session_state.approvals
    if LIVE_MODE:
        all_approvals.extend(LIVE_PENDING_APPROVALS)

    if not all_approvals:
        st.info("No pending approvals. Run the agent to generate optimization actions.")
        st.markdown("**Try asking the agent:** *'Run a full scan and queue risky actions for my approval'*")
    else:
        for i, approval in enumerate(all_approvals):
            risk_color = "🔴" if approval.get("risk_level") == "high" else "🟡"
            with st.expander(f"{risk_color} {approval.get('action', 'Unknown')} — {approval.get('resource_name', 'Unknown')}", expanded=True):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**Resource:** `{approval.get('resource_name')}`")
                    st.markdown(f"**Action:** {approval.get('action')}")
                    st.markdown(f"**Risk Level:** {approval.get('risk_level', 'medium')}")
                    st.code(approval.get("az_command", "N/A"), language="bash")
                with col_b:
                    if st.button("✅ Approve", key=f"approve_{i}"):
                        result = execute_tool("execute_remediation", {
                            "resource_name": approval["resource_name"],
                            "action": approval["action"],
                            "requires_approval": False,
                            "parameters": approval.get("parameters", {}),
                        })
                        st.success(f"Executed: {approval['action']} on {approval['resource_name']}")
                        st.json(json.loads(result))
                        # Remove from approval lists
                        if approval in PENDING_APPROVALS:
                            PENDING_APPROVALS.remove(approval)
                        if LIVE_MODE and approval in LIVE_PENDING_APPROVALS:
                            LIVE_PENDING_APPROVALS.remove(approval)
                        if approval in st.session_state.approvals:
                            st.session_state.approvals.remove(approval)
                        time.sleep(1)
                        st.rerun()
                    if st.button("❌ Reject", key=f"reject_{i}"):
                        st.warning(f"Rejected: {approval['action']} on {approval['resource_name']}")
                        # Remove from approval lists
                        if approval in PENDING_APPROVALS:
                            PENDING_APPROVALS.remove(approval)
                        if LIVE_MODE and approval in LIVE_PENDING_APPROVALS:
                            LIVE_PENDING_APPROVALS.remove(approval)
                        if approval in st.session_state.approvals:
                            st.session_state.approvals.remove(approval)
                        time.sleep(1)
                        st.rerun()


# TAB 4: Agent Trace
with tab_agent_trace:
    st.header("🔍 Agent Reasoning Trace")
    st.markdown("*Full transparency into the agent's decision-making process — every tool call, every reasoning step.*")
    st.divider()

    if not st.session_state.tool_calls_log:
        st.info("No agent activity yet. Start a conversation or run a scan to see the agent's reasoning trace.")
    else:
        st.metric("Total Tool Calls", len(st.session_state.tool_calls_log))
        st.metric("Reasoning Iterations", len(set(t["iteration"] for t in st.session_state.tool_calls_log)))

        st.divider()
        st.subheader("Tool Call Timeline")

        for tc in st.session_state.tool_calls_log:
            iteration = tc["iteration"]
            tool = tc["tool"]
            args = tc["arguments"]

            icon = {"query_cost_data": "📊", "get_resource_details": "🔎", "detect_anomalies": "🚨",
                    "check_resource_utilization": "📈", "get_cost_trend": "📉", "execute_remediation": "⚡",
                    "generate_savings_report": "📋", "list_pending_approvals": "✅",
                    "get_optimization_recommendations": "💡"}.get(tool, "🔧")

            with st.expander(f"{icon} Step {iteration}: `{tool}`", expanded=False):
                st.markdown("**Arguments:**")
                st.json(args)
                if "result_preview" in tc:
                    st.markdown("**Result Preview:**")
                    st.code(tc["result_preview"][:500], language="json")

        if st.button("🗑️ Clear Trace"):
            st.session_state.tool_calls_log = []
            st.rerun()
