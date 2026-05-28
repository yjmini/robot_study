#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image

class ImageSubscriberNode(Node):
    def __init__(self):
        super().__init__('image_subscriber_node')

        self.subscription = self.create_subscription(
            Image,
            '/camera/camera/color/image_raw',
            self.image_callback, # 콜백 함수 연결
            10)
        self.subscription  # prevent unused variable warning

        self.get_logger().info('Image Subscriber Node has been started. Waiting for /image_raw messages...')

    def image_callback(self, msg):
        height = msg.height
        width = msg.width
        encoding = msg.encoding
        is_bigendian = msg.is_bigendian
        step = msg.step
        data = msg.data
        data_length = len(data)

        log_msg = (
            f'\n'
            f'Received Image Information: \n'
            f'width: {width}, height: {height}\n'
            f'encoding: {encoding}, is_bigendian: {is_bigendian}, step: {step}\n'
            f'data size: {data_length}\n'
            # f'data info: {data}\n'
        )
        self.get_logger().info(log_msg)

def main(args=None):
    rclpy.init(args=args)
    node = ImageSubscriberNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard Interrupt (SIGINT) received. Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()