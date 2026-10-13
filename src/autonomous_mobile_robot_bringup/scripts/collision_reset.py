#!/usr/bin/env python3
"""Return the simulated robot to its launch pose after a collision."""

import math
import subprocess
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from ros_gz_interfaces.msg import Contacts


class CollisionReset(Node):
    def __init__(self):
        super().__init__("collision_reset")
        self.declare_parameter("world_name", "empty")
        self.declare_parameter("spawn_x", -3.1)
        self.declare_parameter("spawn_y", -2.5)
        self.declare_parameter("spawn_z", 0.05)
        self.declare_parameter("spawn_yaw", 0.0)
        self.world_name = self.get_parameter("world_name").value
        self.spawn_x = float(self.get_parameter("spawn_x").value)
        self.spawn_y = float(self.get_parameter("spawn_y").value)
        self.spawn_z = float(self.get_parameter("spawn_z").value)
        self.spawn_yaw = float(self.get_parameter("spawn_yaw").value)
        self.reset_pending = False
        self.last_reset = 0.0
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.create_subscription(Contacts, "/robot/contacts", self.on_contacts, 10)
        self.create_timer(0.1, self.process_reset)
        self.get_logger().info(
            f"Reset on contact; home pose x={self.spawn_x:.2f}, y={self.spawn_y:.2f}, "
            f"z={self.spawn_z:.2f}, yaw={self.spawn_yaw:.2f}"
        )

    def on_contacts(self, msg):
        if msg.contacts:
            self.reset_pending = True

    def process_reset(self):
        if not self.reset_pending or time.monotonic() - self.last_reset < 1.5:
            return
        self.reset_pending = False
        self.last_reset = time.monotonic()
        for _ in range(3):
            self.cmd_pub.publish(Twist())

        half_yaw = self.spawn_yaw / 2.0
        request = (
            'name: "autonomous_mobile_robot" '
            f"position {{ x: {self.spawn_x} y: {self.spawn_y} z: {self.spawn_z} }} "
            f"orientation {{ z: {math.sin(half_yaw)} w: {math.cos(half_yaw)} }}"
        )
        try:
            result = subprocess.run(
                [
                    "gz", "service", "-s", f"/world/{self.world_name}/set_pose",
                    "--reqtype", "gz.msgs.Pose", "--reptype", "gz.msgs.Boolean",
                    "--timeout", "1500", "--req", request,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            self.get_logger().warning(
                f"Collision detected; returned robot to launch pose. {result.stdout.strip()}"
            )
        except (OSError, subprocess.SubprocessError) as exc:
            self.get_logger().error(f"Could not reset robot in Gazebo: {exc}")


def main():
    rclpy.init()
    node = CollisionReset()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
