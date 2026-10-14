#!/usr/bin/env python3
import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


SAFE_DISTANCE = 1.0
TARGET_SPEED = 0.8
TURN_SPEED = 0.6
SCAN_ANGLE_LIMIT = 60


def choose_twist(ranges):
    if not ranges:
        return Twist()

    front_slice = ranges[180 - SCAN_ANGLE_LIMIT:180 + SCAN_ANGLE_LIMIT]
    min_front = min(front_slice) if front_slice else math.inf
    if math.isinf(min_front) or min_front > SAFE_DISTANCE:
        cmd = Twist()
        cmd.linear.x = TARGET_SPEED
        cmd.angular.z = 0.0
        return cmd

    left_slice = ranges[180:360]
    right_slice = ranges[0:180]
    left_d = min(left_slice) if left_slice else math.inf
    right_d = min(right_slice) if right_slice else math.inf

    cmd = Twist()
    if left_d < SAFE_DISTANCE and right_d < SAFE_DISTANCE:
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        return cmd

    if left_d > right_d:
        cmd.linear.x = 0.2
        cmd.angular.z = TURN_SPEED
    else:
        cmd.linear.x = 0.2
        cmd.angular.z = -TURN_SPEED
    return cmd


class LidarAvoidNode(Node):
    def __init__(self):
        super().__init__('lidar_avoid_node')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscription_ = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.get_logger().info('LiDAR obstacle avoidance node started')

    def scan_callback(self, msg):
        ranges = list(msg.ranges)
        cmd = choose_twist(ranges)
        self.publisher_.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = LidarAvoidNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
