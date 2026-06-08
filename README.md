# FinOps Agentic Copilot

**Autonomous Cloud Cost Optimization Agent powered by OpenAI GPT-4.1-mini**

An enterprise-grade AI agent that autonomously detects cloud waste, diagnoses root causes, and executes safe optimizations across Azure subscriptions — with human-in-the-loop approval for risky actions.

Built for the **HCLTech–OpenAI Agentic AI Hackathon** | Track 2: Enterprise Operations

---

## Key Features

- **Autonomous Multi-Step Reasoning** — Agent chains 5-15 tool calls per query, deciding what to investigate next
- **11 Azure Tools** — Cost querying, resource listing, utilization analysis, anomaly detection, remediation execution
- **Human-in-the-Loop Safety** — Risky actions (delete, resize, deallocate) require explicit approval; safe actions auto-execute
- **Real-Time Azure Integration** — Live connection to 5 Azure subscriptions via Azure SDK
- **Cost Comparison & Analysis** — Month-to-month comparison with intelligent insights explaining WHY costs changed
- **Interactive Dashboard** — Real-time charts, KPIs, and week-over-week trends
- **Full Transparency** — Agent Trace shows every tool call and decision for auditability

---

## Architecture

```
┌──────────────────────────────────────────────┐
│            User (Natural Language)            │
└─────────────────────┬────────────────────────┘
                      │
┌─────────────────────▼────────────────────────┐
│      GPT-4.1-mini Reasoning Engine           │
│   (Autonomous Planning • Function Calling)   │
└─────────────────────┬────────────────────────┘
                      │
┌─────────────────────▼────────────────────────┐
│              11 Azure Tools                   │
│  Cost Query │ Compare │ Utilization │ Anomaly │
│  List Resources │ Trend │ Remediation │ Report │
└─────────────────────┬────────────────────────┘
                      │
┌─────────────────────▼────────────────────────┐
│            Azure APIs (Live)                  │
│  Cost Management │ Compute │ Monitor │ Network│
└─────────────────────┬────────────────────────┘
                      │
┌─────────────────────▼────────────────────────┐
│         Human-in-the-Loop Gate               │
│   Safe → Auto-Execute │ Risky → Approval     │
└──────────────────────────────────────────────┘
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| AI Model | OpenAI GPT-4.1-mini (via Azure OpenAI) |
| Agent Pattern | OpenAI Function Calling (ReAct-style loop) |
| Frontend | Streamlit with Plotly charts |
| Backend | Python 3.11+ |
| Cloud Integration | Azure SDK (Cost Management, Compute, Monitor, Resource, Network, Storage) |
| Authentication | Azure CLI Credential |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Azure CLI (`az login` with access to target subscriptions)
- Azure OpenAI endpoint with GPT-4.1-mini deployment

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/FinOps-Agent.git
cd FinOps-Agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4.1-mini

AZURE_SUBSCRIPTION_ID=your-primary-subscription-id
AZURE_SUBSCRIPTION_IDS=sub1-id,sub2-id,sub3-id
```

### Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Usage Guide

### Chat Interface

Ask natural language questions:
- *"List all orphaned disks across my subscriptions"*
- *"Why is April 2026 cost higher than May for STAGE subscription?"*
- *"What storage accounts are in ABB-APP-NMG-STAGE?"*
- *"Delete the test disk in STAGE subscription"*

### Quick Actions

Use the pre-built buttons for common workflows:
- **Full Scan** — Autonomous optimization scan across all subscriptions
- **Cost Trends** — 14-day cost trend analysis
- **Find Waste** — Detect orphaned, idle, and unused resources
- **Recommendations** — AI-powered optimization recommendations

### Approval Queue

Risky actions are queued for human review:
1. Agent identifies optimization opportunity
2. Action queued with risk level assessment
3. Human reviews in Approval Queue tab
4. Click **Approve** to execute or **Reject** to dismiss

### Agent Trace

Full transparency into agent decision-making:
- Every tool call with arguments
- Results from each Azure API call
- Reasoning chain visible for auditing

---

## Tools Reference

| Tool | Purpose |
|------|---------|
| `query_cost_data` | Query cost data with flexible time ranges, grouping, and filters |
| `compare_costs` | Compare two periods with change attribution and insights |
| `list_resources` | List Azure resources by type (storage, vm, disk, nsg, vnet, ip) |
| `get_resource_details` | Deep-dive into a specific resource |
| `check_resource_utilization` | CPU/memory/network utilization for VMs |
| `detect_anomalies` | Statistical anomaly detection on cost data |
| `get_cost_trend` | Trend analysis with projections |
| `get_optimization_recommendations` | AI recommendations (right-sizing, cleanup, scheduling) |
| `execute_remediation` | Execute actions (auto-shutdown, tag, resize, delete, deallocate) |
| `generate_savings_report` | Generate executive/detailed savings reports |
| `list_pending_approvals` | View queued actions awaiting approval |

---

## Decision Framework

| Action Type | Risk Level | Behavior |
|-------------|-----------|----------|
| Add tags, auto-shutdown scheduling | None/Low | Auto-execute |
| Resize VM, deallocate | Medium | Queue for approval |
| Delete disk, delete resource | High | Queue for approval |
| Any Production modification | Critical | NEVER auto-execute |

---

## Project Structure

```
FinOps-Agent/
├── app.py                  # Streamlit UI (4 tabs: Chat, Dashboard, Approvals, Trace)
├── orchestrator.py         # Agent orchestration with system prompt
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── .streamlit/
│   └── config.toml         # Streamlit theme configuration
├── tools/
│   ├── definitions.py      # OpenAI function calling tool schemas
│   ├── executor.py         # Tool execution router (demo/live mode)
│   └── azure_live.py       # Live Azure SDK integration
├── utils/
│   └── llm_client.py       # OpenAI client with retry logic
├── agents/
│   ├── monitor_agent.py    # Cost monitoring agent
│   ├── diagnosis_agent.py  # Root cause diagnosis agent
│   ├── action_agent.py     # Remediation action agent
│   └── reporting_agent.py  # Report generation agent
└── data/
    ├── azure_cost_export.csv   # Sample cost data (demo mode)
    └── azure_cost_history.csv  # Historical cost data (demo mode)
```

---

## Business Impact

| Metric | Value |
|--------|-------|
| Waste Detection Time | **30 seconds** (vs 4+ hours manual) |
| Monthly Savings Identified | **₹3.5+ lakh** across 5 subscriptions |
| Subscriptions Monitored | **5** (Dev, Prod, Stage, APM, MGMT) |
| Resource Types Covered | VMs, Disks, Storage, Network, IPs |
| Actions Supported | 7 remediation types |

---

## Demo

A 3-5 minute video demonstration is available showing:
1. Autonomous full scan with multi-step reasoning
2. Real-time cost dashboard with Azure data
3. Human-in-the-loop approval workflow
4. Agent trace for full transparency

---

## Team

**Track:** Track 2 — Agents/Agentic Workflows for Enterprise Operations  
**Organization:** HCLTech (managing ABB Azure infrastructure)  
**Hackathon:** HCLTech–OpenAI Agentic AI Hackathon 2025

---

## License

This project was built for the HCLTech–OpenAI Agentic AI Hackathon. Internal use only.
