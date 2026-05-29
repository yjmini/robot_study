"""Controller agent that turns natural language into turtlesim actions."""

import json
from typing import Any

import ollama

try:
    from pjt_llm.ros2_controller import COLOR_TABLE
    from pjt_llm.ros2_controller import TurtleController
    from pjt_llm.ros2_controller import resolve_color
    from pjt_llm.step2_agent import MODEL, _as_dict
except ImportError:
    from ros2_controller import COLOR_TABLE
    from ros2_controller import TurtleController
    from ros2_controller import resolve_color
    from step2_agent import MODEL, _as_dict


SYSTEM_PROMPT = """
You are a Korean controller agent for ROS 2 turtlesim.
Use tool calling to execute only the user's requested drawing or control task.
Do not add extra objects. If the user asks for one star, call draw_star once
and do not draw a moon or a full night sky. If the user asks for a night sky,
compose it from multiple explicit tool calls: set background, set pen, draw
stars, and optionally draw_crescent if the user requested a moon.
If the user asks for several stars, many stars, or stars here and there,
call draw_star_field once. Do not use move_turtle for drawing.

Important rules:
- For background colors, always call set_background_color with the exact color
  word from the user. Example: "흰색 배경" -> color="흰색".
- For shape colors, always call set_pen_color before drawing the shape.
  Example: "노란색 별" -> set_pen_color(color="노란색"), then draw_star.
  Even better, pass the requested color directly to the drawing tool:
  draw_star(color="노란색").
- Do not invent a different color. Never replace white with yellow, or yellow
  with white.
- If the user only asks to change the background, call only
  set_background_color and stop.

Prefer semantic tools over raw velocity when a shape is requested:
- square/rectangle: draw_square
- circle: draw_circle
- star: draw_star
- several stars/star field: draw_star_field
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
            "name": "draw_star_field",
            "description": (
                "Draw multiple separated stars. Use for several stars, "
                "many stars, or stars here and there. This never draws a moon."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Number of stars, 1-12.",
                    },
                    "color": {
                        "type": "string",
                        "description": "Star color name.",
                    },
                    "background_color": {
                        "type": "string",
                        "description": (
                            "Optional background color name. Use 검은색 "
                            "for a black screen."
                        ),
                    },
                    "pen_width": {
                        "type": "integer",
                        "description": "Optional pen width 1-12.",
                    },
                },
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
                "required": ["color"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draw_square",
            "description": (
                "Draw a precise square. If the user asks for a color, "
                "pass that color name in color."
            ),
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
                    "color": {
                        "type": "string",
                        "description": "Optional pen color name.",
                    },
                    "pen_width": {
                        "type": "integer",
                        "description": "Optional pen width 1-12.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draw_circle",
            "description": (
                "Draw a precise circle. If the user asks for a color, "
                "pass that color name in color."
            ),
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
                    "color": {
                        "type": "string",
                        "description": "Optional pen color name.",
                    },
                    "pen_width": {
                        "type": "integer",
                        "description": "Optional pen width 1-12.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draw_star",
            "description": (
                "Draw exactly one five-point star. If the user asks "
                "for a color, pass that color name in color."
            ),
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
                    "color": {
                        "type": "string",
                        "description": "Optional pen color name.",
                    },
                    "pen_width": {
                        "type": "integer",
                        "description": "Optional pen width 1-12.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draw_crescent",
            "description": (
                "Draw exactly one crescent moon outline. If the user "
                "asks for a color, pass that color name in color."
            ),
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
                    "color": {
                        "type": "string",
                        "description": "Optional pen color name.",
                    },
                    "pen_width": {
                        "type": "integer",
                        "description": "Optional pen width 1-12.",
                    },
                },
            },
        },
    },
]


class ControllerToolbox:
    """Adapter that exposes TurtleController methods as LLM tools."""

    def __init__(self, user_query: str) -> None:
        """Create the underlying turtlesim controller."""
        self.controller = TurtleController()
        self.user_query = user_query
        self.background_color = find_background_color(user_query)
        self.background_applied = False

    def close(self) -> None:
        """Close the underlying controller."""
        self.controller.close()

    def execute(self, tool_call: Any) -> dict[str, Any]:
        """Execute one Ollama tool call against the controller."""
        function = _as_dict(_as_dict(tool_call).get("function"))
        name = function.get("name")
        args = _as_dict(function.get("arguments"))
        args = {
            key: value
            for key, value in args.items()
            if value is not None and value != ""
        }
        self._fix_arguments(str(name), args)
        if not hasattr(self.controller, str(name)):
            return {"ok": False, "error": f"unknown tool: {name}"}
        try:
            self._apply_background_before_drawing(str(name))
            method = getattr(self.controller, str(name))
            return method(**args)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "tool": name, "error": str(exc)}

    def _fix_arguments(self, name: str, args: dict[str, Any]) -> None:
        """Correct color arguments that the small model often misses."""
        if name == "set_background_color" and self.background_color:
            args["color"] = self.background_color
        if name == "draw_star_field" and self.background_color:
            args["background_color"] = self.background_color
        if name == "draw_crescent" and "color" not in args:
            args["color"] = "노란색"
        drawing_tools = {
            "draw_circle",
            "draw_square",
            "draw_star",
            "draw_star_field",
            "draw_crescent",
        }
        if name in drawing_tools and self._same_as_background(args):
            args["color"] = "노란색"

    def _apply_background_before_drawing(self, name: str) -> None:
        """Apply requested background before the first drawing tool."""
        drawing_tools = {
            "draw_square",
            "draw_circle",
            "draw_star",
            "draw_star_field",
            "draw_crescent",
        }
        if name == "set_background_color":
            self.background_applied = True
            return
        if not self.background_color or self.background_applied:
            return
        if name in drawing_tools:
            self.controller.set_background_color(self.background_color)
            self.background_applied = True

    def _same_as_background(self, args: dict[str, Any]) -> bool:
        """Return whether a requested drawing color matches the background."""
        if not self.background_color or "color" not in args:
            return False
        try:
            return resolve_color(args["color"]) == resolve_color(
                self.background_color
            )
        except ValueError:
            return False


def normalize_text(text: str) -> str:
    """Normalize text for light Korean keyword matching."""
    return text.lower().replace(" ", "")


def find_background_color(user_query: str) -> str | None:
    """Find an explicitly requested background or screen color."""
    text = normalize_text(user_query)
    background_context = (
        "배경" in text
        or "화면" in text
        or "바탕" in text
        or "밤하늘" in text
        or "background" in text
        or "screen" in text
    )
    if not background_context:
        return None
    if "밤하늘" in text:
        return "검은색"

    color_names = sorted(COLOR_TABLE, key=len, reverse=True)
    for color_name in color_names:
        if normalize_text(color_name) in text:
            return color_name
    return None


def run_agent(user_query: str, max_iterations: int = 12) -> str:
    """Run a bounded controller-agent loop."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    max_iterations = max(1, min(int(max_iterations or 12), 30))
    toolbox = ControllerToolbox(user_query)

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
