import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class WebcamPublisher(Node):
    def __init__(self):
        super().__init__('webcam_publisher_node')
        
        # /image_raw 토픽으로 이미지를 발행(Publish)
        self.publisher_ = self.create_publisher(Image, '/image_raw', 10)
        
        # 약 30fps(0.033초) 주기로 웹캠 프레임을 읽어오는 타이머
        timer_period = 0.033  
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        # 노트북 내장 웹캠 연결 (일반적으로 0번)
        self.cap = cv2.VideoCapture(0)
        self.bridge = CvBridge()
        
        self.get_logger().info('웹캠 퍼블리셔 노드가 시작되었습니다. (/image_raw 발행 중)')

    def timer_callback(self):
        ret, frame = self.cap.read()
        
        if ret:
            # OpenCV 이미지(BGR)를 ROS 2 Image 메시지로 변환하여 퍼블리시
            msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            self.publisher_.publish(msg)
        else:
            self.get_logger().warning('웹캠에서 프레임을 읽어올 수 없습니다.')

def main(args=None):
    rclpy.init(args=args)
    node = WebcamPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('웹캠 퍼블리셔 노드를 종료합니다.')
    finally:
        node.cap.release()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()