#!/usr/bin/env python3
"""Collect simple campus navigation performance metrics and save a CSV."""
import csv
import math
import time
from pathlib import Path

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool


class CampusEvaluation(Node):
    def __init__(self):
        super().__init__('campus_evaluation')
        self.started = time.monotonic()
        self.last_xy = None
        self.path_length = 0.0
        self.scan_count = 0
        self.near_obstacle_scans = 0
        self.stop_commands = 0
        self.min_obstacle = math.inf
        self.min_front_obstacle = math.inf
        self.succeeded = False
        self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_cb, 10)
        self.create_subscription(Bool, '/campus_navigation/succeeded', self.done_cb, 10)
        self.timer = self.create_timer(5.0, self.report_progress)
        self.get_logger().info('Evaluation recorder started')

    def odom_cb(self, msg):
        p = msg.pose.pose.position
        xy = (p.x, p.y)
        if self.last_xy is not None:
            self.path_length += math.hypot(xy[0] - self.last_xy[0], xy[1] - self.last_xy[1])
        self.last_xy = xy

    def scan_cb(self, msg):
        self.scan_count += 1
        values = [v for v in msg.ranges if math.isfinite(v) and msg.range_min <= v <= msg.range_max]
        if values:
            nearest = min(values)
            self.min_obstacle = min(self.min_obstacle, nearest)
            if nearest < 1.0:
                self.near_obstacle_scans += 1
        # Record the closest return in the forward 60-degree field of view.
        front_values = []
        for i, value in enumerate(msg.ranges):
            angle = msg.angle_min + i * msg.angle_increment
            if abs(angle) <= math.radians(30) and math.isfinite(value) and msg.range_min <= value <= msg.range_max:
                front_values.append(value)
        if front_values:
            self.min_front_obstacle = min(self.min_front_obstacle, min(front_values))

    def cmd_cb(self, msg):
        if abs(msg.linear.x) < 0.02 and abs(msg.angular.z) < 0.02:
            self.stop_commands += 1

    def done_cb(self, msg):
        if msg.data and not self.succeeded:
            self.succeeded = True
            self.save_report()

    def report_progress(self):
        self.get_logger().info(f'Evaluation: path={self.path_length:.2f} m, scans={self.scan_count}, near-obstacle scans={self.near_obstacle_scans}')

    def save_report(self):
        output = Path.home() / 'Desktop' / 'campus_ws' / 'results' / 'campus_evaluation.csv'
        output.parent.mkdir(parents=True, exist_ok=True)
        elapsed = time.monotonic() - self.started
        with output.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['elapsed_seconds', 'path_length_m', 'minimum_obstacle_m', 'minimum_front_obstacle_m', 'scan_count', 'near_obstacle_scans', 'stop_commands', 'route_succeeded'])
            writer.writerow([f'{elapsed:.2f}', f'{self.path_length:.3f}', 'none' if math.isinf(self.min_obstacle) else f'{self.min_obstacle:.3f}', 'none' if math.isinf(self.min_front_obstacle) else f'{self.min_front_obstacle:.3f}', self.scan_count, self.near_obstacle_scans, self.stop_commands, self.succeeded])
        if rclpy.ok():
            self.get_logger().info(f'Evaluation saved to {output}')


def main(args=None):
    rclpy.init(args=args)
    node = CampusEvaluation()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except RuntimeError:
        if rclpy.ok():
            raise
    finally:
        if not node.succeeded:
            node.save_report()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
