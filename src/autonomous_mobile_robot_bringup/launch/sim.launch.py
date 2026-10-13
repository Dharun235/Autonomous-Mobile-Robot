"""Launch Autonomous Mobile Robot in Gazebo simulation with RViz.

Teleop is launched separately from another terminal:
  ros2 run autonomous_mobile_robot_bringup arrow_teleop.py

Kill leftover processes before relaunching:
  pkill -9 -f "gz sim|rviz2|robot_state_publisher|parameter_bridge"
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    autonomous_mobile_robot_description_dir = get_package_share_directory("autonomous_mobile_robot_description")

    world_name_arg = DeclareLaunchArgument(
        name="world_name",
        default_value="house",
        description="Gazebo world file name (without .sdf extension)",
    )
    spawn_x_arg = DeclareLaunchArgument("spawn_x", default_value="-3.1", description="Robot spawn X position in meters")
    spawn_y_arg = DeclareLaunchArgument("spawn_y", default_value="-2.5", description="Robot spawn Y position in meters")
    spawn_z_arg = DeclareLaunchArgument("spawn_z", default_value="0.05", description="Robot spawn Z position in meters")
    spawn_yaw_arg = DeclareLaunchArgument("spawn_yaw", default_value="0.0", description="Robot spawn yaw in radians")

    # Launch Gazebo with the robot (includes robot_state_publisher + bridge)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(autonomous_mobile_robot_description_dir, "launch", "gazebo.launch.py")
        ),
        launch_arguments={
            "world_name": LaunchConfiguration("world_name"),
            "spawn_x": LaunchConfiguration("spawn_x"),
            "spawn_y": LaunchConfiguration("spawn_y"),
            "spawn_z": LaunchConfiguration("spawn_z"),
            "spawn_yaw": LaunchConfiguration("spawn_yaw"),
        }.items(),
    )

    # Odometry from joint states (same node as real hardware)
    odometry_node = Node(
        package="autonomous_mobile_robot_localization",
        executable="odometry_node",
        name="odometry_node",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    collision_reset_node = Node(
        package="autonomous_mobile_robot_bringup",
        executable="collision_reset.py",
        name="collision_reset",
        output="screen",
        parameters=[{
            "world_name": LaunchConfiguration("world_name"),
            "spawn_x": LaunchConfiguration("spawn_x"),
            "spawn_y": LaunchConfiguration("spawn_y"),
            "spawn_z": LaunchConfiguration("spawn_z"),
            "spawn_yaw": LaunchConfiguration("spawn_yaw"),
        }],
    )

    gazebo_pose_node = Node(
        package="autonomous_mobile_robot_bringup",
        executable="gazebo_pose.py",
        name="gazebo_pose",
        output="screen",
        parameters=[{"use_sim_time": True}],
        remappings=[(
            "/robot/pose_gz",
            ["/world/", LaunchConfiguration("world_name"), "/dynamic_pose/info"],
        )],
    )

    # RViz visualization
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=[
            "-d", os.path.join(autonomous_mobile_robot_description_dir, "rviz", "display.rviz"),
        ],
        parameters=[{"use_sim_time": True}],
    )

    return LaunchDescription([
        world_name_arg,
        spawn_x_arg,
        spawn_y_arg,
        spawn_z_arg,
        spawn_yaw_arg,
        gazebo,
        odometry_node,
        collision_reset_node,
        gazebo_pose_node,
        rviz,
    ])
