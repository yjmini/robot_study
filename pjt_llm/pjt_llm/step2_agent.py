"""Single-turn ROS 2 diagnostic agent using Ollama tool calling."""

import json
import subprocess
from typing import Any

import ollama


MODEL = "llama3.2:3b"

SYSTEM_PROMPT = """
You are a ROS 2 Humble diagnostic agent for turtlesim and small ROS systems.
Use tools when the user asks about nodes, topics, messages, rates,
node details, or system health. Do not invent ROS state.
After a tool result is returned, answer in Korean with a concise diagnosis.
"""


def _run_ros2(args: list[str], timeout: float = 5.0) -> dict[str, Any]:
    """Run a ros2 CLI command and return a JSON-friendly result."""
    command = ["ros2", *args]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "command": command,
            "error": (
                "ros2 command not found. Source your ROS 2 environment first."
            ),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "command": command, "error": "command timed out"}

    return {
        "ok": completed.returncode == 0,
        "command": command,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
    }


def list_nodes() -> dict[str, Any]:
    """Return all currently visible ROS 2 nodes."""
    result = _run_ros2(["node", "list"])
    nodes = [
        line.strip()
        for line in result.get("stdout", "").splitlines()
        if line.strip()
    ]
    result["nodes"] = nodes
    result["count"] = len(nodes)
    return result


def list_topics() -> dict[str, Any]:
    """Return all currently visible ROS 2 topics with message types."""
    result = _run_ros2(["topic", "list", "-t"])
    topics = []
    for line in result.get("stdout", "").splitlines():
        line = line.strip()
        if not line:
            continue
        if " [" in line and line.endswith("]"):
            name, msg_type = line.rsplit(" [", 1)
            topics.append({
                "name": name.strip(),
                "type": msg_type[:-1].strip(),
            })
        else:
            topics.append({"name": line, "type": None})
    result["topics"] = topics
    result["count"] = len(topics)
    return result


def get_topic_info(topic_name: str = "/turtle1/cmd_vel") -> dict[str, Any]:
    """Return detailed information for one topic."""
    topic_name = topic_name or "/turtle1/cmd_vel"
    result = _run_ros2(["topic", "info", topic_name, "-v"])
    result["topic_name"] = topic_name
    return result


def get_topic_frequency(
    topic_name: str = "/turtle1/pose",
    window: int = 5,
) -> dict[str, Any]:
    """Measure topic publish frequency for a short window."""
    topic_name = topic_name or "/turtle1/pose"
    window = max(1, min(int(window or 5), 10))
    result = _run_ros2(
        ["topic", "hz", topic_name, "-w", str(window)],
        timeout=float(window) + 3.0,
    )
    result["topic_name"] = topic_name
    result["window"] = window
    return result


def get_node_info(node_name: str = "/turtlesim") -> dict[str, Any]:
    """Return publishers, subscribers, services, and actions for one node."""
    node_name = node_name or "/turtlesim"
    result = _run_ros2(["node", "info", node_name])
    result["node_name"] = node_name
    return result


def system_diagnosis() -> dict[str, Any]:
    """Return a compact snapshot of nodes, topics, and turtlesim status."""
    nodes = list_nodes()
    topics = list_topics()
    node_names = nodes.get("nodes", [])
    topic_names = [topic.get("name") for topic in topics.get("topics", [])]
    return {
        "ok": bool(nodes.get("ok")) and bool(topics.get("ok")),
        "nodes": node_names,
        "topics": topics.get("topics", []),
        "turtlesim_node_found": any(
            "turtlesim" in node for node in node_names
        ),
        "cmd_vel_found": "/turtle1/cmd_vel" in topic_names,
        "pose_found": "/turtle1/pose" in topic_names,
        "hint": (
            "Run `ros2 run turtlesim turtlesim_node` "
            "if turtlesim topics are missing."
        ),
    }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_nodes",
            "description": "Return all currently running ROS 2 node names.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_topics",
            "description": "Return all ROS 2 topic names with message types.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_topic_info",
            "description": "Return detailed information for a ROS 2 topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_name": {
                        "type": "string",
                        "description": (
                            "Topic name, for example /turtle1/cmd_vel."
                        ),
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_topic_frequency",
            "description": "Measure the publish frequency of a ROS 2 topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_name": {
                        "type": "string",
                        "description": "Topic name.",
                    },
                    "window": {
                        "type": "integer",
                        "description": "Sample window count from 1 to 10.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_node_info",
            "description": (
                "Return publishers, subscribers, services, "
                "and actions for a node."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "node_name": {
                        "type": "string",
                        "description": "Node name, for example /turtlesim.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "system_diagnosis",
            "description": (
                "Return a compact ROS 2 system diagnostic snapshot."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

TOOL_FUNCTIONS = {
    "list_nodes": list_nodes,
    "list_topics": list_topics,
    "get_topic_info": get_topic_info,
    "get_topic_frequency": get_topic_frequency,
    "get_node_info": get_node_info,
    "system_diagnosis": system_diagnosis,
}


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return dict(value)


def _execute_tool_call(tool_call: Any) -> dict[str, Any]:
    function = _as_dict(_as_dict(tool_call).get("function"))
    name = function.get("name")
    args = _as_dict(function.get("arguments"))

    if name not in TOOL_FUNCTIONS:
        return {"ok": False, "error": f"unknown tool: {name}"}

    try:
        return TOOL_FUNCTIONS[name](**args)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "tool": name, "error": str(exc)}


def run_agent(user_query: str) -> str:
    """Run a single-turn ROS 2 diagnostic tool-calling agent."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    first = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
    assistant_message = first["message"]
    messages.append(assistant_message)

    tool_calls = assistant_message.get("tool_calls") or []
    if not tool_calls:
        return assistant_message.get("content", "")

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

    final = ollama.chat(model=MODEL, messages=messages)
    return final["message"]["content"]


def main() -> None:
    """Run the single-turn diagnostic CLI."""
    query = input("ROS2 진단 질문을 입력하세요: ").strip()
    if not query:
        query = "현재 ROS2 시스템 상태를 진단해줘."
    print(run_agent(query))


if __name__ == "__main__":
    main()
