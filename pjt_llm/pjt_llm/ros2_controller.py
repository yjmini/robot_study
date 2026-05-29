"""Safe turtlesim controller tools for the controller agent."""

import math
import time
from typing import Any

import rclpy
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
from rcl_interfaces.srv import SetParameters
from std_srvs.srv import Empty
from turtlesim.srv import SetPen, TeleportAbsolute

COLOR_TABLE = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "yellow": (255, 255, 0),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "purple": (160, 80, 255),
    "pink": (255, 120, 180),
    "orange": (255, 140, 0),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "흰색": (255, 255, 255),
    "하얀색": (255, 255, 255),
    "하양": (255, 255, 255),
    "백색": (255, 255, 255),
    "검은색": (0, 0, 0),
    "검정": (0, 0, 0),
    "검정색": (0, 0, 0),
    "노란색": (255, 255, 0),
    "노랑": (255, 255, 0),
    "빨간색": (255, 0, 0),
    "빨강": (255, 0, 0),
    "초록색": (0, 255, 0),
    "초록": (0, 255, 0),
    "녹색": (0, 255, 0),
    "파란색": (0, 0, 255),
    "파랑": (0, 0, 255),
    "보라색": (160, 80, 255),
    "보라": (160, 80, 255),
    "분홍색": (255, 120, 180),
    "분홍": (255, 120, 180),
    "주황색": (255, 140, 0),
    "주황": (255, 140, 0),
    "회색": (128, 128, 128),
}


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a numeric value into the inclusive range."""
    return max(low, min(float(value), high))


def resolve_color(color: str) -> tuple[int, int, int]:
    """Resolve English or Korean color names to RGB."""
    key = color.strip().lower()
    if key not in COLOR_TABLE:
        raise ValueError(f"unknown color name: {color}")
    return COLOR_TABLE[key]


class TurtleController:
    """Small safe wrapper around turtlesim publishers and services."""

    def __init__(self) -> None:
        """Create publishers and service clients for turtlesim."""
        if not rclpy.ok():
            rclpy.init()
        self.node = rclpy.create_node("llm_turtle_controller")
        self.cmd_pub = self.node.create_publisher(
            Twist, "/turtle1/cmd_vel", 10
        )
        self.pen_client = self.node.create_client(SetPen, "/turtle1/set_pen")
        self.teleport_client = self.node.create_client(
            TeleportAbsolute, "/turtle1/teleport_absolute"
        )
        self.clear_client = self.node.create_client(Empty, "/clear")
        self.param_clients = [
            self.node.create_client(
                SetParameters, "/turtlesim/set_parameters"
            ),
            self.node.create_client(SetParameters, "/sim/set_parameters"),
        ]
        time.sleep(0.2)

    def close(self) -> None:
        """Stop the turtle and shut down this controller node."""
        self.stop_turtle()
        self.node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    def _call(
        self,
        client: Any,
        request: Any,
        timeout: float = 3.0,
    ) -> dict[str, Any]:
        if not client.wait_for_service(timeout_sec=timeout):
            return {
                "ok": False,
                "error": f"service unavailable: {client.srv_name}",
            }
        future = client.call_async(request)
        rclpy.spin_until_future_complete(
            self.node, future, timeout_sec=timeout
        )
        if future.done() and future.exception() is None:
            return {"ok": True, "service": client.srv_name}
        if future.done():
            return {
                "ok": False,
                "service": client.srv_name,
                "error": str(future.exception()),
            }
        return {
            "ok": False,
            "service": client.srv_name,
            "error": "service call timed out",
        }

    def move_turtle(
        self,
        linear_x: float = 1.0,
        angular_z: float = 0.0,
        duration: float = 1.0,
    ) -> dict[str, Any]:
        """Publish velocity for a bounded duration, then stop."""
        linear_x = clamp(linear_x, -2.0, 2.0)
        angular_z = clamp(angular_z, -3.0, 3.0)
        duration = clamp(duration, 0.1, 10.0)

        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z

        end_time = time.time() + duration
        while time.time() < end_time:
            self.cmd_pub.publish(msg)
            rclpy.spin_once(self.node, timeout_sec=0.01)
            time.sleep(0.05)

        self.stop_turtle()
        return {
            "ok": True,
            "linear_x": linear_x,
            "angular_z": angular_z,
            "duration": duration,
        }

    def stop_turtle(self) -> dict[str, Any]:
        """Publish zero velocity once."""
        self.cmd_pub.publish(Twist())
        rclpy.spin_once(self.node, timeout_sec=0.05)
        return {"ok": True, "action": "stop"}

    def set_pen(
        self,
        r: int = 255,
        g: int = 255,
        b: int = 255,
        width: int = 2,
        off: bool = False,
    ) -> dict[str, Any]:
        """Set turtlesim pen color, width, and off state."""
        request = SetPen.Request()
        request.r = int(clamp(r, 0, 255))
        request.g = int(clamp(g, 0, 255))
        request.b = int(clamp(b, 0, 255))
        request.width = int(clamp(width, 1, 12))
        request.off = bool(off)
        result = self._call(self.pen_client, request)
        result.update(
            {
                "r": request.r,
                "g": request.g,
                "b": request.b,
                "width": request.width,
                "off": request.off,
            }
        )
        return result

    def set_pen_color(
        self,
        color: str = "white",
        width: int = 2,
        off: bool = False,
    ) -> dict[str, Any]:
        """Set pen using a Korean or English color name."""
        r, g, b = resolve_color(color)
        result = self.set_pen(r, g, b, width, off)
        result["color"] = color
        return result

    def teleport_turtle(
        self,
        x: float = 5.5,
        y: float = 5.5,
        theta: float = 0.0,
    ) -> dict[str, Any]:
        """Teleport the turtle to an absolute position."""
        request = TeleportAbsolute.Request()
        request.x = clamp(x, 0.5, 10.5)
        request.y = clamp(y, 0.5, 10.5)
        request.theta = clamp(theta, -math.pi, math.pi)
        result = self._call(self.teleport_client, request)
        result.update({
            "x": request.x,
            "y": request.y,
            "theta": request.theta,
        })
        return result

    def clear_screen(self) -> dict[str, Any]:
        """Clear the turtlesim drawing canvas."""
        return self._call(self.clear_client, Empty.Request())

    def set_background(
        self,
        r: int = 0,
        g: int = 0,
        b: int = 0,
    ) -> dict[str, Any]:
        """Set the turtlesim background and clear existing drawings."""
        values = {
            "background_r": int(clamp(r, 0, 255)),
            "background_g": int(clamp(g, 0, 255)),
            "background_b": int(clamp(b, 0, 255)),
        }
        request = SetParameters.Request()
        for name, value in values.items():
            parameter = Parameter()
            parameter.name = name
            parameter.value = ParameterValue(
                type=ParameterType.PARAMETER_INTEGER,
                integer_value=value,
            )
            request.parameters.append(parameter)

        last_result = {
            "ok": False,
            "error": "no turtlesim parameter service found",
        }
        for client in self.param_clients:
            if client.wait_for_service(timeout_sec=0.5):
                last_result = self._call(client, request)
                break

        clear_result = self.clear_screen()
        return {
            "ok": bool(last_result.get("ok")),
            "background": values,
            "clear": clear_result,
        }

    def set_background_color(self, color: str = "black") -> dict[str, Any]:
        """Set background using a Korean or English color name."""
        r, g, b = resolve_color(color)
        result = self.set_background(r, g, b)
        result["color"] = color
        return result

    def draw_polyline(
        self,
        points: list[tuple[float, float]],
        close_shape: bool = False,
        theta: float = 0.0,
    ) -> dict[str, Any]:
        """Draw straight line segments through absolute canvas points."""
        if not points:
            return {"ok": False, "error": "points must not be empty"}

        self.set_pen(off=True)
        self.teleport_turtle(points[0][0], points[0][1], theta)
        self.set_pen(off=False)

        draw_points = list(points)
        if close_shape and points[0] != points[-1]:
            draw_points.append(points[0])

        for x, y in draw_points[1:]:
            self.teleport_turtle(x, y, theta)
            rclpy.spin_once(self.node, timeout_sec=0.02)

        return {
            "ok": True,
            "shape": "polyline",
            "points": [{"x": x, "y": y} for x, y in draw_points],
            "closed": close_shape,
        }

    def draw_square(
        self,
        center_x: float = 5.5,
        center_y: float = 5.5,
        size: float = 3.0,
    ) -> dict[str, Any]:
        """Draw a precise square using absolute turtle positions."""
        half = clamp(size, 0.5, 8.0) / 2.0
        center_x = clamp(center_x, 1.0 + half, 10.0 - half)
        center_y = clamp(center_y, 1.0 + half, 10.0 - half)
        points = [
            (center_x - half, center_y - half),
            (center_x + half, center_y - half),
            (center_x + half, center_y + half),
            (center_x - half, center_y + half),
        ]
        result = self.draw_polyline(points, close_shape=True)
        result["shape"] = "square"
        result["size"] = half * 2.0
        return result

    def draw_circle(
        self,
        center_x: float = 5.5,
        center_y: float = 5.5,
        radius: float = 1.7,
        segments: int = 72,
    ) -> dict[str, Any]:
        """Draw a precise circle with many short absolute segments."""
        radius = clamp(radius, 0.3, 4.5)
        center_x = clamp(center_x, 0.6 + radius, 10.4 - radius)
        center_y = clamp(center_y, 0.6 + radius, 10.4 - radius)
        segments = int(clamp(segments, 12, 144))
        points = []
        for index in range(segments):
            angle = 2.0 * math.pi * index / segments
            points.append((
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle),
            ))

        result = self.draw_polyline(points, close_shape=True)
        result["shape"] = "circle"
        result["radius"] = radius
        result["segments"] = segments
        return result

    def draw_star(
        self,
        center_x: float = 5.5,
        center_y: float = 5.5,
        radius: float = 0.6,
    ) -> dict[str, Any]:
        """Draw one five-point star."""
        radius = clamp(radius, 0.15, 2.0)
        center_x = clamp(center_x, 0.6 + radius, 10.4 - radius)
        center_y = clamp(center_y, 0.6 + radius, 10.4 - radius)
        points = []
        for index in range(10):
            current_radius = radius if index % 2 == 0 else radius * 0.42
            angle = math.pi / 2.0 + index * math.pi / 5.0
            points.append((
                center_x + current_radius * math.cos(angle),
                center_y + current_radius * math.sin(angle),
            ))

        result = self.draw_polyline(points, close_shape=True)
        result["shape"] = "star"
        result["radius"] = radius
        return result

    def draw_crescent(
        self,
        center_x: float = 5.5,
        center_y: float = 5.5,
        radius: float = 1.0,
    ) -> dict[str, Any]:
        """Draw a crescent moon as one continuous curved outline."""
        radius = clamp(radius, 0.3, 3.0)
        center_x = clamp(center_x, 0.6 + radius, 10.4 - radius)
        center_y = clamp(center_y, 0.6 + radius, 10.4 - radius)
        points = []

        for index in range(25):
            angle = -math.pi / 2.0 + math.pi * index / 24.0
            points.append((
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle),
            ))

        inner_radius = radius * 0.78
        inner_center_x = center_x + radius * 0.35
        for index in range(25):
            angle = math.pi / 2.0 - math.pi * index / 24.0
            points.append((
                inner_center_x + inner_radius * math.cos(angle),
                center_y + inner_radius * math.sin(angle),
            ))

        result = self.draw_polyline(points, close_shape=True)
        result["shape"] = "crescent"
        result["radius"] = radius
        return result


def main() -> None:
    """Run a small controller smoke test."""
    controller = TurtleController()
    try:
        controller.set_background(0, 0, 0)
        controller.set_pen(255, 255, 0, 3, False)
        controller.teleport_turtle(5.5, 5.5, 0.0)
        controller.move_turtle(1.5, 0.0, 1.0)
    finally:
        controller.close()


if __name__ == "__main__":
    main()
