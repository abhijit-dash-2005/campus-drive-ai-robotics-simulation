#!/usr/bin/env python3
"""Waypoint navigation with a simple LiDAR reactive obstacle layer."""
import math
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String


def clamp(value, low, high):
    return max(low, min(high, value))


def angle_error(target, current):
    return math.atan2(math.sin(target - current), math.cos(target - current))


class CampusAutonomy(Node):
    def __init__(self):
        super().__init__('campus_autonomy')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.done_pub = self.create_publisher(Bool, '/campus_navigation/succeeded', 10)
        self.status_pub = self.create_publisher(String, '/campus_navigation/status', 10)
        self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.waypoints = [(0.0, 2.0), (3.5, 2.0), (3.5, 1.5), (-3.5, 1.5), (-3.5, 2.0), (0.0, 2.0), (0.0, 0.0)]
        self.goal_index = 0
        self.pose = None
        self.yaw = 0.0
        self.scan = None
        self.scan_time = 0.0
        self.odom_time = 0.0
        self.avoid_until = 0.0
        self.avoid_turn = 0.65
        self.completed = False
        self.mode = 'auto'
        self.create_subscription(String, '/campus_navigation/mode', self.mode_cb, 10)
        self.timer = self.create_timer(0.1, self.step)
        self.get_logger().info(f'Waypoint navigation started: {len(self.waypoints)} campus goals')

    def mode_cb(self, msg):
        requested = msg.data.strip().lower()
        if requested in ('auto', 'manual') and requested != self.mode:
            self.mode = requested
            if self.mode == 'manual':
                self.publish()
            self.get_logger().info(f'Control mode: {self.mode}')

    def scan_cb(self, msg):
        self.scan = msg
        self.scan_time = time.monotonic()

    def odom_cb(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self.pose = (p.x, p.y)
        self.yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self.odom_time = time.monotonic()

    def sector_min(self, start, end):
        if self.scan is None:
            return 0.0
        vals = [v for v in self.scan.ranges[start:end] if math.isfinite(v) and self.scan.range_min <= v <= self.scan.range_max]
        return min(vals) if vals else self.scan.range_max

    def publish(self, linear=0.0, angular=0.0):
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.cmd_pub.publish(msg)

    def step(self):
        if self.mode == 'manual':
            return
        now = time.monotonic()
        if self.completed:
            self.publish()
            return
        if self.pose is None or self.scan is None or now - self.odom_time > 1.0 or now - self.scan_time > 1.0:
            self.publish()
            return
        if self.goal_index >= len(self.waypoints):
            self.completed = True
            self.publish()
            self.done_pub.publish(Bool(data=True))
            self.status_pub.publish(String(data='Campus route complete'))
            self.get_logger().info('Campus route complete')
            return

        gx, gy = self.waypoints[self.goal_index]
        dx, dy = gx - self.pose[0], gy - self.pose[1]
        distance = math.hypot(dx, dy)
        if distance < 0.35:
            self.get_logger().info(f'Reached waypoint {self.goal_index + 1}/{len(self.waypoints)}')
            self.goal_index += 1
            self.publish()
            return

        front = self.sector_min(150, 210)
        left = self.sector_min(210, 300)
        right = self.sector_min(60, 150)
        target_yaw = math.atan2(dy, dx)
        error = angle_error(target_yaw, self.yaw)

        # First face the waypoint while stationary. This prevents an obstacle
        # beside the robot from sending it into a long series of avoidance turns.
        if abs(error) > 0.65:
            self.avoid_until = 0.0
            self.publish(0.0, clamp(1.5 * error, -0.8, 0.8))
        else:
            if front < 1.0 and now >= self.avoid_until:
                self.avoid_turn = 0.65 if left >= right else -0.65
                self.avoid_until = now + (0.8 if front < 0.5 else 1.1)
                self.get_logger().info(f'Obstacle at {front:.2f} m; turning to clear it')
            if now < self.avoid_until:
                # Creep around obstacles, but stop forward motion at close range.
                self.publish(0.08 if front >= 0.60 else 0.0, self.avoid_turn)
            elif front < 0.60:
                self.publish(0.0, self.avoid_turn)
            else:
                angular = clamp(1.4 * error, -0.7, 0.7)
                linear = min(0.45, 0.22 * distance)
                self.publish(linear, angular)
        self.status_pub.publish(String(data=f'waypoint {self.goal_index + 1}/{len(self.waypoints)} distance {distance:.2f} m'))


def main(args=None):
    rclpy.init(args=args)
    node = CampusAutonomy()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except RuntimeError:
        if rclpy.ok():
            raise
    finally:
        # Launch may already have shut down this ROS context during Ctrl+C.
        if rclpy.ok():
            try:
                node.publish()
            except Exception:
                pass
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
