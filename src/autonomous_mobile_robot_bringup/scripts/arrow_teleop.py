#!/usr/bin/env python3
"""Drive robot with terminal arrow keys; space stops and q exits."""

import os
import select
import sys
import termios
import time
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class ArrowTeleop(Node):
    def __init__(self):
        super().__init__("arrow_teleop")
        self.publisher = self.create_publisher(Twist, "/cmd_vel", 10)
        self.linear_speed = 0.2
        self.angular_speed = 0.8
        self.command = Twist()
        self.last_key_time = 0.0
        self.timer = self.create_timer(0.05, self.publish_command)

    def set_key(self, key):
        self.last_key_time = time.monotonic()
        self.command = Twist()
        if key == "\x1b[A":
            self.command.linear.x = -self.linear_speed
        elif key == "\x1b[B":
            self.command.linear.x = self.linear_speed
        elif key == "\x1b[D":
            self.command.angular.z = self.angular_speed
        elif key == "\x1b[C":
            self.command.angular.z = -self.angular_speed

    def publish_command(self):
        # Terminal key repeat sustains motion. Stop if repeats cease for 0.5 s.
        command = self.command
        if time.monotonic() - self.last_key_time > 0.5:
            command = Twist()
        self.publisher.publish(command)


def read_key():
    first = os.read(sys.stdin.fileno(), 1).decode(errors="ignore")
    if first != "\x1b":
        return first
    sequence = first
    for _ in range(2):
        ready, _, _ = select.select([sys.stdin], [], [], 0.03)
        if not ready:
            break
        sequence += os.read(sys.stdin.fileno(), 1).decode(errors="ignore")
    return sequence


def main():
    if not sys.stdin.isatty():
        raise SystemExit("Run arrow teleop in an interactive terminal.")

    original_settings = termios.tcgetattr(sys.stdin.fileno())
    node = None
    try:
        tty.setraw(sys.stdin.fileno())
        rclpy.init()
        node = ArrowTeleop()
        print("Arrow keys drive; space stops; q exits.", file=sys.stderr, flush=True)
        while rclpy.ok():
            ready, _, _ = select.select([sys.stdin], [], [], 0.02)
            if ready:
                key = read_key()
                if key == "q":
                    break
                node.set_key(key)
            rclpy.spin_once(node, timeout_sec=0.0)
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, original_settings)
        if node is not None:
            node.command = Twist()
            for _ in range(3):
                rclpy.spin_once(node, timeout_sec=0.06)
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
