# waypoints_follower.py의 목표는 
# 유저의 키보드 입력을 받아서 이동시키는 건데, 
# A, B, C의 입력은 하나씩 받았어요. waypoints_move는..
# waypoints_follower의 목표는, A B C A C 이런식으로 받아도 
# A -> B -> C -> A -> C 이렇게 이동하도록. 
# waypoints_move.py 코드를 레퍼런스 삼아서 개발하세요. 

import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped

# Define your locations here [x, y, z, w]
WAYPOINTS = {
    "A": [-0.518, -0.769, 0.0, 1.0],
    "B": [-3.87, 0.7, 0.0, 1.0],
    "C": [-0.463, 3.92, 0.0, 1.0],
    "D": [-4.4, 3.28, 0.0, 1.0],
    "E": [-1.64, 5.83, 0.0, 1.0]
}

def main():
    # 1. Initialize ROS 2
    rclpy.init()
    navigator = BasicNavigator()

    # 2. Verify Nav2 is Active
    navigator.waitUntilNav2Active()
    print("[INFO] Nav2 is Ready!")

    # 3. Continuous Loop
    while True:
        print("\n" + "="*50)
        print(f"Available Locations: {list(WAYPOINTS.keys())}")
        print("Enter locations separated by space (e.g., A B C A C) or 'q' to quit: ", end="")
        
        user_input = input().strip()

        if user_input.lower() == 'q':
            print("[INFO] Exiting...")
            break

        # 4. 입력 문자열 파싱 (공백이나 쉼표 기준으로 분리)
        sequence = user_input.replace(',', ' ').split()
        
        if not sequence:
            continue

        # 5. 입력된 경로의 유효성 검증
        invalid_points = [wp for wp in sequence if wp not in WAYPOINTS]
        if invalid_points:
            print(f"[WARN] Unknown locations found: {invalid_points}. Please try again.")
            continue
        
        print(f"\n[INFO] Starting sequence: {' -> '.join(sequence)}")

        # 6. 순차적 이동 실행
        for wp_key in sequence:
            target = WAYPOINTS[wp_key]
            target_x = target[0]
            target_y = target[1]
            target_w = target[3]

            goal_pose = PoseStamped()
            goal_pose.header.frame_id = 'map'
            goal_pose.header.stamp = navigator.get_clock().now().to_msg()
            goal_pose.pose.position.x = target_x
            goal_pose.pose.position.y = target_y
            goal_pose.pose.orientation.w = target_w

            print(f"\n[INFO] Moving to '{wp_key}' (x={target_x}, y={target_y})...")
            navigator.goToPose(goal_pose)

            # Wait for task to complete
            while not navigator.isTaskComplete():
                pass

            # Check Result
            result = navigator.getResult()
            if result == TaskResult.SUCCEEDED:
                print(f"[INFO] Reached '{wp_key}' successfully!")
            else:
                print(f"[ERROR] Failed to reach '{wp_key}'. Canceling the rest of the sequence!")
                break  # 이동에 실패하면 남은 경로 이동을 취소하고 다시 입력을 받음

    # Shutdown
    # navigator.lifecycleShutdown()
    rclpy.shutdown()
    exit(0)

if __name__ == '__main__':
    main()