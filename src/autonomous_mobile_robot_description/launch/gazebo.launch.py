import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.substitutions import (
    Command,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_dir = get_package_share_directory("autonomous_mobile_robot_description")
    gui_config = os.path.join(pkg_dir, "gui", "camera_view.config")

    model_arg = DeclareLaunchArgument(
        name="model",
        default_value=os.path.join(pkg_dir, "urdf", "autonomous_mobile_robot.xacro"),
        description="Absolute path to robot xacro file",
    )

    world_name_arg = DeclareLaunchArgument(
        name="world_name",
        default_value="empty",
        description="Gazebo world file name (without .sdf extension)",
    )

    spawn_x_arg = DeclareLaunchArgument("spawn_x", default_value="-3.1", description="Robot spawn X position in meters")
    spawn_y_arg = DeclareLaunchArgument("spawn_y", default_value="-2.5", description="Robot spawn Y position in meters")
    spawn_z_arg = DeclareLaunchArgument("spawn_z", default_value="0.05", description="Robot spawn Z position in meters")
    spawn_yaw_arg = DeclareLaunchArgument("spawn_yaw", default_value="0.0", description="Robot spawn yaw in radians")

    world_path = PathJoinSubstitution([
        pkg_dir,
        "worlds",
        PythonExpression(
            ["'", LaunchConfiguration("world_name"), "' + '.sdf'"]
        ),
    ])

    model_path = os.path.dirname(pkg_dir)
    gazebo_resource_path = SetEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        model_path,
    )

    robot_description = ParameterValue(
        Command(["xacro ", LaunchConfiguration("model")]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description, "use_sim_time": True}],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"
            ),
        ]),
        launch_arguments={
            "gz_args": PythonExpression(
                ["'", world_path, " -v 4 -r --render-engine ogre --gui-config ", gui_config, "'"]
            )
        }.items(),
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic", "robot_description",
            "-name", "autonomous_mobile_robot",
            "-x", LaunchConfiguration("spawn_x"),
            "-y", LaunchConfiguration("spawn_y"),
            "-z", LaunchConfiguration("spawn_z"),
            "-Y", LaunchConfiguration("spawn_yaw"),
        ],
    )

    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
            "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist",
            "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            "/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model",
            PythonExpression([
                "'/world/", LaunchConfiguration("world_name"),
                "/dynamic_pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'",
            ]),
            "/imu@sensor_msgs/msg/Imu[gz.msgs.IMU",
            "/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image",
            "/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            "/robot/contacts@ros_gz_interfaces/msg/Contacts[gz.msgs.Contacts",
        ],
        output="screen",
    )

    return LaunchDescription([
        model_arg,
        world_name_arg,
        spawn_x_arg,
        spawn_y_arg,
        spawn_z_arg,
        spawn_yaw_arg,
        gazebo_resource_path,
        robot_state_publisher,
        gazebo,
        spawn_entity,
        gz_bridge,
    ])
