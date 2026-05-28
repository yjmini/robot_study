#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
import time
import threading

# 사용자 환경에 맞는 패키지에서 Action 메시지 임포트
from dobot_msgs.action import PointToPoint

class PTP_MOVE(Node):

    def __init__(self):
        super().__init__('dobot_PTP_client')
        # Action Client 생성
        self._action_client = ActionClient(self, PointToPoint, '/PTP_action')

    def cancel_done(self, future):
        self.get_logger().info('Goal canceled.')

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected by server.')
            return

        self.get_logger().info('Goal accepted. Robot is moving...')
        
        # 목표가 수락되면 결과를 기다리는 비동기 요청
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)
    
    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Goal reached! Result: {result}')

    def feedback_callback(self, feedback_msg):
        # CLI의 --feedback 옵션과 동일한 역할
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Feedback: {feedback}')

    def timer_callback(self):
        pass
        
    def send_goal(self, target, mode):
        self.get_logger().info('Waiting for action server...')
        self._action_client.wait_for_server()

        # Goal 메시지 설정 및 파라미터 매핑
        goal_msg = PointToPoint.Goal()
        goal_msg.motion_type = mode
        goal_msg.target_pose = target
        goal_msg.velocity_ratio = 0.5       # 고정 파라미터 적용
        goal_msg.acceleration_ratio = 0.3   # 고정 파라미터 적용

        self.get_logger().info(f'Sending goal request: target={target}, mode={mode}')
        
        # 비동기로 Goal 전송 (feedback 콜백 연결)
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback)
        
        # 서버의 수락/거절 응답을 받을 콜백 연결
        self._send_goal_future.add_done_callback(self.goal_response_callback)


def main(args=None):
    rclpy.init(args=args)

    action_client = PTP_MOVE()

    # 💡 [핵심 최적화] 백그라운드 스레드에서 rclpy.spin()을 실행
    # 메인 코드가 time.sleep()으로 대기하는 동안에도 통신(피드백 등)을 실시간으로 처리합니다.
    spin_thread = threading.Thread(target=rclpy.spin, args=(action_client,))
    spin_thread.start()

    # --- 기존 스켈레톤 코드의 메인 로직 완벽 유지 ---
    action_client.send_goal(target = [150.0, 50.0, 100.0, 0.0], mode = 1)
    time.sleep(2)
    action_client.send_goal(target = [200.0, 0.0, 100.0, 0.0], mode = 1)
    time.sleep(2)
    action_client.send_goal(target = [150.0, 50.0, 100.0, 0.0], mode = 1)
    time.sleep(2)
    action_client.send_goal(target = [200.0, 0.0, 100.0, 0.0], mode = 1)
    time.sleep(2)
    # ------------------------------------------------

    # 모든 시퀀스가 종료되면 노드를 안전하게 종료하고 스레드를 정리합니다.
    action_client.get_logger().info('All targets sent. Shutting down node...')
    rclpy.shutdown()
    spin_thread.join()

if __name__ == '__main__':
    main()