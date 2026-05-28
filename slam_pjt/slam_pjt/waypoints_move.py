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
    # (Assuming initial_pose_setter.py was already run)
    navigator.waitUntilNav2Active()
    print("[INFO] Nav2 is Ready!")

    # 3. Continuous Loop
    while True:
        print("\n" + "="*40)
        print(f"Available Locations: {list(WAYPOINTS.keys())}")
        print("Enter location key (or 'q' to quit): ", end="")
        
        user_input = input()

        if user_input == 'q':
            print("[INFO] Exiting...")
            break

        if user_input in WAYPOINTS:
            target = WAYPOINTS[user_input]
            target_x = target[0]
            target_y = target[1]
            target_w = target[3]

            # 4. Create Goal Pose
            goal_pose = PoseStamped()
            goal_pose.header.frame_id = 'map'
            goal_pose.header.stamp = navigator.get_clock().now().to_msg()

            goal_pose.pose.position.x = target_x
            goal_pose.pose.position.y = target_y
            goal_pose.pose.orientation.w = target_w

            # 5. Send Goal
            print(f"[INFO] Moving to '{user_input}' (x={target_x}, y={target_y})...")
            navigator.goToPose(goal_pose)

            # 6. Wait for task to complete
            while not navigator.isTaskComplete():
                pass

            # 7. Check Result
            result = navigator.getResult()
            if result == TaskResult.SUCCEEDED:
                print("[INFO] Goal reached!")
            else:
                print("[ERROR] Goal failed or canceled!")
        else:
            print("[WARN] Unknown location! Please try again.")

    # Shutdown
    # navigator.lifecycleShutdown()
    exit(0)

if __name__ == '__main__':
    main()