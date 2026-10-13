#!/usr/bin/env python3
"""Publish the robot's live Gazebo world pose as geometry_msgs/PoseStamped."""

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from tf2_msgs.msg import TFMessage


class GazeboPose(Node):
    def __init__(self):
        super().__init__("gazebo_pose")
        self.entity_name = "autonomous_mobile_robot"
        self.pose_pub = self.create_publisher(PoseStamped, "/robot/pose", 10)
        self.create_subscription(TFMessage, "/robot/pose_gz", self.on_pose, 10)
        self.first_pose = True

    def on_pose(self, msg):
        selected = None
        for transform in msg.transforms:
            child = transform.child_frame_id.strip("/")
            if not (
                child == self.entity_name
                or child.endswith("/" + self.entity_name)
                or child.endswith("::" + self.entity_name)
            ):
                continue
            selected = transform
            break

        # Gazebo's world dynamic_pose/info stream currently converts to TFMessage
        # without frame names. In this one-robot world its first entry is the
        # robot model pose; use it when the bridge omitted child_frame_id.
        if selected is None and msg.transforms and not any(
            transform.child_frame_id for transform in msg.transforms
        ):
            selected = msg.transforms[0]
        if selected is None:
            return

        pose = PoseStamped()
        pose.header = selected.header
        pose.header.stamp = self.get_clock().now().to_msg()
        if not pose.header.frame_id:
            pose.header.frame_id = "world"
        pose.pose.position.x = selected.transform.translation.x
        pose.pose.position.y = selected.transform.translation.y
        pose.pose.position.z = selected.transform.translation.z
        pose.pose.orientation = selected.transform.rotation
        self.pose_pub.publish(pose)
        if self.first_pose:
            self.get_logger().info(
                f"Publishing Gazebo world pose on /robot/pose in {pose.header.frame_id} frame"
            )
            self.first_pose = False


def main():
    rclpy.init()
    node = GazeboPose()
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
