import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import face_recognition

class FaceDistanceNode(Node):
    def __init__(self):
        super().__init__('face_distance_node')
        
        # RGB 데이터 구독
        self.color_subscription = self.create_subscription(
            Image,
            '/camera/camera/color/image_raw',
            self.color_callback,
            10)
            
        # RGB 시점에 맞게 정렬된(Aligned) Depth 토픽 구독
        self.depth_subscription = self.create_subscription(
            Image,
            '/camera/camera/aligned_depth_to_color/image_raw', 
            self.depth_callback,
            10)
        
        self.bridge = CvBridge()
        self.latest_color = None
        self.latest_depth = None

    def color_callback(self, msg):
        self.latest_color = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.process_and_display()

    def depth_callback(self, msg):
        self.latest_depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='16UC1')
        self.process_and_display()

    def process_and_display(self):
        if self.latest_color is not None and self.latest_depth is not None:
            
            # 해상도를 640x480으로 통일
            color_resized = cv2.resize(self.latest_color, (640, 480))
            
            # Depth 리사이즈 시 픽셀이 섞이지 않도록 INTER_NEAREST 옵션 적용
            depth_resized = cv2.resize(
                self.latest_depth, 
                (640, 480), 
                interpolation=cv2.INTER_NEAREST
            )
            
            rgb_frame = cv2.cvtColor(color_resized, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            for face_location in face_locations:
                top, right, bottom, left = face_location
                center_x = (left + right) // 2
                center_y = (top + bottom) // 2
                
                depth_value_mm = depth_resized[center_y, center_x]
                
                # 깊이 값이 0인 경우(측정 실패) 예외 처리
                if depth_value_mm == 0:
                    label = "Face: Unknown dist"
                else:
                    distance_m = depth_value_mm / 1000.0
                    label = f"Face: {distance_m:.2f}m"
                
                # RGB 이미지에 시각화 (바운딩 박스, 중심점, 텍스트)
                cv2.rectangle(color_resized, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.circle(color_resized, (center_x, center_y), 5, (0, 0, 255), -1)
                cv2.putText(color_resized, label, (left, top - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # RGB 이미지만 출력
            cv2.imshow("Face Distance Viewer", color_resized)
            cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    face_distance_node = FaceDistanceNode()

    try:
        rclpy.spin(face_distance_node)
    except KeyboardInterrupt:
        pass
    finally:
        face_distance_node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()