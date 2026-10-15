import os
import uuid

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, LogInfo, TimerAction


def generate_launch_description():
    share = get_package_share_directory('campus_robot_bringup')
    world = os.path.join(share, 'worlds', 'campus.world')
    model = os.path.join(share, 'models', 'campus_robot', 'model.sdf')
    # Isolate this run from any old Gazebo server left behind after a GUI freeze.
    gz_partition = 'campus_drive_' + uuid.uuid4().hex[:8]
    gz_environment = {'GZ_PARTITION': gz_partition}
    # A separate ROS domain also prevents old autonomy nodes from fighting this run.
    ros_domain_id = str(1 + int(uuid.uuid4().hex[:4], 16) % 232)
    run_environment = {**gz_environment, 'ROS_DOMAIN_ID': ros_domain_id}

    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-r', '-v', '3', world],
        additional_env=run_environment,
        output='screen'
    )
    bridge = TimerAction(period=3.0, actions=[ExecuteProcess(cmd=[
        'ros2', 'run', 'ros_gz_bridge', 'parameter_bridge',
        '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
        '/world/campus_world/create@ros_gz_interfaces/srv/SpawnEntity',
        '/world/campus_world/remove@ros_gz_interfaces/srv/DeleteEntity'
    ], additional_env=run_environment, output='screen')])
    spawn = TimerAction(period=5.0, actions=[ExecuteProcess(cmd=[
        'ros2', 'run', 'ros_gz_sim', 'create', '-world', 'campus_world',
        '-file', model, '-name', 'campus_robot', '-x', '-3.8', '-y', '1.7', '-z', '0.12'
    ], additional_env=run_environment, output='screen')])
    evaluation = TimerAction(period=6.0, actions=[ExecuteProcess(
        cmd=['ros2', 'run', 'campus_robot_bringup', 'campus_evaluation.py'],
        additional_env=run_environment, output='screen')])
    autonomy = TimerAction(period=7.0, actions=[ExecuteProcess(
        cmd=['ros2', 'run', 'campus_robot_bringup', 'campus_autonomy.py'],
        additional_env=run_environment, output='screen')])
    display = TimerAction(period=8.0, actions=[ExecuteProcess(
        cmd=['ros2', 'run', 'campus_robot_bringup', 'campus_status_display.py'],
        additional_env=run_environment, output='screen')])
    domain_notice = LogInfo(msg=f'Campus simulation ROS_DOMAIN_ID={ros_domain_id}; use this value in other ROS terminals.')
    return LaunchDescription([domain_notice, gazebo, bridge, spawn, evaluation, autonomy, display])
