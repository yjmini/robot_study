"""Multi-turn ROS 2 diagnostic agent with an agentic loop."""

import json
from typing import Any

import ollama

try:
    from pjt_llm.step2_agent import MODEL
    from pjt_llm.step2_agent import SYSTEM_PROMPT
    from pjt_llm.step2_agent import TOOLS
    from pjt_llm.step2_agent import _as_dict
    from pjt_llm.step2_agent import _execute_tool_call
except ImportError:
    from step2_agent import MODEL
    from step2_agent import SYSTEM_PROMPT
    from step2_agent import TOOLS
    from step2_agent import _as_dict
    from step2_agent import _execute_tool_call


LOOP_PROMPT = """
You may use ROS 2 diagnostic tools repeatedly. Think step by step internally.
Call tools only when they are needed. When enough evidence is collected,
stop calling tools and provide the final answer in Korean.
"""


def run_agent(
    user_query: str,
    history: list[dict[str, Any]] | None = None,
    max_iterations: int = 5,
) -> list[dict[str, Any]]:
    """Process a query with an agentic loop and return updated messages."""
    if history is None:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT + "\n" + LOOP_PROMPT}
        ]
    else:
        messages = list(history)

    messages.append({"role": "user", "content": user_query})
    max_iterations = max(1, min(int(max_iterations or 5), 10))

    for index in range(max_iterations):
        response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
        assistant_message = response["message"]
        messages.append(assistant_message)

        tool_calls = assistant_message.get("tool_calls") or []
        if not tool_calls:
            return messages

        print(f"[agent] tool round {index + 1}: {len(tool_calls)} call(s)")
        for tool_call in tool_calls:
            function = _as_dict(_as_dict(tool_call).get("function"))
            result = _execute_tool_call(tool_call)
            messages.append(
                {
                    "role": "tool",
                    "name": function.get("name", "unknown_tool"),
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    messages.append(
        {
            "role": "user",
            "content": "지금까지 수집한 도구 결과만 바탕으로 최종 진단을 정리해줘.",
        }
    )
    final = ollama.chat(model=MODEL, messages=messages)
    messages.append(final["message"])
    return messages


def latest_assistant_text(messages: list[dict[str, Any]]) -> str:
    """Return the latest assistant message text from a message list."""
    for message in reversed(messages):
        if message.get("role") == "assistant" and message.get("content"):
            return str(message["content"])
    return ""


def main() -> None:
    """Run the multi-turn diagnostic CLI."""
    query = input("ROS2 진단 질문을 입력하세요: ").strip()
    if not query:
        query = "turtlesim 노드와 토픽 상태를 진단해줘."
    messages = run_agent(query)
    print(latest_assistant_text(messages))


if __name__ == "__main__":
    main()
