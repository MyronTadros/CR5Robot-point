# Next Agent TODO

This handoff reflects the verified state after the 2026-05-11 merge of `main` into `fix/camera-position-fix`.

## Project Goal

Build and maintain a Gazebo + MoveIt demo where the Dobot CR5:

1. starts in Gazebo with gravity ON,
2. holds itself physically using Gazebo ROS control,
3. spawns red/yellow/green cubes on the ground plane,
4. moves the wrist RGB-D camera to `scan`,
5. detects a requested color using HSV + RGB-D,
6. moves safely above the detected box,
7. returns to `scan` or `home`,
8. never grips, touches, or descends onto the boxes.

## Current Accepted State

Confirmed on 2026-05-11:

- `main` was merged into `fix/camera-position-fix`.
- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- `run-cr5-gazebo` launched Gazebo + RViz + MoveIt.
- Gravity stayed ON.
- `joint_state_controller` and `cr5_joint_trajectory_controller` were running.
- `cr5_joint_trajectory_controller` used `effort_controllers/JointTrajectoryController`.
- Wrist RGB-D topics published.
- Colored boxes spawned.
- `scan` moved through the real trajectory controller with action status `3`.
- RGB sampling from scan contained red/yellow/green pixels.
- One-shot detections passed for red, yellow, and green at tabletop height.
- Topic-command sequence `red -> scan -> yellow -> scan -> green -> home` completed through the real trajectory controller.
- Simulated motion/detection fallbacks were disabled and unused.
- `home` returned to near-zero launch/home joints.

## Important Paths

```text
host workspace: /teamspace/studios/this_studio
ROS workspace:  /teamspace/studios/this_studio/cr5_ws
CR5 repo:       /teamspace/studios/this_studio/cr5_ws/src/CR5_ROS
demo package:   /teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing
container:      cr5ros
```

Standard ROS command pattern:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && COMMAND_HERE'
```

## Camera And Scan

Active Gazebo camera mount:

```text
Link6 -> wrist_rgbd_camera_link
xyz="0 -0.055 0"
rpy="1.5708 -1.5708 0"
```

Optical frame:

```text
wrist_rgbd_camera_link -> wrist_rgbd_camera_optical_frame
xyz="0 0 0"
rpy="-1.5708 0 -1.5708"
```

Current scan config in `cr5_ws/src/cr5_color_pointing/config/demo.yaml`:

```yaml
scan_target_link: wrist_rgbd_camera_optical_frame
observation_joints: [0.34378241586489544, -0.207839157537828, -0.5200047031534822, -0.8883737435138563, 1.5699748257363364, 0.3523303922635028]
above_box_orientation_xyzw: [0.0, 0.0, 1.0, 0.0]
```

The command node still supports optional Cartesian scan config if `scan_position` and `scan_orientation_xyzw` are added back, but the accepted default uses `observation_joints`.

Latest scan TF sample:

```text
world -> wrist_rgbd_camera_optical_frame
translation about [0.525, 0.018, 0.704]
RPY about [176 deg, -2 deg, -90 deg]
```

## Latest Detection Results

Standalone detector results after scan:

```text
red:    dummy_link x=0.4544, y=-0.2396, z=0.0501
yellow: dummy_link x=0.5512, y= 0.0018, z=0.0501
green:  dummy_link x=0.4534, y= 0.2446, z=0.0500
```

Command-node results used the configured planning frame and logged:

```text
red:    world x=0.454, y=-0.239, z=0.050
yellow: world x=0.551, y= 0.002, z=0.050
green:  world x=0.453, y= 0.245, z=0.050
```

## Repeat Verification

Use this sequence after future edits:

```bash
source ~/.bashrc
start-cr5-desktop
```

In another terminal:

```bash
source ~/.bashrc
run-cr5-gazebo
```

Then:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

Send commands from another terminal:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py yellow'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py green'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Move above red.'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Move above yellow.'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Move above green.'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Return home.'\''"'
```

## Hard Rules

- Keep gravity ON.
- Do not set the robot static.
- Do not disable physics.
- Do not fake robot motion as the normal solution.
- Do not use Gazebo joint teleporting as the main path.
- Do not add gripper logic.
- Do not make the robot touch boxes.
- Do not work on real robot bringup unless explicitly required.
- Prefer sim-specific files.
- Keep changes small and reversible.
- If perception fails later, diagnose camera image content before changing HSV thresholds.

## Sensible Next Work

- Add a small automated smoke-test script for the scan/detect sequence.
- Publish optional RViz markers for detected points and above-box targets.
- Clean up backup files only if the project owner wants repository history tidied.
- Consider narrowing or documenting the broad Docker port bindings for VNC/noVNC if the Lightning environment exposes host ports beyond SSH forwarding.
