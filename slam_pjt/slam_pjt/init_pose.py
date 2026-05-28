import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped

def main():
    # 1. Initialize ROS 2
    rclpy.init()
    
    # 2. Create Navigator
    navigator = BasicNavigator()

    # 3. Create Initial Pose
    # [IMPORTANT] Ensure these coordinates match the robot's spawn location in Gazebo
    initial_pose = PoseStamped()
    initial_pose.header.frame_id = 'map'
    initial_pose.header.stamp = navigator.get_clock().now().to_msg()
    
    # Position (x, y) and Orientation (z, w)
    # Usually (0,0) if you didn't change the spawn point
    initial_pose.pose.position.x = 0.0
    initial_pose.pose.position.y = 0.0
    initial_pose.pose.orientation.z = 0.0
    initial_pose.pose.orientation.w = 1.0

    # 4. Set Initial Pose
    print(f"Setting initial pose to (x={initial_pose.pose.position.x}, y={initial_pose.pose.position.y})...")
    navigator.setInitialPose(initial_pose)

    # 5. Wait for Nav2 to activate
    # This checks if AMCL accepted the pose and became active.
    print("Waiting for Nav2 to activate...")
    navigator.waitUntilNav2Active()

    print("Nav2 is now ACTIVE and ready for commands.")
    
    # Exit
    # navigator.lifecycleShutdown()
    exit(0)

if __name__ == '__main__':
    main()