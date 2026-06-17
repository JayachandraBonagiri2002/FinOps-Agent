import os
import json
import time
import re
from openai import AzureOpenAI, RateLimitError
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4.1-mini")

MAX_TOOL_RESULT_CHARS = 10000


def _truncate_tool_result(result: str) -> str:
    """Intelligently compress tool results to stay within token budget.

    Instead of sending 50KB of raw Azure data to the LLM, extract the
    summary/insights and limit raw data to top items. Always returns valid JSON.
    """
    if len(result) <= MAX_TOOL_RESULT_CHARS:
        return result

    try:
        data = json.loads(result)
    except (json.JSONDecodeError, TypeError):
        return result[:MAX_TOOL_RESULT_CHARS - 50] + '... [truncated]"}'

    compressed = {}

    for key in ("summary", "query", "comparison", "insights", "category",
                "anomalies_detected", "total_potential_monthly_savings_inr",
                "total_potential_annual_savings_inr", "subscriptions_scanned",
                "total_vms_scanned", "total_disks_scanned", "unattached_disks_found",
                "status", "resource_name", "utilization", "recommendation",
                "note", "errors"):
        if key in data:
            compressed[key] = data[key]

    for key in ("data", "resources", "all_changes"):
        if key in data and isinstance(data[key], list):
            total_count = len(data[key])
            compressed[f"{key}_total_count"] = total_count
            compressed[key] = data[key][:15]
            if total_count > 15:
                compressed[f"_{key}_note"] = f"Showing top 15 of {total_count}. Use totals from 'summary' for accurate counts — do NOT count this list."

    if "recommendations" in data:
        recs = data["recommendations"]
        if isinstance(recs, dict):
            compressed["recommendations"] = {}
            for cat, items in recs.items():
                if isinstance(items, list):
                    compressed["recommendations"][cat] = items[:10]
                else:
                    compressed["recommendations"][cat] = items
        else:
            compressed["recommendations"] = recs

    if "anomalies" in data and isinstance(data["anomalies"], list):
        compressed["anomalies"] = data["anomalies"][:10]
        if len(data["anomalies"]) > 10:
            compressed["_anomalies_note"] = f"Showing top 10 of {len(data['anomalies'])}"

    if "raw_cost_data" in data:
        raw = data["raw_cost_data"]
        if isinstance(raw, dict):
            compressed["raw_cost_data"] = {
                "summary": raw.get("summary"),
                "query": raw.get("query"),
            }
            if "data" in raw and isinstance(raw["data"], list):
                compressed["raw_cost_data"]["data"] = raw["data"][:10]
                compressed["raw_cost_data"]["_data_count"] = len(raw["data"])

    for key in ("top_increases", "top_new_resources"):
        if key in data:
            compressed[key] = data[key][:5]

    if not compressed:
        compressed = data

    out = json.dumps(compressed, default=str)

    if len(out) > MAX_TOOL_RESULT_CHARS:
        for key in ("data", "resources", "all_changes", "anomalies"):
            if key in compressed and isinstance(compressed[key], list) and len(compressed[key]) > 5:
                compressed[key] = compressed[key][:5]
                compressed[f"_{key}_note"] = f"Trimmed to top 5 to fit response size. See '{key}_total_count' or 'summary' for real totals."
        out = json.dumps(compressed, default=str)

    if len(out) > MAX_TOOL_RESULT_CHARS:
        for key in ("data", "resources", "all_changes"):
            if key in compressed and isinstance(compressed[key], list):
                compressed.pop(key)
                compressed[f"_{key}_note"] = f"Data omitted for size. Total count in 'summary' field."
        out = json.dumps(compressed, default=str)

    return out


def _get_retry_after(error: RateLimitError) -> int:
    """Extract retry-after seconds from a RateLimitError response."""
    try:
        if hasattr(error, 'response') and error.response is not None:
            retry_after = error.response.headers.get("Retry-After") or error.response.headers.get("retry-after")
            if retry_after:
                return int(retry_after)
        error_body = str(error)
        match = re.search(r'retry after (\d+) second', error_body, re.IGNORECASE)
        if match:
            return int(match.group(1))
        match = re.search(r'Please retry after (\d+)', error_body)
        if match:
            return int(match.group(1))
    except (ValueError, AttributeError):
        pass
    return 0


def chat(system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
    max_retries = 5
    base_delay = 10

    for retry in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            if retry < max_retries - 1:
                retry_after = _get_retry_after(e)
                wait_time = max(retry_after, base_delay * (2 ** retry))
                wait_time = min(wait_time, 120)
                print(f"Rate limit hit. Waiting {wait_time}s before retry {retry + 1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                return f"OpenAI API rate limit exceeded. Please wait a few minutes and try again. Error: {str(e)}"


def chat_with_tools(messages: list, tools: list, temperature: float = 0.3, max_iterations: int = 10):
    from tools.executor import execute_tool

    iterations = 0
    tool_calls_log = []
    start_time = time.time()
    MAX_TOTAL_TIME = 120  # Hard cap: 2 minutes for the entire conversation turn

    while iterations < max_iterations:
        iterations += 1

        if time.time() - start_time > MAX_TOTAL_TIME:
            return "I'm sorry, the request took too long due to Azure API delays. Please try again in a moment.", tool_calls_log

        if iterations > 1:
            time.sleep(0.5)

        max_retries = 3
        base_delay = 5

        for retry in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=DEPLOYMENT,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=temperature,
                    max_tokens=4000,
                )
                break
            except RateLimitError as e:
                if retry < max_retries - 1:
                    retry_after = _get_retry_after(e)
                    wait_time = max(retry_after, base_delay * (2 ** retry))
                    wait_time = min(wait_time, 30)
                    print(f"Rate limit hit. Waiting {wait_time}s before retry {retry + 1}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    error_msg = f"OpenAI API rate limit exceeded after {max_retries} retries. Error: {str(e)}"
                    return error_msg, tool_calls_log

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content, tool_calls_log

        messages.append(message)

        cost_api_tools = {"query_cost_data", "compare_costs", "detect_anomalies", "get_cost_trend", "generate_savings_report"}

        for i, tool_call in enumerate(message.tool_calls):
            if time.time() - start_time > MAX_TOTAL_TIME:
                return "I'm sorry, the request took too long due to Azure API delays. Please try again in a moment.", tool_calls_log

            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            # Stagger calls to cost-heavy tools to avoid Azure 429 rate limits
            if i > 0 and fn_name in cost_api_tools:
                time.sleep(1)

            tool_calls_log.append({
                "iteration": iterations,
                "tool": fn_name,
                "arguments": fn_args,
            })

            result = execute_tool(fn_name, fn_args)

            compressed_result = _truncate_tool_result(result)

            tool_calls_log[-1]["result_preview"] = result[:200] + "..." if len(result) > 200 else result

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": compressed_result,
            })

    return messages[-1].get("content", "Agent reached maximum iterations."), tool_calls_log
