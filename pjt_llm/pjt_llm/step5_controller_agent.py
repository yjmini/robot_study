"""Controller agent that turns natural language into turtlesim actions."""

import json
from typing import Any

import ollama

try:
    from pjt_llm.ros2_controller import TurtleController
    from pjt_llm.step2_agent import MODEL, _as_dict
except ImportError:
    from ros2_controller import TurtleController
    from step2_agent import MODEL, _as_dict


SYSTEM_PROMPT = """
You are a Korean controller agent for ROS 2 turtlesim.
Use tool calling to execute only the user's requested drawing or control task.
Do not add extra objects. If the user asks for one star, call draw_star once
and do not draw a moon or a full night sky. If the user asks for a night sky,
compose it from multiple explicit tool calls: set background, set pen, draw
stars, and optionally draw_crescent if the user requested a moon.

Prefer semantic tools over raw velocity when a shape is requested:
- square/rectangle: draw_square
- circle: draw_circle
- star: draw_star
- moon/crescent: draw_crescent

For color words, prefer set_background_color and set_pen_color. Supported
colors include Korean and English names such as 흰색, 검은색, 노란색, white,
black, yellow, red, green, blue, purple, pink, orange, and gray.
After tool calls, summarize what you did in Korean.
If the requested action has already been completed by tool results, stop
calling tools and provide the final summary.
"""


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "move_turtle",
            "description": "Move turtle by publishing cmd_vel for a duration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "linear_x": {
                        "type": "number",
                        "description": (
                            "Forward speed m/s. Safe range -2.0 to 2.0."
                        ),
                    },
                    "angular_z": {
                        "type": "number",
                        "description": (
                            "Turn speed rad/s. Safe range -3.0 to 3.0."
                        ),
                    },
                    "duration": {
                        "type": "number",
                        "description": (
                            "Seconds to move. Safe range 0.1 to 10.0."
                        ),
                    },
                },
                "required": ["linear_x", "angular_z", "duration"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop_turtle",
            "description": "Stop the turtle immediately.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_background",
            "description": (
                "Set turtlesim background color and clear the screen."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "r": {"type": "integer", "description": "Red 0-255."},
                    "g": {"type": "integer", "description": "Green 0-255."},
                    "b": {"type": "integer", "description": "Blue 0-255."},
                },
                "required": ["r", "g", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_background_color",
            "description": (
                "Set background by Korean or English color name and clear."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "color": {
                        "type": "string",
                        "description": (
                            "Color name, e.g. 흰색, 검은색, 노란색, white."
                        ),
                    },
                },
                "required": ["color"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_pen",
            "description": "Set turtle pen color, width, or turn drawing off.",
            "parameters": {
                "type": "object",
                "properties": {
                    "r": {"type": "integer", "description": "Red 0-255."},
                    "g": {"type": "integer", "description": "Green 0-255."},
                    "b": {"type": "integer", "description": "Blue 0-255."},
                    "width": {
                        "type": "integer",
                        "description": "Pen width 1-12.",
                    },
                    "off": {
                        "type": "boolean",
                        "description": "True disables drawing.",
                    },
                },
                "required": ["r", "g", "b", "width", "off"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_pen_color",
            "description": "Set pen by Korean or English color name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "color": {
                        "type": "string",
                        "description": (
                            "Color name, e.g. 흰색, 검은색, 노란색, yellow."
                        ),
                    },
                    "width": {
                        "type": "integer",
                        "description": "Pen width 1-12.",
                    },
                    "off": {
                        "type": "boolean",
                        "description": "True disables drawing.",
                    },
                },
                "required": ["color", "width", "off"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "teleport_turtle",
            "description": (
                "Teleport turtle to an absolute turtlesim position."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "number",
                        "description": "X coordinate 0.5-10.5.",
                    },
                    "y": {
                        "type": "number",
                        "description": "Y coordinate 0.5-10.5.",
                    },
                    "theta": {
                        "type": "number",
                        "description": "Heading radians -3.14 to 3.14.",
                    },
                },
                "required": ["x", "y", "theta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draw_square",
            "description": "Draw a precise square using absolute positions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "center_x": {
                        "type": "number",
                        "description": "Center X coordinate.",
                    },
                    "center_y": {
                        "type": "number",
                        "description": "Center Y coordinate.",
                    },
                    "size": {
                        "type": "number",
                        "description": "Square side length.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draw_circle",
            "description": "Draw a precise circle using absolute positions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "center_x": {
                        "type": "number",
                        "description": "Center X coordinate.",
                    },
                    "center_y": {
                        "type": "number",
                        "description": "Center Y coordinate.",
                    },
                    "radius": {
                        "type": "number",
                        "description": "Circle radius.",
                    },
                    "segments": {
                        "type": "integer",
                        "description": "Number of segments.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draw_star",
            "description": "Draw exactly one five-point star.",
            "parameters": {
                "type": "object",
                "properties": {
                    "center_x": {
                        "type": "number",
                        "description": "Center X coordinate.",
                    },
                    "center_y": {
                        "type": "number",
                        "description": "Center Y coordinate.",
                    },
                    "radius": {
                        "type": "number",
                        "description": "Star outer radius.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draw_crescent",
            "description": "Draw exactly one crescent moon outline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "center_x": {
                        "type": "number",
                        "description": "Center X coordinate.",
                    },
                    "center_y": {
                        "type": "number",
                        "description": "Center Y coordinate.",
                    },
                    "radius": {
                        "type": "number",
                        "description": "Crescent outer radius.",
                    },
                },
            },
        },
    },
]


class ControllerToolbox:
    """Adapter that exposes TurtleController methods as LLM tools."""

    def __init__(self) -> None:
        """Create the underlying turtlesim controller."""
        self.controller = TurtleController()

    def close(self) -> None:
        """Close the underlying controller."""
        self.controller.close()

    def execute(self, tool_call: Any) -> dict[str, Any]:
        """Execute one Ollama tool call against the controller."""
        function = _as_dict(_as_dict(tool_call).get("function"))
        name = function.get("name")
        args = _as_dict(function.get("arguments"))
        if not hasattr(self.controller, str(name)):
            return {"ok": False, "error": f"unknown tool: {name}"}
        try:
            method = getattr(self.controller, str(name))
            return method(**args)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "tool": name, "error": str(exc)}


def run_agent(user_query: str, max_iterations: int = 12) -> str:
    """Run a bounded controller-agent loop."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    max_iterations = max(1, min(int(max_iterations or 12), 30))
    toolbox = ControllerToolbox()

    try:
        for index in range(max_iterations):
            response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
            assistant_message = response["message"]
            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls") or []
            if not tool_calls:
                return assistant_message.get("content", "")

            print(
                "[controller] tool round "
                f"{index + 1}: {len(tool_calls)} call(s)"
            )
            for tool_call in tool_calls:
                function = _as_dict(_as_dict(tool_call).get("function"))
                result = toolbox.execute(tool_call)
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
                "content": (
                    "지금까지 실행한 제어 결과를 요약하고, "
                    "추가 동작 없이 마무리해줘."
                ),
            }
        )
        final = ollama.chat(model=MODEL, messages=messages)
        return final["message"]["content"]
    finally:
        toolbox.close()


def main() -> None:
    """Run the controller agent CLI."""
    query = input("turtlesim 제어 명령을 입력하세요: ").strip()
    if not query:
        query = "거북이로 사각형을 그려줘."
    print(run_agent(query))


if __name__ == "__main__":
    main()
