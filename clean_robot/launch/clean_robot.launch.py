from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    rviz_config_file = '/home/ssafy/ssafy_ws/src/clean_robot/rviz/clean_robot.rviz'
    
    # URDF 파일 경로
    urdf_file = '/home/ssafy/ssafy_ws/src/clean_robot/urdf/clean_robot.urdf'

    with open(urdf_file, 'r') as infp:
        robot_description = infp.read()
    
    print(robot_description)

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description}]
        ),

        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            output='screen',
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config_file]
        )
    ])