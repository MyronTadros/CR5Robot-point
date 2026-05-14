# CR5 Color Pointing Demo

This package implements a simple wrist camera pointing demo for the Dobot CR5 in ROS Melodic.

The robot moves to an observation pose, detects a red, yellow, or green cube with HSV color thresholding and depth, transforms the detected point into the planning frame, and moves above the requested box. It does not grip, touch, or descend onto the boxes.

In simulation and with a real RGB-D camera, perception uses HSV + depth. With the real VX500 mono smart camera, use `perception/mode: point_topic` and publish calibrated `geometry_msgs/PointStamped` detections from the VX500 workflow.

## Assumptions

- Gazebo ground plane is the tabletop plane.
- Robot base and boxes sit on `z = 0`.
- Cube size is `0.05 m`.
- Cube center z is `0.025 m`.
- Above-box camera targets use the original `0.25 m` safety height plus an extra `0.25 m` gripper-clearance margin.
- `scan` moves to the configured joint-space observation pose, which places the merged wrist camera above the boxes and points the optical frame down toward the ground.
- Color commands skip the scan move when the current joints are already within `0.035 rad` of the configured observation pose.

## Launch

Start the desktop and Gazebo first:

```bash
start-cr5-desktop
run-cr5-gazebo
```

Spawn the boxes:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

If the boxes already exist from an older run but the camera image is gray at the box locations, delete and respawn them so Gazebo reloads the current color materials:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /gazebo/delete_model "model_name: red_box"; rosservice call /gazebo/delete_model "model_name: yellow_box"; rosservice call /gazebo/delete_model "model_name: green_box"; roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

Check camera topics:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

Run the debug detector:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
```

Run the pointing node:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

This starts the CR5 color pointing program inside the Docker container. Leave this terminal running. If interactive input is attached, it shows a `cr5>` prompt where you can type commands such as:

```text
red
scan
Move above yellow.
Return home.
quit
```

If the node is launched without interactive stdin, send commands with:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Move above red.'\''"'
```

This does not start a second pointing program. It sends one text command to the already-running pointing node over the ROS topic `/cr5_color_pointing/command`. Use this from another terminal if the `cr5>` prompt is not accepting typed input cleanly.

Do not paste the full `docker exec ... rostopic pub ...` command at the `cr5>` prompt. At `cr5>`, type only the robot command:

```text
red
```

or:

```text
Move above red.
```

The normal Gazebo demo path now uses the real MoveIt/Gazebo trajectory controller only. `motion/execution_mode` defaults to `moveit`, so the node does not move Gazebo joints directly and does not publish fake `/joint_states`.

The wrist camera must detect the requested color. Simulated detection and box-pose fallbacks are disabled by default, so failed camera detection or implausible tabletop geometry is reported as a real failure instead of being hidden by configured box positions.

## Real Robot Launch

After the CR5 controller, emergency stop, and network are set up, make sure the Linux Ethernet interface is on the CR5 subnet. On the tested host this was:

```bash
nmcli connection add type ethernet ifname enp4s0 con-name cr5-direct ipv4.method manual ipv4.addresses 192.168.5.10/24 ipv4.never-default yes ipv6.method ignore autoconnect yes
nmcli connection up cr5-direct
```

The tested physical controller used dashboard port `29999`, realtime feedback port `30004`, and accepted streamed `ServoJ` motion commands on dashboard port `29999`. Port `30003` was refused on this controller even after TCP mode was active.

Start the real hardware path:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing hardware_color_pointing.launch robot_ip:=192.168.5.1'
```

The hardware config uses the Dobot driver action `/follow_joint_trajectory/follow_joint_trajectory`, low velocity/acceleration scaling, Dobot speed factor `10`, robot-status preflight checks, and no simulation fallbacks.

If the camera is not ready yet, use the motion-only real robot launch:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing hardware_motion_only.launch robot_ip:=192.168.5.1'
```

This launch still starts Dobot bringup and MoveIt, but accepts only `scan` and `home` style commands. Red/yellow/green commands are rejected before any camera wait.

For a Gazebo view during hardware demos, use the hardware shadow launch instead of the normal simulation launch:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing hardware_gazebo_shadow.launch'
```

Do not run `run-cr5-gazebo` at the same time as hardware control. That command starts a separate simulated robot and its own controllers/MoveIt stack. The shadow launch keeps Gazebo paused and mirrors the physical robot's `/joint_states` into a display-only model.

For the default VX500-compatible path, publish calibrated box points as:

```text
/cr5_color_pointing/detections/red
/cr5_color_pointing/detections/yellow
/cr5_color_pointing/detections/green
```

Each topic must publish `geometry_msgs/PointStamped` in `dummy_link` or another TF-connected frame.

Supported commands:

```text
Scan.
Move above red.
Move above yellow.
Move above green.
Return home.
scan
red
yellow
green
home
quit
```

## Tuning

Tune HSV thresholds in `config/color_thresholds.yaml`.

Tune robot behavior in `config/demo.yaml`, especially:

- `motion/observation_joints`
- `motion/scan_joint_tolerance`
- optional `motion/scan_position` and `motion/scan_orientation_xyzw` if Cartesian scan debugging is reintroduced
- `motion/safety_height`
- `motion/above_box_extra_clearance`
- `motion/above_box_orientation_xyzw`
- `motion/center_camera_over_box`
- `scene/boxes`
- camera topics and frames
