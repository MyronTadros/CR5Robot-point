# CR5 Lightning Workflow

This document is the day-to-day runbook for the Dobot CR5 ROS Melodic environment on Lightning AI.

## One-Time Setup

The setup script is:

```text
/teamspace/studios/this_studio/setup_cr5_lightning.sh
```

It creates:

- the persistent workspace at `/teamspace/studios/this_studio/cr5_ws`
- the CR5 repository at `/teamspace/studios/this_studio/cr5_ws/src/CR5_ROS`
- the Docker image `cr5-ros-melodic-turbovnc:local`
- helper commands in `~/.local/bin`
- a catkin build inside the Docker image/container environment

The setup has already completed successfully when the output ends with:

```text
[CR5 setup] Setup complete.
```

## Start The Desktop

From a Lightning host terminal:

```bash
source ~/.bashrc
start-cr5-desktop
```

Expected successful signs:

- TurboVNC listens on TCP port `5901`
- noVNC/websockify listens on port `6080`
- the terminal stays running and tails VNC/noVNC logs
- TurboVNC Viewer can connect from Windows to `localhost::5901`
- the desktop appears as a minimal black Fluxbox session with an `xterm`

Common Fluxbox and xterm warnings are harmless if the desktop appears and port `5901` is listening.

## Launch RViz Robot Display

Start the desktop first, then in another Lightning terminal:

```bash
run-cr5-rviz
```

This runs inside the container:

```bash
source /usr/local/bin/cr5-env && roslaunch dobot_description display.launch
```

Expected result:

- RViz opens in the TurboVNC desktop
- the CR5 model appears
- the joint state publisher GUI may also appear, depending on the launch file

## Launch MoveIt Planning Demo

Start the desktop first, then:

```bash
run-cr5-moveit
```

This runs inside the container:

```bash
source /usr/local/bin/cr5-env && roslaunch dobot_moveit demo.launch
```

Expected result:

- RViz opens in the TurboVNC desktop
- the MoveIt MotionPlanning panel is available
- planning groups and interactive markers load for the CR5

## Launch Gazebo Simulation

Start the desktop first, then:

```bash
run-cr5-gazebo
```

This runs inside the container:

```bash
source /usr/local/bin/cr5-env && roslaunch cr5_moveit demo_gazebo.launch
```

Expected result:

- Gazebo Classic opens in the TurboVNC desktop
- RViz may also open, depending on the launch file
- ROS topics for the robot and camera become available after Gazebo finishes loading

Gazebo can take longer than RViz to start on a 4x CPU cloud machine. Give it time before assuming it failed.

## Use A Shell Inside The Container

For direct ROS commands:

```bash
cr5-shell
```

The shell starts with the CR5 ROS environment loaded. If using an xterm inside the VNC desktop, source the environment manually:

```bash
source /usr/local/bin/cr5-env
```

Useful direct commands:

```bash
roslaunch dobot_description display.launch
roslaunch dobot_moveit demo.launch
roslaunch cr5_moveit demo_gazebo.launch
```

## Environment Variables

The environment depends on:

```bash
DOBOT_TYPE=cr5
DISPLAY=:1
LIBGL_ALWAYS_SOFTWARE=1
QT_X11_NO_MITSHM=1
```

Meanings:

- `DOBOT_TYPE=cr5` selects the CR5 robot in the repository's generic launch/config wrappers.
- `DISPLAY=:1` sends GUI windows to the TurboVNC X display.
- `LIBGL_ALWAYS_SOFTWARE=1` makes OpenGL use software rendering for cloud/container stability.
- `QT_X11_NO_MITSHM=1` avoids Qt shared-memory problems in remote/container X sessions.

## Port Forwarding From Windows

Forward these ports through VS Code Remote-SSH as needed:

```text
5901  TurboVNC
6080  noVNC browser fallback
8080  camera web stream
```

Preferred viewer:

```text
TurboVNC Viewer -> localhost::5901
```

Fallback browser viewer:

```text
http://localhost:6080/vnc.html
```

Camera stream path after forwarding port `8080`:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw
```
