import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from std_msgs.msg import String
from geometry_msgs.msg import Point, TransformStamped # Point와 TF 메시지 추가
from tf2_ros import TransformBroadcaster # TF 브로드캐스터 추가

import torch
from cv_bridge import CvBridge
import cv2
import pyrealsense2 as rs # RealSense 제공 함수 사용을 위해 추가

class YOLOv5RealSenseNode(Node):
    def __init__(self):
        super().__init__('yolov5_realsense_node')
        
        # 기존 퍼블리셔 유지
        self.result_publisher = self.create_publisher(String, 'yolov5_results', 10)
        self.image_publisher = self.create_publisher(Image, 'yolov5_image_with_boxes', 10)
        
        # [조건 반영] 1. Point 퍼블리셔 추가 (토픽: /detected_object_coordinates)
        self.coord_publisher = self.create_publisher(Point, '/detected_object_coordinates', 10)
        
        # [조건 반영] 2. TF 브로드캐스터 초기화
        self.tf_broadcaster = TransformBroadcaster(self)
        
        self.bridge = CvBridge()
        
        # [조건 반영] 3. RealSense 깊이(Depth) 및 카메라 파라미터(Intrinsics) 구독
        # RGB 이미지의 픽셀과 매칭하려면 aligned_depth 토픽을 사용하는 것이 가장 정확합니다.
        self.depth_sub = self.create_subscription(Image, '/camera/camera/aligned_depth_to_color/image_raw', self.depth_callback, 10)
        self.info_sub = self.create_subscription(CameraInfo, '/camera/camera/color/camera_info', self.info_callback, 10)
        self.image_subscriber = self.create_subscription(Image, '/camera/camera/color/image_raw', self.image_callback, 10)
        
        # YOLOv5 모델 로드
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        
        self.depth_image = None
        self.intrinsics = None

    def info_callback(self, msg):
        # RealSense의 rs2_deproject_pixel_to_point 함수를 쓰기 위해 Intrinsics 객체 생성
        if self.intrinsics is None:
            self.intrinsics = rs.intrinsics()
            self.intrinsics.width = msg.width
            self.intrinsics.height = msg.height
            self.intrinsics.ppx = msg.k[2]
            self.intrinsics.ppy = msg.k[5]
            self.intrinsics.fx = msg.k[0]
            self.intrinsics.fy = msg.k[4]
            self.intrinsics.model = rs.distortion.none
            self.intrinsics.coeffs = [i for i in msg.d]

    def depth_callback(self, msg):
        # Depth 이미지를 OpenCV 형식으로 변환 (보통 16UC1 포맷)
        try:
            self.depth_image = self.bridge.imgmsg_to_cv2(msg, msg.encoding)
        except Exception as e:
            self.get_logger().error(f"Depth image convert failed: {e}")

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return
        
        results = self.model(cv_image)
        detections = results.pandas().xyxy[0] 

        detection_data = []
        
        for _, row in detections.iterrows():
            label = row['name']
            confidence = row['confidence']
            xmin, ymin, xmax, ymax = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            
            # [조건 반영] 4. 바운딩 박스 중심 좌표 계산
            center_x = int((xmin + xmax) / 2)
            center_y = int((ymin + ymax) / 2)
            
            detection_info = f"Label: {label}, Confidence: {confidence:.2f}, Center: ({center_x}, {center_y})"
            detection_data.append(detection_info)

            # [조건 반영] 5. 상대 좌표 계산 및 퍼블리시
            if self.depth_image is not None and self.intrinsics is not None:
                # 중심점의 깊이 값 추출 (mm 단위일 경우 m 단위로 변환 필요)
                depth_value = self.depth_image[center_y, center_x]
                depth_in_meters = depth_value * 0.001 

                if depth_in_meters > 0:
                    # realsense에서 제공하는 함수 활용해 x, y, z값 획득
                    spatial_coords = rs.rs2_deproject_pixel_to_point(self.intrinsics, [center_x, center_y], depth_in_meters)
                    
                    obj_x, obj_y, obj_z = spatial_coords[0], spatial_coords[1], spatial_coords[2]

                    # ROS 2 퍼블리시 (geometry_msgs/Point)
                    point_msg = Point()
                    point_msg.x = float(obj_x)
                    point_msg.y = float(obj_y)
                    point_msg.z = float(obj_z)
                    self.coord_publisher.publish(point_msg)

                    # [조건 반영] 6. TF 생성 및 pub
                    t = TransformStamped()
                    t.header.stamp = self.get_clock().now().to_msg()
                    t.header.frame_id = 'camera_color_optical_frame'  # 부모 프레임 (카메라 좌표계)
                    t.child_frame_id = label                          # 자식 프레임 (객체 이름)

                    t.transform.translation.x = float(obj_x)
                    t.transform.translation.y = float(obj_y)
                    t.transform.translation.z = float(obj_z)
                    
                    # 객체의 회전은 알 수 없으므로 기본값(단위 쿼터니언) 설정
                    t.transform.rotation.x = 0.0
                    t.transform.rotation.y = 0.0
                    t.transform.rotation.z = 0.0
                    t.transform.rotation.w = 1.0

                    self.tf_broadcaster.sendTransform(t)

            # 이미지에 바운딩 박스 및 중심점 그리기
            cv2.rectangle(cv_image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            cv2.circle(cv_image, (center_x, center_y), 5, (0, 0, 255), -1) # 중심점 시각화
            cv2.putText(cv_image, f"{label} {confidence:.2f}", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        result_message = String()
        result_message.data = '\n'.join(detection_data)
        self.result_publisher.publish(result_message)
        
        try:
            boxed_image_msg = self.bridge.cv2_to_imgmsg(cv_image, encoding="bgr8")
            self.image_publisher.publish(boxed_image_msg)
        except Exception as e:
            self.get_logger().error(f"Failed to publish image: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = YOLOv5RealSenseNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()