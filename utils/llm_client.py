import os
import json
import time
from openai import AzureOpenAI, RateLimitError
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4.1-mini")


def chat(system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
    max_retries = 7
    retry_delay = 5  # Start at 5 seconds to respect rate limits

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
                wait_time = retry_delay * (2 ** retry)  # Exponential backoff: 5s, 10s, 20s, 40s, 80s, 160s
                print(f"Rate limit hit. Waiting {wait_time}s before retry {retry + 1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                return f"OpenAI API rate limit exceeded. Please wait a few minutes and try again. Error: {str(e)}"


def chat_with_tools(messages: list, tools: list, temperature: float = 0.3, max_iterations: int = 10):
    from tools.executor import execute_tool

    iterations = 0
    tool_calls_log = []

    while iterations < max_iterations:
        iterations += 1

        # Add a small delay between iterations to avoid rapid-fire requests
        if iterations > 1:
            time.sleep(2)

        # Retry logic for rate limits
        max_retries = 7
        retry_delay = 5  # Start with 5 seconds to respect rate limits

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
                break  # Success, exit retry loop
            except RateLimitError as e:
                if retry < max_retries - 1:
                    wait_time = retry_delay * (2 ** retry)  # Exponential backoff: 5s, 10s, 20s, 40s, 80s, 160s
                    print(f"Rate limit hit. Waiting {wait_time}s before retry {retry + 1}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    # Last retry failed, return error message
                    error_msg = f"OpenAI API rate limit exceeded. Please wait a few minutes and try again. Error: {str(e)}"
                    return error_msg, tool_calls_log

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content, tool_calls_log

        messages.append(message)

        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            tool_calls_log.append({
                "iteration": iterations,
                "tool": fn_name,
                "arguments": fn_args,
            })

            result = execute_tool(fn_name, fn_args)

            tool_calls_log[-1]["result_preview"] = result[:200] + "..." if len(result) > 200 else result

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return messages[-1].get("content", "Agent reached maximum iterations."), tool_calls_log
