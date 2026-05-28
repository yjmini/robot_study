import cv2
import numpy as np
import pyrealsense2 as rs
import rclpy
from rclpy.node import Node

from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped, Point
from std_msgs.msg import Header

# Haar Cascade 로드
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)


def detect_faces(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=8, minSize=(60, 60)
    )
    return faces


def get_3d_coordinates(depth_frame, depth_intrin, pixel):
    depth = depth_frame.get_distance(pixel[0], pixel[1])
    point = rs.rs2_deproject_pixel_to_point(depth_intrin, pixel, depth)
    return point


class FaceTFBroadcaster(Node):
    def __init__(self):
        super().__init__('face_tf_broadcaster')
        self.tf_broadcaster = TransformBroadcaster(self)
        self.point_publisher = self.create_publisher(Point, '/detected_object_coordinates', 10)

    def publish_tf(self, frame_id, child_frame_id, translation):
        t = TransformStamped()
        t.header = Header()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = frame_id
        t.child_frame_id = child_frame_id
        t.transform.translation.x = translation[0]
        t.transform.translation.y = translation[1]
        t.transform.translation.z = translation[2]
        t.transform.rotation.w = 1.0

        self.tf_broadcaster.sendTransform(t)

    def publish_point(self, point):
        msg = Point()
        msg.x = point[0]
        msg.y = point[1]
        msg.z = point[2]
        self.point_publisher.publish(msg)


def main():
    rclpy.init()
    node = FaceTFBroadcaster()

    # RealSense 카메라 설정
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    pipeline.start(config)

    try:
        while rclpy.ok():
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics

            faces = detect_faces(color_image)

            # 가장 큰 얼굴 하나만 사용
            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                center = (x + w // 2, y + h // 2)
                point_3d = get_3d_coordinates(depth_frame, depth_intrin, center)

                node.publish_tf('camera_link', 'face_0', point_3d)
                node.publish_point(point_3d)

                # 시각화
                cv2.rectangle(color_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(color_image, center, 5, (0, 0, 255), -1)
                cv2.putText(color_image, f'face_0  Z={point_3d[2]:.2f}m',
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            # 검출된 얼굴 수 표시
            cv2.putText(color_image, f'Faces: {len(faces)}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            # 영상 출력
            cv2.imshow('Face Detection', color_image)

            # 'q' 키로 종료
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            rclpy.spin_once(node, timeout_sec=0.01)

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
