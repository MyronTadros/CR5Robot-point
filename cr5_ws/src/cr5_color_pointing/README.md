# cr5_color_pointing

ROS Melodic package for the Dobot CR5 wrist-camera color-pointing demo.

The robot moves to an observation pose, detects red/yellow/green boxes on the table with HSV color thresholding and an RGB-D depth camera, then moves safely **above** the requested box using MoveIt. It does not grip or touch the boxes.

---

## Package Layout

```text
config/
  demo.yaml               simulation config (Gazebo)
  hardware.yaml           real CR5 config
  color_thresholds.yaml   HSV ranges (shared, tune here first)
launch/
  color_pointing.launch         simulation: MoveIt + pointing node
  spawn_colored_boxes.launch    spawn red/yellow/green SDF boxes in Gazebo
  hardware_color_pointing.launch  real robot: Dobot bringup + MoveIt + node
  hardware_motion_only.launch     real robot: scan/home only, no color commands
  hardware_gazebo_shadow.launch   real robot: Gazebo display mirroring real /joint_states
models/
  colored_box_red/    SDF model with explicit Gazebo material + emissive color
  colored_box_yellow/
  colored_box_green/
scripts/
  color_pointing_node.py        main demo node (interactive + topic command interface)
  detect_color_once.py          standalone one-shot debug detector
  gazebo_joint_state_mirror.py  mirrors real /joint_states into a Gazebo display model
src/cr5_color_pointing/
  perception.py                 HSV + RGB-D detector and PointStamped topic detector
```

---

## Simulation Quickstart

Start the desktop and Gazebo before this package:

```bash
start-cr5-desktop          # Terminal 1 — keep running
run-cr5-gazebo             # Terminal 2 — keep running
```

Spawn boxes:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

If boxes from a previous run appear gray in the camera image, delete and respawn them:

```bash
docker exec -it cr5ros bash -lc '
  source /usr/local/bin/cr5-env
  rosservice call /gazebo/delete_model "model_name: red_box"
  rosservice call /gazebo/delete_model "model_name: yellow_box"
  rosservice call /gazebo/delete_model "model_name: green_box"
  roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

Verify camera topics are up:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
# expected: /wrist_rgbd/rgb/image_raw, /wrist_rgbd/rgb/camera_info,
#           /wrist_rgbd/depth/image_raw, /wrist_rgbd/depth/camera_info, /wrist_rgbd/depth/points
```

Run one-shot debug detection (after moving to scan pose first):

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
```

Launch the demo node:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

---

## Commands

The node accepts commands via:

1. **Interactive prompt** `cr5>` — type directly if stdin is a PTY.
2. **ROS topic** `/cr5_color_pointing/command` — `std_msgs/String`.

| Command | Effect |
|---|---|
| `scan` / `Scan.` | Move to observation pose (joint space) |
| `red` / `Move above red.` | Detect and move above the red box |
| `yellow` / `Move above yellow.` | Detect and move above the yellow box |
| `green` / `Move above green.` | Detect and move above the green box |
| `home` / `Return home.` | Return all joints to `[0,0,0,0,0,0]` |
| `quit` | Shut down the node |

Send a command from another terminal when the prompt is not available:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'scan'"'"'"'

docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'Move above red.'"'"'"'
```

> Do **not** paste the full `rostopic pub` shell command at the `cr5>` prompt. At that prompt, type only the robot command (`red`, `Move above red.`, etc.).

---

## Behavior Notes

- **scan skip**: color commands skip the scan trajectory if the current joints are already within `0.035 rad` of `observation_joints`.
- **camera offset compensation**: the node reads the `Link6 → wrist_rgbd_camera_optical_frame` TF and shifts the Link6 target so the camera optical frame is centered over the detected box.
- **above-box height**: `ground_plane_z + cube_size/2 + safety_height + above_box_extra_clearance` = `0 + 0.025 + 0.25 + 0.25 = 0.525 m` (simulation default).
- **fallbacks disabled**: simulated detection and box-pose fallbacks are off by default; detection failures are reported as real errors.

---

## Real Robot Launch

See [docs/15_REAL_ROBOT_BRINGUP.md](../../docs/15_REAL_ROBOT_BRINGUP.md) for detailed prerequisites.

**Full launch (with camera/detection):**

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   roslaunch cr5_color_pointing hardware_color_pointing.launch robot_ip:=192.168.5.1'
```

**Motion-only (scan/home, no color detection required):**

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   roslaunch cr5_color_pointing hardware_motion_only.launch robot_ip:=192.168.5.1'
```

**Gazebo shadow viewer (mirrors real /joint_states — use instead of `run-cr5-gazebo`):**

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   roslaunch cr5_color_pointing hardware_gazebo_shadow.launch'
```

> Do **not** run `run-cr5-gazebo` alongside hardware control. It starts a conflicting simulated robot, controllers, and MoveIt stack.

### Perception mode for real robot

The default `hardware.yaml` uses `perception/mode: point_topic`, expecting calibrated `geometry_msgs/PointStamped` messages:

```text
/cr5_color_pointing/detections/red
/cr5_color_pointing/detections/yellow
/cr5_color_pointing/detections/green
```

To use a real RGB-D ROS camera instead, set `perception/mode: rgbd` in `hardware.yaml`.

### Hardware preflight

The node checks before any motion:

- `/dobot_bringup/msg/RobotStatus` present
- `is_connected: True`
- `is_enable: True`
- Detection source topic available (color commands only)

Enable the robot:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosservice call /dobot_bringup/srv/EnableRobot'
```

---

## Tuning

HSV detection thresholds → `config/color_thresholds.yaml`

Motion behavior → `config/demo.yaml` (simulation) or `config/hardware.yaml` (real robot):

| Key | What it controls |
|---|---|
| `motion/observation_joints` | Scan/observation pose in joint space |
| `motion/scan_joint_tolerance` | Tolerance (rad) to skip redundant scan |
| `motion/safety_height` | Min height above box (m) |
| `motion/above_box_extra_clearance` | Extra gripper clearance (m) |
| `motion/above_box_orientation_xyzw` | End-effector quaternion above box |
| `motion/center_camera_over_box` | Compensate Link6→camera offset |
| `motion/max_velocity_scaling` | MoveIt velocity scale (0–1) |
| `scene/boxes` | Fallback box positions (used only if fallback is enabled) |
