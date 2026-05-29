"""Chatbot interface with intent routing to the diagnostic agent."""

import ollama

try:
    from pjt_llm.step2_agent import MODEL
    from pjt_llm.step3_agent import latest_assistant_text, run_agent
except ImportError:
    from step2_agent import MODEL
    from step3_agent import latest_assistant_text, run_agent


CHAT_PROMPT = """
You are a friendly Korean ROS 2 learning assistant. Answer general questions
without tools. If the user asks for live ROS 2 node/topic/message/rate/system
inspection, the program will route that request to a diagnostic agent.
"""

CLASSIFY_PROMPT = """
Classify whether the next user message requires live ROS 2 inspection.

- If node/topic/message state, topic rate, node info, turtlesim health, or
  system diagnosis must be inspected with tools: DIAGNOSE
- If it is greeting, thanks, conceptual explanation, coding discussion,
  robot control request, or not about live ROS state: CHAT

Reply with exactly one word: DIAGNOSE or CHAT.
"""


def classify_intent(user_query: str) -> str:
    """Classify whether a query needs live ROS 2 diagnosis."""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": CLASSIFY_PROMPT},
            {"role": "user", "content": user_query},
        ],
    )
    label = response["message"]["content"].strip().upper()
    if "DIAGNOSE" in label:
        return "DIAGNOSE"
    return "CHAT"


def chat_once(
    user_query: str,
    history: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Run one normal chatbot turn without ROS 2 tools."""
    messages = list(history)
    messages.append({"role": "user", "content": user_query})
    response = ollama.chat(model=MODEL, messages=messages)
    messages.append(response["message"])
    return messages


def main() -> None:
    """Run the CLI chatbot."""
    print("ROS2 LLM 챗봇입니다. 종료: exit/quit, 대화 초기화: reset")
    chat_history: list[dict[str, str]] = [
        {"role": "system", "content": CHAT_PROMPT}
    ]
    diagnose_history = None

    while True:
        user_query = input("\nUSER> ").strip()
        if not user_query:
            continue
        if user_query.lower() in {"exit", "quit", "q"}:
            print("종료합니다.")
            break
        if user_query.lower() == "reset":
            chat_history = [{"role": "system", "content": CHAT_PROMPT}]
            diagnose_history = None
            print("대화 기록을 초기화했습니다.")
            continue

        intent = classify_intent(user_query)
        if intent == "DIAGNOSE":
            diagnose_history = run_agent(user_query, history=diagnose_history)
            print(f"\nASSISTANT> {latest_assistant_text(diagnose_history)}")
        else:
            chat_history = chat_once(user_query, chat_history)
            print(f"\nASSISTANT> {chat_history[-1]['content']}")


if __name__ == "__main__":
    main()
