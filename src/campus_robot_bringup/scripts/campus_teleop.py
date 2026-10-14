#!/usr/bin/env python3
"""Keyboard teleoperation; run from a terminal while the simulation is active."""
import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String


class CampusTeleop(Node):
    def __init__(self):
        super().__init__('campus_teleop')
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.mode_pub = self.create_publisher(String, '/campus_navigation/mode', 10)

    def publish(self, key):
        msg = Twist()
        if key in ('w', 'i'):
            msg.linear.x = 0.30
        elif key in ('s', 'k'):
            msg.linear.x = -0.20
        elif key in ('a', 'j'):
            msg.angular.z = 0.70
        elif key in ('d', 'l'):
            msg.angular.z = -0.70
        self.cmd_pub.publish(msg)

    def set_mode(self, value):
        self.mode_pub.publish(String(data=value))


def main(args=None):
    if not sys.stdin.isatty():
        print('Run this node directly in an interactive terminal.')
        return
    rclpy.init(args=args)
    node = CampusTeleop()
    old_settings = termios.tcgetattr(sys.stdin.fileno())
    print('Manual drive: W/I forward, S/K reverse, A/J turn left, D/L turn right.')
    print('Release a key or press SPACE to stop. Press Q to return to autonomous mode.')
    try:
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            ready, _, _ = select.select([sys.stdin], [], [], 0.10)
            key = sys.stdin.read(1).lower() if ready else ''
            if key == 'q':
                node.publish(' ')
                node.set_mode('auto')
                print('Autonomous mode requested.')
                break
            node.set_mode('manual')
            node.publish(key)
            rclpy.spin_once(node, timeout_sec=0.0)
    except KeyboardInterrupt:
        node.publish(' ')
        node.set_mode('auto')
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
