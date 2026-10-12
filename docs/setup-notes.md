# Setup Notes: Ubuntu 24.04 ARM64 and ROS 2 Jazzy

These notes record one setup on Ubuntu 24.04 ARM64 in a MacBook virtual machine. Other systems may need different graphics or network settings.

## Install and build

Install ROS 2 Jazzy using the [official Ubuntu instructions](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html), then open a terminal:

```bash
source /opt/ros/jazzy/setup.bash
sudo apt install -y python3-rosdep python3-colcon-common-extensions
sudo rosdep init  # Run once per computer; skip if already initialized
rosdep update
git clone https://github.com/Dharun235/Autonomous-Mobile-Robot.git ~/Documents/Autonomous-Mobile-Robot
cd ~/Documents/Autonomous-Mobile-Robot
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Source ROS 2 before building in each new terminal. After a successful build, source `install/setup.bash` before running ROS commands.

## Run simulation

Install the Gazebo and visualization packages if they are missing:

```bash
sudo apt install ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge \
  ros-jazzy-robot-state-publisher ros-jazzy-rviz2
```

Launch the simulation:

```bash
cd ~/Documents/Autonomous-Mobile-Robot
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch autonomous_mobile_robot_bringup sim.launch.py
```

The Gazebo launch file includes `--render-engine ogre` because OGRE2 failed to initialize OpenGL in this ARM64 VM. Standalone Gazebo was verified with OGRE1:

```bash
gz sim -v 3 shapes.sdf --render-engine ogre
```

The workspace build and full Gazebo simulation were verified in this environment. Publishing velocity commands moved the simulated robot and updated wheel states and odometry. Physical ESP32 control was not verified.

## Optional micro-ROS agent

For ESP32 hardware on the same network, run the agent in its own terminal:

```bash
docker run -it --rm --net=host microros/micro-ros-agent:jazzy udp4 --port 8888 -v6
```

The agent started successfully here, but ESP32 connectivity was not verified. Camera hostname discovery (`marpy-cam.local`) also remained unresolved; camera is not needed for simulation.
