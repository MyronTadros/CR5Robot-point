# Real Robot Bringup

This page records the real CR5 path added on 2026-05-13.

## Manual Facts Used

From the Dobot CR Series guide:

- The controller LAN default address is `192.168.5.1`.
- The controller LAN port is intended for PC debugging and TCP/IP or Modbus TCP use.
- The emergency stop switch must be connected before operation.
- Emergency stop is a complementary protective measure, not a replacement for workspace safeguarding and operator supervision.

From the Dobot VX500 smart camera guide:

- The VX500 camera is a mono smart camera. The listed pixel format is `Mono 8`, and the camera color is `Mono`.
- The camera uses Ethernet for camera debugging/configuration.
- VX500 tools can output calibrated coordinates, including `coord` results in `{X, Y, Z, RX, RY, RZ}` format for positioning tools.

Confirmed implication:

- The existing HSV + RGB-D detector can work with a real ROS RGB-D camera, but it cannot color-threshold red/yellow/green directly from a VX500 mono image.
- For a VX500-only setup, publish calibrated target points to ROS as `geometry_msgs/PointStamped` messages, one topic per requested color.

## Launch Path

Real-hardware launch:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing hardware_color_pointing.launch robot_ip:=192.168.5.1'
```

Motion-only launch while the camera is not ready:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing hardware_motion_only.launch robot_ip:=192.168.5.1'
```

Gazebo hardware shadow viewer:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing hardware_gazebo_shadow.launch'
```

Use this shadow viewer during a physical demo instead of `run-cr5-gazebo`. The normal Gazebo demo launch starts a separate simulated robot, simulated controllers, `/move_group`, `/robot_state_publisher`, and simulated `/joint_states`; those collide with the hardware bringup stack. The shadow launch starts a paused Gazebo world and mirrors the real robot's `/joint_states` into a display-only model named `hardware_robot`.

This starts the same Dobot driver and MoveIt path, but the command node rejects red/yellow/green commands immediately. Use only:

```text
scan
home
Return home.
```

The launch file starts:

- `dobot_bringup bringup.launch`, connected to `robot_ip`;
- `cr5_moveit cr5_moveit.launch`, using the real `follow_joint_trajectory` controller manager;
- `cr5_color_pointing color_pointing_node.py`, loaded from `config/hardware.yaml`.

The Gazebo shadow launch starts:

- Gazebo paused, without Gazebo ROS control;
- a `hardware_robot` visual model from the real CR5 URDF;
- `gazebo_joint_state_mirror.py`, which copies live `/joint_states` from the Dobot driver into the Gazebo model.

The hardware config uses:

- controller action: `/follow_joint_trajectory/follow_joint_trajectory`;
- execution mode: `moveit`;
- dashboard port: `29999`;
- realtime feedback port: `30004`;
- motion-command port: `29999` for this tested CR5A controller;
- low MoveIt scaling: `0.05` velocity and `0.05` acceleration;
- Dobot speed factor: `10`;
- ServoJ trajectory streaming period: `0.05 s`;
- simulated motion and detection fallbacks disabled;
- above-box extra clearance: `0.25 m`;
- full MoveIt trajectories, not the Gazebo single-point trajectory shortcut.

## Required Preflight

On the tested Linux host, the robot was connected through wired interface `enp4s0`. DHCP did not provide an address, so the interface needed a static no-default-route profile:

```bash
nmcli connection add type ethernet ifname enp4s0 con-name cr5-direct ipv4.method manual ipv4.addresses 192.168.5.10/24 ipv4.never-default yes ipv6.method ignore autoconnect yes
nmcli connection up cr5-direct
```

Confirmed TCP ports:

```text
192.168.5.1:29999 open
192.168.5.1:30004 open and streaming the expected 1440-byte realtime packet
192.168.5.1:30005 open and streaming realtime feedback
192.168.5.1:30003 refused on this controller
```

Confirmed controller mode and command behavior:

- If raw dashboard commands return `Control Mode Is Not Tcp`, ROS cannot enable or move the robot yet.
- In DobotStudio Pro 4.x, this is normally switched from the main interface, not from `Settings` -> `Communication`.
- Go back to the main CR robot page, find `Device mode` in the device information panel, click the current value such as `Online`, select `TCP` or `TCP/IP Secondary Development`, and confirm.
- The `Settings` -> `Communication` page only configures IP/WiFi/fieldbus settings. `EtherNet/IP` under bus communication is not the TCP/IP secondary-development mode used by ROS.
- On this CR5A controller, TCP mode made dashboard commands return success on `29999`, but did not open `30003`.
- A no-op `ServoJ` command on `29999` returned success, so the hardware launch defaults `motion_port` to `29999`.
- Dashboard-backed services such as `ClearError` and `EnableRobot` return `res: -1` while the controller rejects commands.
- Do this before launching the ROS hardware stack. The controller does not accept dashboard control commands while it remains in Online/default mode.

Before sending `scan`, `red`, `yellow`, `green`, or `home`, the node checks:

- `/dobot_bringup/msg/RobotStatus` is present;
- the driver reports `is_connected`;
- the driver reports `is_enable`;
- the configured detection source topic exists for color commands.

By default, `hardware/auto_enable_robot` is `false`. Enable the robot deliberately from the Dobot RViz plugin or by calling the Dobot bringup service after the physical area is safe.

## Perception Modes

`config/hardware.yaml` defaults to:

```yaml
perception:
  mode: point_topic
topics:
  detected_point_template: /cr5_color_pointing/detections/{color}
```

For this mode, publish:

```text
/cr5_color_pointing/detections/red
/cr5_color_pointing/detections/yellow
/cr5_color_pointing/detections/green
```

Message type:

```text
geometry_msgs/PointStamped
```

The point should represent the box/tabletop target in `dummy_link`, `world`, or another TF-connected frame. The command node transforms it into the MoveIt planning frame before planning.

If using a real RGB-D ROS camera instead, set:

```yaml
perception:
  mode: rgbd
```

and provide the configured image/depth/camera-info topics.

## Real MoveIt URDF

The real MoveIt launch expects:

```text
cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot.urdf
```

This file now exists and keeps the verified CR5 chain plus the current wrist camera TF:

```text
Link6 -> wrist_rgbd_camera_link
xyz="0 -0.055 0"
rpy="1.5708 -1.5708 0"
```

It omits Gazebo transmissions, Gazebo plugins, and the Gazebo-only `world` anchor.

## Not Yet Runtime Verified

No physical robot or VX500 bridge was connected during this code pass.

Validated so far:

- Python syntax checks passed.
- YAML parsing passed.
- XML parsing passed.
- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed inside `cr5ros`.
- `check_urdf` passed for `dobot_description/urdf/cr5_robot.urdf`.
- `roslaunch --nodes` resolved `hardware_color_pointing.launch`.
- `roslaunch --nodes` resolved `hardware_motion_only.launch`.
- `roslaunch --nodes` resolved `hardware_gazebo_shadow.launch`.
- Driver-only hardware bringup connected to the physical robot's dashboard and realtime feedback sockets.
- `/dobot_bringup/msg/RobotStatus` reported `is_enable: True` and `is_connected: True` with `motion_port:=29999`.
- `/dobot_bringup/srv/ClearError` and `/dobot_bringup/srv/EnableRobot` returned `res: 0`.
- A no-op `/dobot_bringup/srv/ServoJ` call at the current joint angles returned `res: 0`.
- A no-op `FollowJointTrajectory` action completed with state `3`.
- `/joint_states` published live physical robot joint angles.
- `hardware_gazebo_shadow.launch gazebo_gui:=false` spawned `hardware_robot` into Gazebo while the Dobot driver published real joint states.
- Full `hardware_motion_only.launch` started `cr5_robot`, `move_group`, `robot_state_publisher`, RViz, and `cr5_color_pointing`.
- Motion-only mode rejected a `red` command before any camera wait.
- `scan` command preflight refused motion while the robot was connected but not enabled.

Still required before a live demo:

- keep DobotStudio Pro `Device mode` in `TCP` / `TCP/IP Secondary Development`;
- verify the robot can be enabled and disabled safely;
- publish or bridge real camera detections;
- test `scan` at low speed over empty space first;
- test color moves only after the point topics and TF frame are confirmed.
