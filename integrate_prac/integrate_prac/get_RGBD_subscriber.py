import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

class ImageSubscriber(Node):
    def __init__(self):
        super().__init__('image_subscriber')
        
        # RGB 데이터 구독
        self.color_subscription = self.create_subscription(
            Image,
            '/camera/camera/color/image_raw',
            self.color_callback,
            10)
            
        # Depth 데이터 구독
        self.depth_subscription = self.create_subscription(
            Image,
            '/camera/camera/depth/image_rect_raw',
            self.depth_callback,
            10)
        
        self.bridge = CvBridge()
        
        # 최신 이미지를 저장할 변수 초기화
        self.latest_color = None
        self.latest_depth = None

    def color_callback(self, msg):
        # RGB 이미지가 들어오면 변수에 저장하고 출력 함수 호출
        self.latest_color = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.display_images()

    def depth_callback(self, msg):
        # Depth 이미지가 들어오면 변수에 저장하고 출력 함수 호출
        self.latest_depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='16UC1')
        self.display_images()

    def display_images(self):
        # RGB와 Depth 데이터가 모두 한 번 이상 들어왔을 때만 실행
        if self.latest_color is not None and self.latest_depth is not None:
            
            # 각각 640x480 해상도로 리사이즈
            color_resized = cv2.resize(self.latest_color, (640, 480))
            depth_resized = cv2.resize(self.latest_depth, (640, 480))
            
            # Depth 이미지를 시각화를 위해 8비트 컬러맵으로 변환
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_resized, alpha=0.03), cv2.COLORMAP_JET)
            
            # 두 이미지를 가로로 합침
            combined_image = np.hstack((color_resized, depth_colormap))
            
            # 윈도우 출력
            cv2.imshow("Camera Image", combined_image)
            cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)

    image_subscriber = ImageSubscriber()

    try:
        rclpy.spin(image_subscriber)
    except KeyboardInterrupt:
        image_subscriber.get_logger().info("Node stopped cleanly")
    except Exception as e:
        image_subscriber.get_logger().error(f"Error: {str(e)}")
    finally:
        image_subscriber.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()