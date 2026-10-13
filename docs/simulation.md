# Simulation

Run Autonomous Mobile Robot in Gazebo without hardware. The simulation uses the same `/cmd_vel` and `/joint_states` topics as the real robot, so teleop and odometry work identically.

## Prerequisites

Install the following ROS2 Jazzy packages (Ubuntu 24.04):

```bash
sudo apt update
sudo apt install -y \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-xacro \
  ros-jazzy-rviz2
```

Build the workspace:

```bash
cd ~/Autonomous-Mobile-Robot
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Launch the Simulation

The `sim.launch.py` file starts Gazebo, RViz, and the odometry node in one command:

```bash
ros2 launch autonomous_mobile_robot_bringup sim.launch.py
```

This launches:
- **Gazebo** with the robot spawned in the included house world
- **RViz** for visualization (TF, robot model, odometry path)
- **Odometry node** computing wheel odometry from `/joint_states`
- **Collision reset node** returning the robot to its launch pose when its chassis collision box contacts a wall or obstacle

## Drive the Robot

In a separate terminal:

```bash
source ~/Autonomous-Mobile-Robot/install/setup.bash
ros2 run autonomous_mobile_robot_bringup arrow_teleop.py
```

Use arrow keys to drive. Press Space to stop and `q` to quit. You should see:
- The robot moving in Gazebo
- The odometry path (`/odom_path`) drawing in RViz
- The TF tree updating in real time

Use one teleop process at a time. Multiple teleop processes publish to `/cmd_vel` and can cancel each other's commands.

## Visualize the Odometry Path in RViz

If the path is not already visible in RViz:

1. Click **Add** in the Displays panel
2. Select **By topic** → `/odom_path` → **Path**
3. Click **OK**

The path will draw the route the robot has traveled in the odom frame.

## View the URDF Model Only

To inspect the robot model in RViz without Gazebo:

```bash
ros2 launch autonomous_mobile_robot_description display.launch.py
```

## Custom Worlds

Run the included house-like indoor world:

```bash
ros2 launch autonomous_mobile_robot_bringup sim.launch.py world_name:=house
```

It has several rooms, doorways, walls, and simple furniture obstacles. The world is self-contained, so it works offline and does not need Gazebo Fuel downloads. The open top makes it easier to inspect the layout in Gazebo. It is a simple navigation test map, not a photorealistic home.

The robot has a forward-facing 640×480 RGB camera at 15 Hz. Gazebo shows live feed in right-side **Robot RGB Camera** panel. ROS 2 publishes:

- `/camera/image_raw` (`sensor_msgs/Image`)
- `/camera/camera_info` (`sensor_msgs/CameraInfo`)
- `camera_link` and `camera_optical_frame` in TF

Gazebo's true model position is published to **`/robot/pose`** as `geometry_msgs/PoseStamped` in the `world` frame. It represents the robot model's ground-level `base_footprint` origin, not the camera location. Read it with `ros2 topic echo /robot/pose --once`. `/odom` remains wheel odometry relative to where the robot started.

Camera component lives in `urdf/camera.xacro`; `gui/camera_view.config` sets Gazebo camera panel. RViz also shows camera frames and image topic. This is RGB only; it does not publish depth.

### Physical camera mounting reference

The simulated camera is a front-center mount with a visible support shelf. Measurements use the robot's `base_link` frame, with +X forward, +Y left, and +Z up:

- Camera housing center: **105 mm forward**, **0 mm lateral**, **85 mm above** the `base_link` origin.
- Camera pitch: **6.9° downward**.
- Lens center: about **121 mm forward** and **83 mm above** the `base_link` origin. This is about **131 mm above the floor** when the robot rests on its wheels.
- Housing size in the model: **45 × 52 × 26 mm**.

I measured the base mesh extents as X = **−120.6 to +80.3 mm**, Y = **±71.2 mm**, and Z = **−27.8 to +82.2 mm**, relative to `base_link`. At the front centerline, the chassis top is about **64 mm above** the `base_link` origin. The modeled **8 mm** shelf spans the chassis front edge and the camera housing. For the physical robot, use a similar small shelf/bracket and place the lens on the centerline at the measurements above. Check the real chassis top and camera dimensions before fastening; the repository has no hardware bracket CAD.

Walls and furniture have collision geometry, so they block the robot in physics. The robot chassis collision is a **0.22 × 0.16 × 0.11 m box** centered at `(-0.02015, 0, 0.02723)` in `base_link`; the contact sensor watches this box and resets the robot after a collision. The house's perimeter walls keep it inside the map. The robot starts in southwest corner at `(x=-3.1, y=-2.5, z=0.05 m)`, facing east (`+X`). Gravity settles it onto the floor.

To verify contact reset in a running `house` world, place the robot in the sofa collision volume. Gazebo reports the resulting physics contact and the reset node returns it to the launch pose:

```bash
gz service -s /world/house/set_pose \
  --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 3000 \
  --req 'name: "autonomous_mobile_robot" position { x: -2.8 y: -1.7 z: 0.05 } orientation { w: 1 }'
ros2 topic echo /robot/pose --once
```

The pose should return to approximately `x=-3.1, y=-2.5`.

Set another starting pose with `spawn_x`, `spawn_y`, `spawn_z`, and `spawn_yaw` (yaw is radians):

```bash
ros2 launch autonomous_mobile_robot_bringup sim.launch.py \
  world_name:=house spawn_x:=-3.1 spawn_y:=-2.5 spawn_yaw:=0.0
```

Choose a clear spot inside house walls and away from furniture.

Pass another world file by name:

```bash
ros2 launch autonomous_mobile_robot_bringup sim.launch.py world_name:=my_world
```

World files are located in `src/autonomous_mobile_robot_description/worlds/` (SDF format). For example, use `world_name:=empty` to return to the empty world.

## Troubleshooting

**Gazebo doesn't start or hangs:**
Stop an existing simulation with `Ctrl+C` in its launch terminal before starting another. Running multiple Gazebo launches in the same ROS domain can cause conflicting simulation clocks.

**Robot doesn't move with teleop:**
- Make sure the teleop terminal is focused (it reads keypresses)
- Run teleop in an interactive terminal; arrow keys use terminal escape sequences
- Make sure only one `arrow_teleop.py` process is running (`ros2 node list` should show one `/arrow_teleop`)
- Check that the Gazebo bridge is running: `ros2 topic list` should show `/cmd_vel`

**No odometry path in RViz:**
- Verify the odometry node is running: `ros2 node list` should show `/odometry_node`
- Check the topic: `ros2 topic echo /odom_path --once`
