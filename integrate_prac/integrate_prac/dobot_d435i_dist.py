import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import face_recognition

# Dobot 액션 메시지 임포트
from dobot_msgs.action import PointToPoint

# 1번, 2번, 3번 위치 데이터를 mm 및 degree(X, Y, Z, R)로 변환하여 적용
POINTS = [
    [105.97, -130.65, 42.28, -50.96], # 1번 위치 (30cm 이내)
    [175.94, 13.36, 18.44, 4.34],     # 2번 위치 (40cm 이내)
    [103.54, 149.67, 24.44, 55.33],   # 3번 위치 (50cm 이내)
]

class FaceDistanceDobotNode(Node):
    def __init__(self):
        super().__init__('face_distance_dobot_node')
        
        # 1. RGB 및 Aligned Depth 데이터 구독
        self.color_subscription = self.create_subscription(
            Image, '/camera/camera/color/image_raw', self.color_callback, 10)
        self.depth_subscription = self.create_subscription(
            Image, '/camera/camera/aligned_depth_to_color/image_raw', self.depth_callback, 10)
        
        self.bridge = CvBridge()
        self.latest_color = None
        self.latest_depth = None

        # 2. Dobot PTP Action Client 생성
        self._action_client = ActionClient(self, PointToPoint, 'PTP_action')
        
        # 로봇 제어 상태 관리 (똑같은 위치로 중복 이동하는 것을 방지)
        self.current_target = None

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
            depth_resized = cv2.resize(
                self.latest_depth, (640, 480), interpolation=cv2.INTER_NEAREST)
            
            rgb_frame = cv2.cvtColor(color_resized, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            target_number = None

            for face_location in face_locations:
                top, right, bottom, left = face_location
                center_x = (left + right) // 2
                center_y = (top + bottom) // 2
                
                depth_value_mm = depth_resized[center_y, center_x]
                
                if depth_value_mm > 0:
                    distance_m = depth_value_mm / 1000.0
                    
                    # 거리 범위에 따른 숫자 할당
                    if distance_m <= 0.3:    # 30cm 이내
                        target_number = 1
                    elif distance_m <= 0.4:  # 40cm 이내
                        target_number = 2
                    elif distance_m <= 0.5:  # 50cm 이내
                        target_number = 3
                    
                    if target_number is not None:
                        label = f"Dist: {distance_m:.2f}m -> Target: {target_number}"
                    else:
                        label = f"Dist: {distance_m:.2f}m -> Out of range"
                        
                else:
                    label = "Unknown dist"
                
                # 시각화 (바운딩 박스, 중심점, 텍스트)
                cv2.rectangle(color_resized, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.circle(color_resized, (center_x, center_y), 5, (0, 0, 255), -1)
                cv2.putText(color_resized, label, (left, top - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # 한 프레임에 얼굴 하나만 기준으로 제어
                break 

            cv2.imshow("Face Distance & Dobot Control", color_resized)
            cv2.waitKey(1)

            # --- [Dobot 제어 트리거] ---
            # 목표 숫자가 할당되었고, 이전과 다른 새로운 목표일 때만 이동 명령 전송
            if target_number is not None and target_number != self.current_target:
                self.get_logger().info(f'--- Object detected at target {target_number}. Moving Dobot! ---')
                self.current_target = target_number
                # 리스트 인덱스는 0부터 시작하므로 target_number - 1
                self.send_goal(target=POINTS[target_number - 1], mode=1)

    # -----------------------------------------------------------------
    # 원본 Action Client 함수 유지 구역
    # -----------------------------------------------------------------
    def send_goal(self, target, mode):
        self.get_logger().info('Waiting for action server...')
        self._action_client.wait_for_server()

        goal_msg = PointToPoint.Goal()
        goal_msg.target_pose = target
        goal_msg.motion_type = mode
        self.get_logger().info(f'Sending goal request... Target: {target}')

        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback)

        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected :(')
            return

        self._goal_handle = goal_handle
        self.get_logger().info('Goal accepted :)')

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info('Result: {0}'.format(result))

    def feedback_callback(self, feedback):
        # 로깅이 너무 많이 뜨는 것을 방지하려면 주석 처리해도 무방합니다.
        # self.get_logger().info('Received feedback: {0}'.format(feedback.feedback.current_pose))
        pass

def main(args=None):
    rclpy.init(args=args)

    node = FaceDistanceDobotNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node stopped cleanly")
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()