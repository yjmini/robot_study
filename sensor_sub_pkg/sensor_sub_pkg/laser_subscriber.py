#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import LaserScan

class LaserSubscriberNode(Node):
    def __init__(self):
        super().__init__('laser_subscriber_node')

        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback, 
            10) 
        self.subscription  # prevent unused variable warning

        self.get_logger().info('LaserScan Subscriber Node has been started. Waiting for /scan messages...')

    def scan_callback(self, msg):
        if not msg.ranges:
            self.get_logger().warn('Received empty scan ranges.')
            return
        
        front_dist = msg.ranges[0]
        left_dist = msg.ranges[90]
        right_dist = msg.ranges[270]

        log_msg = f'Front: {front_dist:.3f}, Left: {left_dist:.3f}, Right: {right_dist:.3f}'
        self.get_logger().info(log_msg)

def main(args=None):
    rclpy.init(args=args)
    node = LaserSubscriberNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard Interrupt (SIGINT) received. Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()