import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np

class QRCodeDetectorNode(Node):
    def __init__(self):
        super().__init__('qr_code_detection_node')
        
        # /image_raw 토픽 구독(Subscribe)
        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.image_callback,
            10)
        
        # QR 코드에 담긴 텍스트 데이터를 발행할 퍼블리셔
        self.publisher_ = self.create_publisher(String, '/qr_code_data', 10)
        
        self.bridge = CvBridge()
        self.qr_detector = cv2.QRCodeDetector() # 요구사항: 기본 디텍터 사용
        
        self.get_logger().info('QR Code Detection Node가 시작되었습니다. 웹캠 영상을 대기합니다...')

    def image_callback(self, msg):
        try:
            # ROS 2 Image 메시지를 OpenCV 이미지(BGR)로 변환
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'이미지 변환 오류: {e}')
            return

        # QR 코드 감지 및 디코딩
        data, bbox, _ = self.qr_detector.detectAndDecode(cv_image)

        if data:
            # 1. 감지된 데이터 퍼블리시
            msg_str = String()
            msg_str.data = data
            self.publisher_.publish(msg_str)
            self.get_logger().info(f'QR 코드 인식됨: "{data}"')

            # 2. 결과 시각화 (바운딩 박스 및 텍스트)
            if bbox is not None:
                bbox = np.int32(bbox).reshape(-1, 2)
                
                # 4개의 꼭짓점을 초록색 선으로 연결
                for i in range(len(bbox)):
                    pt1 = tuple(bbox[i])
                    pt2 = tuple(bbox[(i + 1) % len(bbox)])
                    cv2.line(cv_image, pt1, pt2, color=(0, 255, 0), thickness=3)
                
                # 디코딩된 텍스트를 화면에 출력
                cv2.putText(cv_image, data, (bbox[0][0], bbox[0][1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 결과 이미지 화면 출력
        cv2.imshow('QR Code Detection Result', cv_image)
        cv2.waitKey(1) 

def main(args=None):
    rclpy.init(args=args)
    node = QRCodeDetectorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('QR 코드 감지 노드를 종료합니다.')
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()