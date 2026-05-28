#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped

class DobotTCPSubscriberNode(Node):
    def __init__(self):
        super().__init__('dobot_TCP_subscriber_node')

        self.subscription = self.create_subscription(
            PoseStamped,
            '/dobot_TCP',
            self.tcp_callback, # 콜백 함수 연결
            10)
        self.subscription  # prevent unused variable warning

        self.get_logger().info('TCP Subscriber Node has been started. Waiting for /dobot_TCP messages...')

    def tcp_callback(self, msg):
        pos_x = msg.pose.position.x
        pos_y = msg.pose.position.y
        pos_z = msg.pose.position.z

        ori_x = msg.pose.orientation.x
        ori_y = msg.pose.orientation.y
        ori_z = msg.pose.orientation.z
        ori_w = msg.pose.orientation.w

        log_msg = (
            f'\n'
            f'Received TCP Information: \n'
            f'pos_x: {pos_x}\n'
            f'pos_y: {pos_y}\n'
            f'pos_z: {pos_z}\n\n'

            f'ori_x: {ori_x}\n'
            f'ori_y: {ori_y}\n'
            f'ori_z: {ori_z}\n'
            f'ori_w: {ori_w}\n'
        )
        self.get_logger().info(log_msg)

def main(args=None):
    rclpy.init(args=args)
    node = DobotTCPSubscriberNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard Interrupt (SIGINT) received. Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()