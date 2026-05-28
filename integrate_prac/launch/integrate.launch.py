from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    # argument 선언 
    dof_arg = DeclareLaunchArgument(
        'DOF', default_value='4', description='Degrees of freedom for the Dobot'
    )

    tool_arg = DeclareLaunchArgument(
        'tool', default_value='suction_cup', description='Tool attached to Dobot'
    )

    # 실제 그 파일의 위치를 불러와서 launch 실행하는 방법
    dobot_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join('/home/ssafy/magician_ros2_control_system_ws/src/dobot_bringup/launch', 'dobot_magician_control_system.launch.py')
        )
    )

    # 실제 명령어를 그대로 입력해서 launch 실행하는 방법
    realsense2_launch = ExecuteProcess(
        cmd=['ros2', 'launch', 'realsense2_camera', 'rs_launch.py'],
        shell=True,
        output='screen',
    )

    # argument 추가해서 파일 위치 불러와서 launch  실행하는 방법 
    display_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join('/home/ssafy/magician_ros2_control_system_ws/src/dobot_description/launch', 'display.launch.py')
        ),
        launch_arguments={
            'DOF': LaunchConfiguration('DOF'),
            'tool': LaunchConfiguration('tool')
        }.items(),
    )

    dobot_homing_service_call = TimerAction(
        period=35.0,
        actions=[
            ExecuteProcess(
                cmd=['ros2', 'service', 'call', '/dobot_homing_service', 'dobot_msgs/srv/ExecuteHomingProcedure'],
                shell=True,
                output='screen',
            )
        ]
    )

    ptp_move_node = TimerAction(
        period=50.0,
        actions=[
            ExecuteProcess(
                cmd=['ros2', 'run', 'integrate_prac', 'ptp_move'],
                shell=True,
                output='screen',
            )
        ]
    )

    suction_cup_node = TimerAction(
        period=60.0,  # Adjust delay as necessary
        actions=[
            ExecuteProcess(
                cmd=['ros2', 'run', 'dobot_control', 'suction_cup_control'],
                shell=True,
                output='screen',
            )
        ]
    )


    return LaunchDescription([
        dof_arg,
        tool_arg,
        dobot_bringup_launch, 
        # TimerAction을 통해 순차적으로 실행되도록 함. 
        TimerAction(period=20.0, actions=[realsense2_launch]),
        TimerAction(period=25.0, actions=[display_launch]),
        dobot_homing_service_call,
        ptp_move_node,
        suction_cup_node,
    ])