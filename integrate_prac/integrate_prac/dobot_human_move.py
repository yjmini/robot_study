import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import face_recognition
import threading
import time

# Dobot 액션 메시지 임포트
from dobot_msgs.action import PointToPoint

# 로봇이 수행할 사전 정의된 좌표 (실제 환경에 맞게 조정 필요)
POSE_HOME = [200.0, 0.0, 50.0, 0.0]      # 초기 위치 (Home)
POSE_POINT = [250.0, 0.0, 20.0, 0.0]     # 가리키는 위치

class FaceDistanceDobotNode(Node):
    def __init__(self):
        super().__init__('face_distance_dobot_node')
        
        # 1. 카메라 데이터 구독
        self.color_subscription = self.create_subscription(
            Image, '/camera/camera/color/image_raw', self.color_callback, 10)
        self.depth_subscription = self.create_subscription(
            Image, '/camera/camera/aligned_depth_to_color/image_raw', self.depth_callback, 10)
        
        self.bridge = CvBridge()
        self.latest_color = None
        self.latest_depth = None

        # 2. Dobot PTP Action Client 생성
        self._action_client = ActionClient(self, PointToPoint, 'PTP_action')
        
        # 로봇 제어 상태 관리
        self.current_action = None
        self.action_thread = None  # 복합 동작(흔들기)을 카메라 멈춤 없이 실행하기 위한 스레드

    def color_callback(self, msg):
        self.latest_color = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        self.process_and_display()

    def depth_callback(self, msg):
        self.latest_depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='16UC1')
        self.process_and_display()

    def process_and_display(self):
        if self.latest_color is not None and self.latest_depth is not None:
            
            color_resized = cv2.resize(self.latest_color, (640, 480))
            depth_resized = cv2.resize(
                self.latest_depth, (640, 480), interpolation=cv2.INTER_NEAREST)
            
            rgb_frame = cv2.cvtColor(color_resized, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # 얼굴 번호를 안정적으로 부여하기 위해 X좌표(왼쪽) 기준으로 정렬 (왼쪽 사람부터 1번)
            face_locations.sort(key=lambda x: x[3])
            
            target_action_key = None

            for idx, face_location in enumerate(face_locations):
                face_id = idx + 1  # 1번부터 시작
                top, right, bottom, left = face_location
                center_x = (left + right) // 2
                center_y = (top + bottom) // 2
                
                depth_value_mm = depth_resized[center_y, center_x]
                
                state = "범위 외"
                distance_cm = 0.0
                
                if depth_value_mm > 0:
                    distance_cm = depth_value_mm / 10.0  # mm를 cm로 변환
                    
                    # 1. 거리 조건 평가
                    if distance_cm <= 30.0:
                        state = "가까움"
                    elif distance_cm <= 40.0:
                        state = "중간"
                    elif distance_cm <= 50.0:
                        state = "멀리"
                
                # 2. 얼굴 번호와 거리 조건에 따른 로봇 행동 결정
                # (가장 우선순위가 높은 동작 하나만 target_action_key에 저장)
                if target_action_key is None and state != "범위 외":
                    if face_id == 1:
                        if state == "가까움":
                            target_action_key = "WAVE_UP_DOWN"
                        elif state == "중간":
                            target_action_key = "POINTING"
                        elif state == "멀리":
                            target_action_key = "HOME"
                    elif face_id >= 2:
                        if state == "가까움":
                            target_action_key = "WAVE_LEFT_RIGHT"
                        elif state in ["중간", "멀리"]:
                            target_action_key = "HOME"

                # 3. 화면 시각화 (ID, 거리, 상태 표시)
                label = f"ID:{face_id} | {distance_cm:.1f}cm | {state}"
                
                cv2.rectangle(color_resized, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.circle(color_resized, (center_x, center_y), 5, (0, 0, 255), -1)
                cv2.putText(color_resized, label, (left, top - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            cv2.imshow("Face Distance & Dobot Control", color_resized)
            cv2.waitKey(1)

            # --- [Dobot 제어 트리거] ---
            # 화면에 얼굴이 없거나 조건에 안 맞으면 초기 위치(HOME)로 복귀
            if target_action_key is None and len(face_locations) == 0:
                target_action_key = "HOME"

            # 새로운 동작이 필요하고, 현재 로봇 스레드가 비어있거나 끝났을 때만 실행
            if target_action_key is not None and target_action_key != self.current_action:
                if self.action_thread is None or not self.action_thread.is_alive():
                    self.get_logger().info(f'>>> Action Change Detected: Triggering {target_action_key}')
                    self.current_action = target_action_key
                    
                    # 로봇 동작 스레드 시작
                    self.action_thread = threading.Thread(target=self.run_robot_action, args=(target_action_key,))
                    self.action_thread.start()

    # -----------------------------------------------------------------
    # 복합 로봇 동작 실행 스레드 (time.sleep을 써도 카메라가 안 멈춤)
    # -----------------------------------------------------------------
    def run_robot_action(self, action_key):
        if action_key == "WAVE_UP_DOWN":
            self.get_logger().info("Action: 1번 얼굴 가까움 -> 위아래 흔들기")
            self.send_goal_direct([200.0, 0.0, 80.0, 0.0])
            time.sleep(1.0)
            self.send_goal_direct([200.0, 0.0, 20.0, 0.0])
            time.sleep(1.0)
            self.send_goal_direct([200.0, 0.0, 80.0, 0.0])
            
        elif action_key == "POINTING":
            self.get_logger().info("Action: 1번 얼굴 중간 -> 가리키기")
            self.send_goal_direct(POSE_POINT)
            
        elif action_key == "WAVE_LEFT_RIGHT":
            self.get_logger().info("Action: 2번 이상 얼굴 가까움 -> 좌우 흔들기")
            self.send_goal_direct([200.0, 50.0, 50.0, 0.0])
            time.sleep(1.0)
            self.send_goal_direct([200.0, -50.0, 50.0, 0.0])
            time.sleep(1.0)
            self.send_goal_direct([200.0, 50.0, 50.0, 0.0])
            
        elif action_key == "HOME":
            self.get_logger().info("Action: 멀리 있음 or 얼굴 없음 -> 초기 위치 복귀")
            self.send_goal_direct(POSE_HOME)

    # -----------------------------------------------------------------
    # 원본 Action Client 함수 유지 구역
    # -----------------------------------------------------------------
    def send_goal_direct(self, target):
        # 스레드 내부에서 호출하기 쉽도록 기존 send_goal을 감싼 래퍼 함수
        self._action_client.wait_for_server()
        goal_msg = PointToPoint.Goal()
        goal_msg.target_pose = target
        goal_msg.motion_type = 1
        
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected :(')
            return
        self._goal_handle = goal_handle
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        # self.get_logger().info('Result: {0}'.format(result))

    def feedback_callback(self, feedback):
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