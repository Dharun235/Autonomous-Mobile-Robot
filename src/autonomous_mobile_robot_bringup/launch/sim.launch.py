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
        default_value="empty",
        description="Gazebo world file name (without .sdf extension)",
    )

    # Launch Gazebo with the robot (includes robot_state_publisher + bridge)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(autonomous_mobile_robot_description_dir, "launch", "gazebo.launch.py")
        ),
        launch_arguments={"world_name": LaunchConfiguration("world_name")}.items(),
    )

    # Odometry from joint states (same node as real hardware)
    odometry_node = Node(
        package="autonomous_mobile_robot_localization",
        executable="odometry_node",
        name="odometry_node",
        output="screen",
        parameters=[{"use_sim_time": True}],
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
        gazebo,
        odometry_node,
        rviz,
    ])
