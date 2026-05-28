import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped

def main():
    # 1. Initialize ROS 2
    rclpy.init()
    
    # 2. Create Navigator
    navigator = BasicNavigator()

    # 3. Check Nav2 Status
    print("[DEBUG] Checking Nav2 active status...")
    # If this hangs here, it means Nav2 is not fully launched or crashed.
    navigator.waitUntilNav2Active()
    print("[DEBUG] Nav2 is ACTIVE.")

    # 4. Set Goal
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = 'map'
    goal_pose.header.stamp = navigator.get_clock().now().to_msg()

    # [TEST COORDINATES]
    # Ensure these coordinates are VALID (empty space) in your map.
    goal_pose.pose.position.x = 0.0
    goal_pose.pose.position.y = 0.0
    goal_pose.pose.orientation.w = 1.0

    print(f"[DEBUG] Sending Goal: (x={goal_pose.pose.position.x}, y={goal_pose.pose.position.y})")
    
    # 5. Send Goal
    navigator.goToPose(goal_pose)

    # 6. Monitor Loop with Timeout
    i = 0
    while not navigator.isTaskComplete():
        i += 1
        feedback = navigator.getFeedback()

        if feedback and i % 5 == 0:
            print(f"[INFO] Distance remaining: {feedback.distance_remaining:.2f} meters")
            
            # If distance is not changing for a long time, the robot might be stuck.
            if feedback.distance_remaining < 0.1:
                print("[INFO] Very close to target...")

    # 7. Detailed Result Analysis
    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        print("[SUCCESS] Goal reached!")
    elif result == TaskResult.CANCELED:
        print("[CANCELED] Goal was canceled. Check if another node canceled it.")
    elif result == TaskResult.FAILED:
        print("[FAILED] Goal failed!")
        print("  - Possible Reason 1: Goal is inside a wall/obstacle (Check Costmap).")
        print("  - Possible Reason 2: Robot is stuck.")
        print("  - Possible Reason 3: Path planning failed (No valid path found).")

    # navigator.lifecycleShutdown()
    exit(0)

if __name__ == '__main__':
    main()