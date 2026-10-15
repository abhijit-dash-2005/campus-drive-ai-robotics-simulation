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
        self.obstacle_pub = self.create_publisher(Bool, '/campus_navigation/obstacle_detected', 10)
        self.obstacle_seen = False
        # Gazebo's scan can include the robot's own bumper/body at these ranges.
        self.self_echo_max_range = 0.40
        self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        # S-shaped slalom: pass below block 1, above block 2, then below block 3.
        self.route_world = [
            (-3.2, 1.70),  # line up before block 1
            (-3.2, 0.65),  # pass below block 1
            (-1.35, 0.65), # move between blocks 1 and 2
            (-1.35, 2.75), # pass to the left of block 2, then above it
            (1.35, 2.75),  # cross above block 2
            (1.35, 0.65),  # pass to the right of block 2, then below block 3
            (3.2, 0.65),   # pass below block 3
            (3.2, 1.70),   # return to the east-side campus path
            (3.8, 1.70),   # red finish pad
        ]
        self.odom_origin = None
        self.waypoints = []
        self.goal_index = 0
        self.pose = None
        self.yaw = 0.0
        self.scan = None
        self.scan_time = 0.0
        self.odom_time = 0.0
        self.avoid_until = 0.0
        self.avoid_turn = 0.65
        self.avoid_action = 'turn_left'
        self.completed = False
        self.failed = False
        self.route_started = time.monotonic()
        self.max_route_seconds = 180.0
        self.mode = 'auto'
        self.create_subscription(String, '/campus_navigation/mode', self.mode_cb, 10)
        self.timer = self.create_timer(0.1, self.step)
        self.get_logger().info('Waiting for odometry at the green start pad before navigation')

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
        valid_ranges = [
            value for value in msg.ranges
            if math.isfinite(value)
            and max(msg.range_min, self.self_echo_max_range) < value <= msg.range_max
        ]
        if valid_ranges and min(valid_ranges) < 1.8 and not self.obstacle_seen:
            self.obstacle_seen = True
            self.get_logger().info(f'LiDAR detected a nearby obstacle at {min(valid_ranges):.2f} m')
        self.obstacle_pub.publish(Bool(data=self.obstacle_seen))

    def odom_cb(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        if self.odom_origin is None:
            self.odom_origin = (p.x, p.y)
            self.waypoints = [
                (x - (-3.8), y - 1.70)
                for x, y in self.route_world
            ]
            self.get_logger().info(
                f'Route origin captured at spawn odometry ({p.x:.2f}, {p.y:.2f}); '
                'green start pad is the route origin'
            )
        self.pose = (p.x - self.odom_origin[0], p.y - self.odom_origin[1])
        self.yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self.odom_time = time.monotonic()

    def sector_min_angle(self, low, high):
        if self.scan is None:
            return 0.0
        values = []
        for index, value in enumerate(self.scan.ranges):
            angle = self.scan.angle_min + index * self.scan.angle_increment
            if (
                low <= angle <= high
                and math.isfinite(value)
                and max(self.scan.range_min, self.self_echo_max_range) < value <= self.scan.range_max
            ):
                values.append(value)
        return min(values) if values else self.scan.range_max

    def publish(self, linear=0.0, angular=0.0):
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.cmd_pub.publish(msg)

    def step(self):
        if self.mode == 'manual':
            return
        now = time.monotonic()
        if self.failed:
            self.publish()
            return
        if now - self.route_started > self.max_route_seconds:
            self.failed = True
            self.publish()
            message = f'Route timed out at waypoint {self.goal_index + 1}/{len(self.waypoints)}'
            self.status_pub.publish(String(data=message))
            self.get_logger().error(message)
            return
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
        # Stay close to the painted roadmap at each corner before switching goals.
        if distance < 0.12:
            self.get_logger().info(f'Reached waypoint {self.goal_index + 1}/{len(self.waypoints)}')
            self.goal_index += 1
            self.publish()
            return

        front = self.sector_min_angle(-math.pi / 6.0, math.pi / 6.0)
        left = self.sector_min_angle(math.pi / 6.0, 2.0 * math.pi / 3.0)
        right = self.sector_min_angle(-2.0 * math.pi / 3.0, -math.pi / 6.0)
        target_yaw = math.atan2(dy, dx)
        error = angle_error(target_yaw, self.yaw)

        # First face the waypoint while stationary. This prevents an obstacle
        # beside the robot from sending it into a long series of avoidance turns.
        if abs(error) > 0.65:
            self.avoid_until = 0.0
            self.publish(0.0, clamp(1.5 * error, -0.8, 0.8))
        else:
            if front < 0.65 and now >= self.avoid_until:
                if left >= right and left >= 0.35:
                    action = 'turn_left'
                elif right >= 0.35:
                    action = 'turn_right'
                else:
                    action = 'stop'

                self.avoid_turn = 0.65 if action == 'turn_left' else -0.65
                self.avoid_action = action
                self.avoid_until = now + (0.45 if action == 'stop' else (0.80 if front < 0.5 else 1.0))
                self.get_logger().info(
                    f'LiDAR obstacle at {front:.2f} m; clearance rule: {action}; '
                    f'left={left:.2f} m, right={right:.2f} m'
                )
            if now < self.avoid_until:
                if self.avoid_action == 'stop':
                    self.publish()
                else:
                    # Creep only when front clearance is adequate; turn in place if close.
                    self.publish(0.08 if front >= 0.40 else 0.0, self.avoid_turn)
            elif front < 0.40:
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
