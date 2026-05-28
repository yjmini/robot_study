#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Imu

class ImuSubscriberNode(Node):
    def __init__(self):
        super().__init__('imu_subscriber_node')

        self.subscription = self.create_subscription(
            Imu,
            '/imu',
            self.imu_callback, # 콜백 함수 연결
            10)
        self.subscription  # prevent unused variable warning

        self.get_logger().info('IMU Subscriber Node has been started. Waiting for /imu messages...')

    def imu_callback(self, msg):
        ori_x = msg.orientation.x
        ori_y = msg.orientation.y
        ori_z = msg.orientation.z
        ori_w = msg.orientation.w

        ang_z = msg.angular_velocity.z

        log_msg = (
            f'X: {ori_x: .3f}, Y: {ori_y: .3f}, Z: {ori_z: .3f}, W: {ori_w: .3f}'
            f'Ang.Z: {ang_z: .3f}'
        )
        self.get_logger().info(log_msg)

def main(args=None):
    rclpy.init(args=args)
    node = ImuSubscriberNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard Interrupt (SIGINT) received. Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()