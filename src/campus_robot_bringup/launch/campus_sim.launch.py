import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction


def generate_launch_description():
    share = get_package_share_directory('campus_robot_bringup')
    world = os.path.join(share, 'worlds', 'campus.world')
    model = os.path.join(share, 'models', 'campus_robot', 'model.sdf')

    gazebo = ExecuteProcess(cmd=['gz', 'sim', '-r', '-v', '3', world], output='screen')
    bridge = TimerAction(period=3.0, actions=[ExecuteProcess(cmd=[
        'ros2', 'run', 'ros_gz_bridge', 'parameter_bridge',
        '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
        '/world/campus_world/create@ros_gz_interfaces/srv/SpawnEntity',
        '/world/campus_world/remove@ros_gz_interfaces/srv/DeleteEntity'
    ], output='screen')])
    spawn = TimerAction(period=5.0, actions=[ExecuteProcess(cmd=[
        'ros2', 'run', 'ros_gz_sim', 'create', '-world', 'campus_world',
        '-file', model, '-name', 'campus_robot', '-x', '0', '-y', '0', '-z', '0.15'
    ], output='screen')])
    evaluation = TimerAction(period=6.0, actions=[ExecuteProcess(
        cmd=['ros2', 'run', 'campus_robot_bringup', 'campus_evaluation.py'], output='screen')])
    autonomy = TimerAction(period=7.0, actions=[ExecuteProcess(
        cmd=['ros2', 'run', 'campus_robot_bringup', 'campus_autonomy.py'], output='screen')])
    display = TimerAction(period=8.0, actions=[ExecuteProcess(
        cmd=['ros2', 'run', 'campus_robot_bringup', 'campus_status_display.py'], output='screen')])
    return LaunchDescription([gazebo, bridge, spawn, evaluation, autonomy, display])
