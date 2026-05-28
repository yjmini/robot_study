#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState

class DobotJointSubscriberNode(Node):
    def __init__(self):
        super().__init__('dobot_joint_subscriber_node')

        self.subscription = self.create_subscription(
            JointState,
            '/dobot_joint_states',
            self.joint_callback, # 콜백 함수 연결
            10)
        self.subscription  # prevent unused variable warning

        self.get_logger().info('Joint Subscriber Node has been started. Waiting for /dobot_joint_states messages...')

    def joint_callback(self, msg):
        names = msg.name
        joints = msg.position

        log_msg = (
            f'\n'
            f'Received Joint Information: \n'
        )

        for name, pos in zip(names, joints):
            log_msg += f'{name}: {pos}\n'

        self.get_logger().info(log_msg)

def main(args=None):
    rclpy.init(args=args)
    node = DobotJointSubscriberNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard Interrupt (SIGINT) received. Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()