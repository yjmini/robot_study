"""Multi-agent orchestrator for ROS 2 diagnosis and turtlesim control."""

import ollama

try:
    from pjt_llm.step2_agent import MODEL
    from pjt_llm.step3_agent import latest_assistant_text
    from pjt_llm.step3_agent import run_agent as run_diagnosis_agent
    from pjt_llm.step5_controller_agent import run_agent as run_control_agent
except ImportError:
    from step2_agent import MODEL
    from step3_agent import latest_assistant_text
    from step3_agent import run_agent as run_diagnosis_agent
    from step5_controller_agent import run_agent as run_control_agent


ROUTER_PROMPT = """
You are a router for a ROS 2 multi-agent system.
Classify the next user message into exactly one label.

Labels:
- DIAGNOSE: needs live ROS 2 inspection, node/topic/message/rate checks,
  turtlesim health checks, or system diagnosis.
- CONTROL: asks to move/draw/control turtlesim, publish velocity, set pen,
  set background, teleport, draw shapes, stars, or moon.
- BOTH: asks for diagnosis/inspection and control/drawing in the same request.
- CHAT: general conversation, conceptual explanation, coding help, greetings,
  thanks, or anything that does not need live diagnosis or robot control.

Reply with exactly one word: DIAGNOSE, CONTROL, BOTH, or CHAT.
"""

CHAT_PROMPT = """
You are a helpful Korean ROS 2 assistant. Answer general ROS 2, LLM agent,
and coding questions clearly. Do not claim that you inspected live ROS state
unless the orchestrator routed the message to a diagnostic agent.
"""


def classify_route(user_query: str) -> str:
    """Classify a user request for multi-agent routing."""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user", "content": user_query},
        ],
    )
    label = response["message"]["content"].strip().upper()
    for route in ("BOTH", "DIAGNOSE", "CONTROL", "CHAT"):
        if route in label:
            return route
    return "CHAT"


def chat_once(
    user_query: str,
    history: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Run one general chat turn."""
    messages = list(history)
    messages.append({"role": "user", "content": user_query})
    response = ollama.chat(model=MODEL, messages=messages)
    messages.append(response["message"])
    return messages


def run_orchestrator_turn(
    user_query: str,
    chat_history: list[dict[str, str]],
    diagnosis_history: list[dict] | None,
) -> tuple[str, list[dict[str, str]], list[dict] | None]:
    """Route one user request and return response plus updated histories."""
    route = classify_route(user_query)

    if route == "DIAGNOSE":
        diagnosis_history = run_diagnosis_agent(
            user_query,
            history=diagnosis_history,
        )
        response = latest_assistant_text(diagnosis_history)
        return response, chat_history, diagnosis_history

    if route == "CONTROL":
        response = run_control_agent(user_query)
        return response, chat_history, diagnosis_history

    if route == "BOTH":
        diagnosis_history = run_diagnosis_agent(
            user_query,
            history=diagnosis_history,
        )
        diagnosis_text = latest_assistant_text(diagnosis_history)
        control_text = run_control_agent(user_query)
        response = (
            "[진단 결과]\n"
            f"{diagnosis_text}\n\n"
            "[제어 결과]\n"
            f"{control_text}"
        )
        return response, chat_history, diagnosis_history

    chat_history = chat_once(user_query, chat_history)
    return chat_history[-1]["content"], chat_history, diagnosis_history


def main() -> None:
    """Run the multi-agent orchestrator CLI."""
    print("ROS2 multi-agent orchestrator입니다.")
    print("종료: exit/quit/q, 기록 초기화: reset")
    chat_history: list[dict[str, str]] = [
        {"role": "system", "content": CHAT_PROMPT}
    ]
    diagnosis_history: list[dict] | None = None

    while True:
        user_query = input("\nUSER> ").strip()
        if not user_query:
            continue
        if user_query.lower() in {"exit", "quit", "q"}:
            print("종료합니다.")
            break
        if user_query.lower() == "reset":
            chat_history = [{"role": "system", "content": CHAT_PROMPT}]
            diagnosis_history = None
            print("대화 기록을 초기화했습니다.")
            continue

        response, chat_history, diagnosis_history = run_orchestrator_turn(
            user_query,
            chat_history,
            diagnosis_history,
        )
        print(f"\nASSISTANT> {response}")


if __name__ == "__main__":
    main()
