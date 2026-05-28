#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from nav_msgs.msg import Odometry

class OdomSubscriberNode(Node):
    def __init__(self):
        super().__init__('odom_subscriber_node')

        self.subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10)
        self.subscription  # prevent unused variable warning

        self.get_logger().info('Odom Subscriber Node has been started. Waiting for /odom messages...')
    
    def odom_callback(self, msg):
        pos_x = msg.pose.pose.position.x
        pos_y = msg.pose.pose.position.y
        ori_z = msg.pose.pose.orientation.z
        ori_w = msg.pose.pose.orientation.w

        log_msg = (
            f'X: {pos_x: .3f}, Y: {pos_y: .3f}, O-Z: {ori_z: .3f}, O-W: {ori_w: .3f}'
        )
        self.get_logger().info(log_msg)


def main(args=None):
    rclpy.init(args=args)
    node = OdomSubscriberNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard Interrupt (SIGINT) received. Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()