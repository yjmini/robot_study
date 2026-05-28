import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
import time

def main():
    rclpy.init()
    navigator = BasicNavigator()
    navigator.waitUntilNav2Active()

    # 순찰할 경로 리스트 (순서대로 방문)
    patrol_route = [
        [1.5, 0.0, 0.0, 1.0],
        [2.0, 1.0, 0.0, 1.0],
        [0.0, 0.0, 0.0, 1.0]
    ]

    print("[INFO] Start Patrolling... (Press Ctrl+C to stop)")

    while True:  # 무한 루프
        for i, waypoint in enumerate(patrol_route):
            print(f"\n[INFO] Heading to Waypoint {i+1}...")
            
            goal_pose = PoseStamped()
            goal_pose.header.frame_id = 'map'
            goal_pose.header.stamp = navigator.get_clock().now().to_msg()

            goal_pose.pose.position.x = waypoint[0]
            goal_pose.pose.position.y = waypoint[1]
            goal_pose.pose.orientation.z = waypoint[2]
            goal_pose.pose.orientation.w = waypoint[3]
            
            navigator.goToPose(goal_pose)

            while not navigator.isTaskComplete():
                pass # 이동 중...

            result = navigator.getResult()

            if result == TaskResult.SUCCEEDED:
                print(f"[INFO] Waypoint {i+1} Reached! Scanning area for 3 seconds...")
                time.sleep(3) # 3초간 경비(대기) 후 다음 장소로
            else:
                print(f"[ERROR] Failed to reach Waypoint {i+1}. Skipping...")

if __name__ == '__main__':
    main()