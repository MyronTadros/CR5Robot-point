# Dobot CR5 — Wrist-Camera Color Pointing Demo

> **Branch:** `main` — software stack, Gazebo simulation, fully verified  
> **Hardware branch:** `hardware-demo` — real CR5 hardware stack  
> **Stack:** Ubuntu 18.04 · ROS Melodic · Gazebo Classic 9 · MoveIt 1 · TurboVNC

The robot moves to a joint-space observation pose, detects red/yellow/green boxes on the ground plane using its wrist-mounted RGB-D camera and HSV thresholding, and moves safely **above** the requested box with MoveIt. No gripping.

Run commands from the repository root unless a section says otherwise. On Lightning AI the root is usually `/teamspace/studios/this_studio`; if you cloned the project somewhere else, use that clone path instead.

---

## Quick Start

Use this path after cloning the repository or after Docker state was reset:

```bash
./setup-docker.sh
source ~/.bashrc
start-cr5-desktop
```

Forward port `5901`, connect TurboVNC Viewer to `localhost::5901`, then launch the simulation:

```bash
run-cr5-gazebo
```

In another terminal, spawn the boxes and start the command node:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'

docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

Then send commands at the `cr5>` prompt:

```text
scan
red
yellow
green
home
```

For the full verification flow, use the detailed sequence below.

---

## Branch Overview

| Branch | Purpose |
|---|---|
| `main` | **Software stack** — Docker, Gazebo simulation, wrist RGB-D perception, and MoveIt color-pointing demo |
| `hardware-demo` | **Hardware stack** — real CR5 hardware integration built from the software stack |

The `main` branch contains:

- Repaired Gazebo wrist camera (`wrist_rgbd_camera_link` preserved, not lumped).
- Co-located RGB + depth sensors so HSV detection gets real color while depth is available.
- `gazebo.launch` updated to export Gazebo plugin paths for ROS camera plugins.
- Full simulation sequence (`scan → Move above red. → Move above yellow. → Move above green. → Return home.`) verified through MoveIt/Gazebo trajectory controller.

---

## Environment at a Glance

```text
Repo root       : current clone path (Lightning default: /teamspace/studios/this_studio)
ROS workspace   : ./cr5_ws
CR5 ROS repo    : ./cr5_ws/src/CR5_ROS
Demo package    : ./cr5_ws/src/cr5_color_pointing
Docker image    : cr5-ros-melodic-turbovnc:local
Docker container: cr5ros
Container ws    : /root/cr5_ws
TurboVNC port   : 5901  →  connect with TurboVNC Viewer → localhost::5901
noVNC port      : 6080  →  http://localhost:6080  (browser fallback)
Camera stream   : 8080  →  http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw
```

**Do not** migrate to ROS 2, Noetic, Ubuntu 22.04 native, or Ignition/Gazebo Sim.

---

## First-Time Terminal Setup

```bash
source ~/.bashrc
command -v start-cr5-desktop    # should print the path
command -v run-cr5-gazebo
```

If the commands are missing:

```bash
source ~/.bashrc
# still missing? run Docker recovery:
./setup-docker.sh && source ~/.bashrc
```

---

## Docker Basics

```bash
docker ps                              # list running containers
docker ps -a                           # list all (including stopped)
docker images | grep cr5               # confirm image exists
cr5-ensure-container                   # start/repair the cr5ros container
cr5-shell                              # interactive shell inside cr5ros
```

Run any ROS command inside the container:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && COMMAND_HERE'
```

### Docker-Only Recovery

Use when Docker lost the image/container but workspace files still exist:

```bash
./setup-docker.sh
source ~/.bashrc
```

Rebuilds the image and container from the existing workspace without recloning anything.  
Full setup (only when starting completely from scratch):

```bash
./setup_cr5_lightning.sh
```

---

## Build

After any change to `.py`, `.launch`, `.yaml`, or `.urdf` files:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && cd /root/cr5_ws && catkin_make -DCMAKE_BUILD_TYPE=Release'
```

Documentation-only changes do not need a rebuild.

Quick syntax checks:

```bash
# Gazebo URDF
xmllint --noout \
  cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf

# Demo config
python -c 'import yaml,sys; yaml.safe_load(open(sys.argv[1])); print("ok")' \
  cr5_ws/src/cr5_color_pointing/config/demo.yaml

# Main node
python -m py_compile \
  cr5_ws/src/cr5_color_pointing/scripts/color_pointing_node.py
```

---

## Start the GUI Desktop

> **Required before Gazebo** — camera rendering needs `DISPLAY=:1` (TurboVNC).

**Terminal 1** (keep running):

```bash
source ~/.bashrc
start-cr5-desktop
```

Forward port `5901` in VS Code Remote-SSH, then connect:

```text
TurboVNC Viewer → localhost::5901
```

Browser fallback (forward port `6080` first):

```text
http://localhost:6080/
```

---

## Full Demo Sequence

### Step 1 — Launch Gazebo + MoveIt

**Terminal 2** (keep running):

```bash
source ~/.bashrc
run-cr5-gazebo
```

Expected: Gazebo Classic opens, CR5 spawns upright, gravity stays ON, both controllers start as `RUNNING`.

Verify controllers:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
# joint_state_controller and cr5_joint_trajectory_controller → RUNNING

docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosparam get /cr5_joint_trajectory_controller/type'
# expected: effort_controllers/JointTrajectoryController

docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic echo -n 1 /joint_states'
# expected: finite positions, small velocities after a few seconds
```

Gravity check:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosservice call /gazebo/get_physics_properties | grep -A4 gravity'
```

### Step 2 — Spawn Colored Boxes

**Terminal 3:**

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

Default box positions:

| Color | x | y | z (center) |
|---|---|---|---|
| red | 0.45 | −0.25 | 0.025 |
| yellow | 0.55 | 0.00 | 0.025 |
| green | 0.45 | 0.25 | 0.025 |

If boxes from a previous run appear **gray** in the camera image, delete and respawn them to reload Gazebo materials:

```bash
docker exec -it cr5ros bash -lc '
  source /usr/local/bin/cr5-env
  rosservice call /gazebo/delete_model "model_name: red_box"
  rosservice call /gazebo/delete_model "model_name: yellow_box"
  rosservice call /gazebo/delete_model "model_name: green_box"
  roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

Verify spawned models:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic echo -n 1 /gazebo/model_states'
```

### Step 3 — Check Camera Topics

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

Expected:

```text
/wrist_rgbd/rgb/image_raw
/wrist_rgbd/rgb/camera_info
/wrist_rgbd/depth/image_raw
/wrist_rgbd/depth/camera_info
/wrist_rgbd/depth/points
```

View the camera feed inside the TurboVNC desktop:

```bash
run-cr5-camera-rqt    # opens rqt_image_view in the TurboVNC desktop
```

Or view the camera feed in a local browser:

```bash
run-cr5-camera-web    # keep running; starts web_video_server on port 8080
```

`run-cr5-camera-rqt` does not serve the browser URL; `run-cr5-camera-web` starts `web_video_server`, which does. Then forward port `8080` and open:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw
```

Camera image rate:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic hz /wrist_rgbd/rgb/image_raw'
# expected: ~10–11 Hz
```

### Step 4 — Launch the Color Pointing Node

**Terminal 4** (after boxes are spawned):

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

The node prints a `cr5>` prompt if stdin is a PTY. Type commands directly:

```text
scan
red
scan
yellow
scan
green
home
quit
```

**If no prompt appears** (non-interactive `docker exec`), send commands from another terminal:

```bash
# Move to scan/observation pose
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'scan'"'"'"'

# Move above each color
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'Move above red.'"'"'"'

docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'Move above yellow.'"'"'"'

docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'Move above green.'"'"'"'

# Return home
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'Return home.'"'"'"'
```

> `rostopic pub -1` sends one message to the **already-running** node over `/cr5_color_pointing/command`. It does not start a second node.  
> Do **not** paste the full `rostopic pub` shell command at the `cr5>` prompt — type only the robot command there.

---

## Supported Commands

| Command | Aliases | Effect |
|---|---|---|
| `scan` | `Scan.` | Move to joint-space observation pose |
| `red` | `Move above red.` | Detect red box → move above it |
| `yellow` | `Move above yellow.` | Detect yellow box → move above it |
| `green` | `Move above green.` | Detect green box → move above it |
| `home` | `Return home.` | Return joints to `[0,0,0,0,0,0]` |
| `quit` | — | Shut down the node |

Color commands automatically **skip the scan trajectory** if the current joints are already within `0.035 rad` of `observation_joints`.

---

## Verifying Detection

Run after `scan` has completed (arm must be at the observation pose):

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py yellow'
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py green'
```

Expected: `blob found`, valid depth, `z ≈ 0.0–0.20 m` (tabletop height).

Check pixel-level HSV content of the live image:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && python - <<'"'"'PY'"'"'
import rospy, cv2, numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
rospy.init_node("hsv_check", anonymous=True)
msg = rospy.wait_for_message("/wrist_rgbd/rgb/image_raw", Image, timeout=5)
bgr = CvBridge().imgmsg_to_cv2(msg, desired_encoding="bgr8")
hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
print("shape", bgr.shape)
for name, ranges in {
    "red":    [((0,100,80),(10,255,255)), ((170,100,80),(180,255,255))],
    "yellow": [((20,100,80),(35,255,255))],
    "green":  [((40,80,60),(85,255,255))],
}.items():
    mask = None
    for lo, hi in ranges:
        m = cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
        mask = m if mask is None else cv2.bitwise_or(mask, m)
    print(name, "pixels", int(np.count_nonzero(mask)))
PY'
```

Healthy counts from a verified run: red ≈ 2419, yellow ≈ 1810, green ≈ 2455.  
**If all counts are zero** → do not tune HSV ranges. Fix camera rendering first (see Troubleshooting).

Camera TF at scan pose:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && timeout 5 rosrun tf tf_echo world wrist_rgbd_camera_optical_frame'
# expected: translation ≈ [0.525, 0.018, 0.704], optical +Z pointing down (~RPY 176°, -2°, -90°)
```

---

## Configuration Reference

All simulation behavior is in `cr5_ws/src/cr5_color_pointing/config/demo.yaml`:

| Key | Value | Description |
|---|---|---|
| `motion/observation_joints` | `[0.344, -0.208, -0.520, -0.888, 1.570, 0.352]` | Scan pose (joint space) |
| `motion/safety_height` | `0.25 m` | Min above-box height |
| `motion/above_box_extra_clearance` | `0.25 m` | Extra gripper clearance |
| `motion/scan_joint_tolerance` | `0.035 rad` | Tolerance to skip redundant scan |
| `motion/above_box_orientation_xyzw` | `[0.707, -0.707, 0.0, 0.0]` | Wrist camera pointing down |
| `motion/center_camera_over_box` | `true` | Compensate Link6→camera TF offset |
| `motion/max_velocity_scaling` | `0.2` | MoveIt velocity scale |
| `frames/planning_frame` | `world` | MoveIt planning frame |
| `frames/camera_frame` | `wrist_rgbd_camera_optical_frame` | Camera TF frame |

HSV detection thresholds → `config/color_thresholds.yaml` (tune only after confirming nonzero pixel counts in the image).

---

## Camera Mount Reference

Camera chain in `cr5_robot_gazebo.urdf`:

```text
Link6 → wrist_rgbd_camera_link   xyz="0 -0.055 0"  rpy="1.5708 -1.5708 0"
wrist_rgbd_camera_link → wrist_rgbd_camera_optical_frame
                                  rpy="-1.5708 0 -1.5708"  (standard ROS optical rotation)
```

Topics: `/wrist_rgbd/rgb/…` and `/wrist_rgbd/depth/…`  
Plugin: `libgazebo_ros_openni_kinect.so`  
Resolution: `640×480`, ~10–11 Hz

---

## Troubleshooting

### Helper commands missing

```bash
source ~/.bashrc
# still missing:
./setup-docker.sh && source ~/.bashrc
```

### Docker container missing or image gone

```bash
docker ps -a && docker images | grep cr5
./setup-docker.sh
```

### TurboVNC does not open

```bash
start-cr5-desktop
docker exec -it cr5ros bash -lc 'pgrep -a Xvnc || true'
# then re-forward port 5901 in VS Code and reconnect
```

### Gazebo does not launch / duplicate launch error

Stop stale processes:

```bash
docker exec -it cr5ros bash -lc \
  'pkill -f roslaunch || true; pkill -f rosmaster || true; pkill -f gzserver || true'
```

Then relaunch:

```bash
run-cr5-gazebo
```

### Camera topics missing after Gazebo launch

Gazebo camera rendering **requires** `DISPLAY=:1` (TurboVNC). Always run `start-cr5-desktop` first.

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

If still empty, check `cr5_robot_gazebo.urdf` for `wrist_rgbd_camera_link`, `wrist_rgbd_camera_optical_frame`, and `libgazebo_ros_openni_kinect.so`. Also check that `gazebo.launch` sets the Gazebo plugin path environment variable.

### Robot collapses or moves wildly

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic echo -n 1 /joint_states'
```

Likely causes: controller not running, wrong controller type, PID instability, strict abort tolerance.  
Relevant config files:

```text
cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
cr5_ws/src/CR5_ROS/cr5_moveit/config/gazebo_controllers.yaml
cr5_ws/src/CR5_ROS/cr5_moveit/scripts/unpause_after_controllers.py
```

### HSV detects no colors (all pixel counts zero)

1. Run `run-cr5-camera-rqt` — confirm the image looks like a color scene, not gray.
2. Run the HSV sampling snippet above.
3. If counts are zero → fix camera rendering (mount, scan pose, Gazebo material scripts on box SDF models). Do **not** tune HSV thresholds yet.
4. If counts are nonzero but detection fails → tune `config/color_thresholds.yaml`.

### Scan moves to wrong position

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   timeout 5 rosrun tf tf_echo world wrist_rgbd_camera_optical_frame'
# expected: x≈0.525, y≈0.018, z≈0.704
```

Scan pose is set via `motion/observation_joints` in `config/demo.yaml`.

### Command node shows no prompt

Normal when launched via `docker exec` without a PTY. Use `rostopic pub` from another terminal as shown in the Full Demo Sequence section.

Check subscriber is alive:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic info /cr5_color_pointing/command'
```

---

## Safety Rules

- Keep Gazebo gravity **ON**. Never disable physics globally.
- Do **not** touch, grip, or descend onto boxes.
- Keep all motions at least `0.25 m + 0.25 m clearance` above the boxes.
- Start only one Gazebo launch at a time — duplicate launches cause `SpawnModel: entity already exists` errors.
- Do not use direct Gazebo joint teleporting as the normal execution path.

---

## Key Files

```text
# Setup
setup_cr5_lightning.sh                      full environment setup (run once)
setup-docker.sh                             Docker-only recovery

# Host helper commands (~/.local/bin/)
start-cr5-desktop                           start TurboVNC/noVNC desktop (required first)
run-cr5-gazebo                              Gazebo + RViz + MoveIt
run-cr5-rviz                                RViz only
run-cr5-moveit                              MoveIt only
cr5-shell                                   interactive shell in cr5ros
cr5-ensure-container                        start/repair the container
run-cr5-camera-web                          web_video_server camera stream (port 8080)
run-cr5-camera-rqt                          rqt_image_view in VNC desktop

# Gazebo simulation files
cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
cr5_ws/src/CR5_ROS/cr5_moveit/config/gazebo_controllers.yaml
cr5_ws/src/CR5_ROS/cr5_moveit/launch/gazebo.launch
cr5_ws/src/CR5_ROS/cr5_moveit/scripts/unpause_after_controllers.py

# Color pointing demo package
cr5_ws/src/cr5_color_pointing/config/demo.yaml
cr5_ws/src/cr5_color_pointing/config/color_thresholds.yaml
cr5_ws/src/cr5_color_pointing/launch/color_pointing.launch
cr5_ws/src/cr5_color_pointing/launch/spawn_colored_boxes.launch
cr5_ws/src/cr5_color_pointing/scripts/color_pointing_node.py
cr5_ws/src/cr5_color_pointing/scripts/detect_color_once.py
```

---

## Documentation Index

| Doc | Topic |
|---|---|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/00_PROJECT_OVERVIEW.md](docs/00_PROJECT_OVERVIEW.md) | Project goals |
| [docs/01_LIGHTNING_DOCKER_ENVIRONMENT.md](docs/01_LIGHTNING_DOCKER_ENVIRONMENT.md) | Docker & Lightning setup |
| [docs/04_GAZEBO_CONTROL_FIX.md](docs/04_GAZEBO_CONTROL_FIX.md) | Effort controller fix history |
| [docs/05_WRIST_CAMERA_AND_PERCEPTION.md](docs/05_WRIST_CAMERA_AND_PERCEPTION.md) | Camera URDF, topics, TF |
| [docs/06_COLOR_POINTING_PACKAGE.md](docs/06_COLOR_POINTING_PACKAGE.md) | Package architecture |
| [docs/07_OPERATION_GUIDE.md](docs/07_OPERATION_GUIDE.md) | Step-by-step operation |
| [docs/10_DECISIONS_LOG.md](docs/10_DECISIONS_LOG.md) | Design decisions |
| [docs/11_CHANGELOG.md](docs/11_CHANGELOG.md) | Change history |
| [docs/12_CURRENT_STATUS.md](docs/12_CURRENT_STATUS.md) | Latest verified state |
| [docs/CR5_TROUBLESHOOTING.md](docs/CR5_TROUBLESHOOTING.md) | Extended troubleshooting |
| [docs/CR5_CAMERA.md](docs/CR5_CAMERA.md) | Camera reference |
| [docs/CR5_VERIFICATION_CHECKLIST.md](docs/CR5_VERIFICATION_CHECKLIST.md) | Verification checklist |
