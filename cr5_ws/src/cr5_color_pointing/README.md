# CR5 Color Pointing Demo

This package implements a simple wrist RGB-D camera demo for the Dobot CR5 in ROS Melodic.

The robot moves to an observation pose, detects a red, yellow, or green cube with HSV color thresholding and depth, transforms the detected point into the planning frame, and moves above the requested box. It does not grip, touch, or descend onto the boxes.

## Assumptions

- Gazebo ground plane is the tabletop plane.
- Robot base and boxes sit on `z = 0`.
- Cube size is `0.05 m`.
- Cube center z is `0.025 m`.
- The tool target stays at least `0.25 m` above the box.
- `scan` moves to the configured joint-space observation pose, which places the merged wrist camera above the boxes and points the optical frame down toward the ground.

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
- optional `motion/scan_position` and `motion/scan_orientation_xyzw` if Cartesian scan debugging is reintroduced
- `motion/safety_height`
- `scene/boxes`
- camera topics and frames
