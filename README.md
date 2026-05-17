# Dobot CR5 — Wrist-Camera Color Pointing Demo

> **Branch:** `feat/hardware-demo` — real robot bringup + simulation  
> **Simulation-only branch:** `fix/camera-position-fix`  
> **Stack:** Ubuntu 18.04 · ROS Melodic · Gazebo Classic 9 · MoveIt 1 · TurboVNC

The robot moves to an observation pose, detects red/yellow/green boxes on the table with a wrist-mounted RGB-D camera and HSV thresholding, then moves safely **above** the requested box. No gripping.

---

## Quick-start: which branch do I want?

| Branch | Purpose |
|---|---|
| `fix/camera-position-fix` | Simulation only — Gazebo + MoveIt + wrist camera fully verified |
| `feat/hardware-demo` | Real CR5 hardware + simulation shadow; builds on the above |
| `main` | Baseline camera-added commit; use one of the branches above |

---

## Environment at a Glance

```text
Host workspace : /teamspace/studios/this_studio
ROS workspace  : /teamspace/studios/this_studio/cr5_ws
CR5 ROS repo   : /teamspace/studios/this_studio/cr5_ws/src/CR5_ROS
Demo package   : /teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing
Docker image   : cr5-ros-melodic-turbovnc:local
Docker container: cr5ros
Container ws   : /root/cr5_ws
TurboVNC port  : 5901  (connect with TurboVNC Viewer → localhost::5901)
noVNC port     : 6080  (browser fallback → http://localhost:6080)
Camera stream  : 8080  (→ http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw)
```

**Do not** migrate to ROS 2, Noetic, Ubuntu 22.04 native, or Ignition/Gazebo Sim.

---

## First-Time Terminal Setup

```bash
source ~/.bashrc
command -v start-cr5-desktop   # should print the path
command -v run-cr5-gazebo
```

If the commands are missing:

```bash
source ~/.bashrc
# still missing? run Docker recovery:
cd /teamspace/studios/this_studio && ./setup-docker.sh && source ~/.bashrc
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
cd /teamspace/studios/this_studio
./setup-docker.sh
source ~/.bashrc
```

This rebuilds the image and container from the existing workspace without recloning anything.  
Full setup (only when starting from scratch):

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
# URDF
xmllint --noout /teamspace/studios/this_studio/cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
# YAML
python -c 'import yaml,sys; yaml.safe_load(open(sys.argv[1])); print("ok")' \
  /teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing/config/demo.yaml
# Python node
python -m py_compile \
  /teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing/scripts/color_pointing_node.py
```

---

## Start the GUI Desktop

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

## Simulation Demo (Gazebo + MoveIt)

### 1. Launch Gazebo

**Terminal 2:**

```bash
source ~/.bashrc
run-cr5-gazebo
```

Expected: Gazebo Classic opens, CR5 spawns upright, gravity stays ON, controllers start.

Verify controllers:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
# should show joint_state_controller and cr5_joint_trajectory_controller as RUNNING

docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosparam get /cr5_joint_trajectory_controller/type'
# expected: effort_controllers/JointTrajectoryController
```

### 2. Spawn Colored Boxes

**Terminal 3:**

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

Default box positions:

| Color | x | y | z |
|---|---|---|---|
| red | 0.45 | −0.25 | 0.025 |
| yellow | 0.55 | 0.00 | 0.025 |
| green | 0.45 | 0.25 | 0.025 |

If boxes were spawned in a previous run and the camera sees them as gray, delete and respawn:

```bash
docker exec -it cr5ros bash -lc '
  source /usr/local/bin/cr5-env
  rosservice call /gazebo/delete_model "model_name: red_box"
  rosservice call /gazebo/delete_model "model_name: yellow_box"
  rosservice call /gazebo/delete_model "model_name: green_box"
  roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

### 3. Check Camera Topics

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

Expected topics:

```text
/wrist_rgbd/rgb/image_raw
/wrist_rgbd/rgb/camera_info
/wrist_rgbd/depth/image_raw
/wrist_rgbd/depth/camera_info
/wrist_rgbd/depth/points
```

View the camera feed:

```bash
run-cr5-camera-rqt          # opens rqt_image_view in the TurboVNC desktop
# or browser stream (forward port 8080 first):
# http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw
```

Camera TF at the scan pose:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && timeout 5 rosrun tf tf_echo world wrist_rgbd_camera_optical_frame'
# expect: translation ~ [0.525, 0.018, 0.704], optical +Z pointing down
```

### 4. Run the Color Pointing Node

**Terminal 3** (after boxes are spawned):

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

The node prints a `cr5>` prompt if stdin is interactive. Type commands directly:

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

**If no prompt appears** (non-interactive docker exec), send commands from another terminal:

```bash
# Scan first — moves wrist camera above the boxes
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'scan'"'"'"'

# Move above a box
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'Move above red.'"'"'"'

docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'Move above yellow.'"'"'"'

docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'Move above green.'"'"'"'

# Return home
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'Return home.'"'"'"'
```

> The command topic is `/cr5_color_pointing/command`. `rostopic pub -1` sends one message to the already-running node — it does **not** start a second node.

### 5. Verify Detection Before Moving

After `scan`, run the standalone debug detector:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py yellow'
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py green'
```

Expected output: blob found, valid depth, tabletop z near `0.0–0.20 m`.

Check pixel-level HSV content of the live camera image:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && python - <<'"'"'PY'"'"'
import rospy, cv2, numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
rospy.init_node("sample_wrist_image", anonymous=True)
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

Healthy counts from a verified run: red ≈ 2419, yellow ≈ 1810, green ≈ 2455. If all counts are zero, do not tune HSV — fix the camera view first.

---

## Real Robot Bringup (`feat/hardware-demo` only)

> The `fix/camera-position-fix` branch does **not** include hardware launch files.

### Prerequisites

1. CR5 controller powered on, emergency stop connected.
2. CR5 in **TCP mode** — in DobotStudio Pro, go to the main robot page → `Device mode` → select `TCP` / `TCP/IP Secondary Development`. The `Settings → Communication` page is for IP config only.
3. Static Ethernet interface on the same subnet as the CR5 (`192.168.5.x`):

```bash
nmcli connection add type ethernet ifname enp4s0 con-name cr5-direct \
  ipv4.method manual ipv4.addresses 192.168.5.10/24 \
  ipv4.never-default yes ipv6.method ignore autoconnect yes
nmcli connection up cr5-direct
```

Verify reachability:

```bash
docker exec -it cr5ros bash -lc 'nc -zv 192.168.5.1 29999 && echo dashboard ok'
docker exec -it cr5ros bash -lc 'nc -zv 192.168.5.1 30004 && echo feedback ok'
```

Confirmed port behavior on the tested CR5A:

| Port | Status |
|---|---|
| `29999` | Open — dashboard + motion commands (ServoJ) |
| `30004` | Open — 1440-byte realtime feedback stream |
| `30005` | Open — realtime feedback |
| `30003` | **Refused** on this controller |

### Option A — Full hardware launch (with camera)

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   roslaunch cr5_color_pointing hardware_color_pointing.launch robot_ip:=192.168.5.1'
```

This starts: Dobot bringup → MoveIt (`cr5_moveit.launch`) → color pointing node loaded from `config/hardware.yaml`.

Default perception mode is `point_topic`. Publish calibrated detections to:

```text
/cr5_color_pointing/detections/red     # geometry_msgs/PointStamped
/cr5_color_pointing/detections/yellow
/cr5_color_pointing/detections/green
```

To use an RGB-D camera instead, set `perception/mode: rgbd` in `hardware.yaml`.

### Option B — Motion-only launch (scan/home, no camera required)

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   roslaunch cr5_color_pointing hardware_motion_only.launch robot_ip:=192.168.5.1'
```

Same as Option A but red/yellow/green commands are rejected immediately. Use for initial joint motion testing.

### Option C — Gazebo shadow viewer during hardware demo

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   roslaunch cr5_color_pointing hardware_gazebo_shadow.launch'
```

Starts Gazebo **paused** with a display-only `hardware_robot` model mirroring the real robot's `/joint_states`. **Do not run `run-cr5-gazebo` alongside hardware control** — it starts a conflicting simulation stack.

### Hardware preflight checks

Before issuing any robot commands, the node verifies:

- `/dobot_bringup/msg/RobotStatus` is present
- `is_connected: True`
- `is_enable: True`
- Configured detection source topic available (for color commands)

Enable the robot from the Dobot RViz plugin or:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   rosservice call /dobot_bringup/srv/EnableRobot'
```

### Hardware motion settings (`config/hardware.yaml`)

| Setting | Value |
|---|---|
| `motion/max_velocity_scaling` | `0.05` |
| `motion/max_acceleration_scaling` | `0.05` |
| `hardware/speed_factor` | `10` |
| `motion/controller_action` | `/follow_joint_trajectory/follow_joint_trajectory` |
| `motion/above_box_extra_clearance` | `0.25 m` |
| Simulation fallbacks | disabled |

### Hardware demo commands

Same command set as simulation — send via the `cr5>` prompt or the ROS topic:

```text
scan               ← moves to observation pose (low speed)
Move above red.    ← requires camera/point detections
Move above yellow.
Move above green.
Return home.
```

---

## Supported Commands (All Modes)

| Typed or published | Effect |
|---|---|
| `scan` / `Scan.` | Move to observation pose |
| `red` / `Move above red.` | Detect red box, move above it |
| `yellow` / `Move above yellow.` | Detect yellow box, move above it |
| `green` / `Move above green.` | Detect green box, move above it |
| `home` / `Return home.` | Return all joints to `[0,0,0,0,0,0]` |
| `quit` | Shut down the node |

Color commands automatically skip the scan move if the current joints are already within `0.035 rad` of the observation pose.

---

## Configuration Reference

### `config/demo.yaml` (simulation)

| Key | Value | Description |
|---|---|---|
| `motion/observation_joints` | `[0.344, -0.208, -0.520, -0.888, 1.570, 0.352]` | Scan pose (joint space) |
| `motion/safety_height` | `0.25` m | Minimum height above box |
| `motion/above_box_extra_clearance` | `0.25` m (`0.15` on hw-demo branch) | Extra gripper clearance |
| `motion/scan_joint_tolerance` | `0.035` rad | Tolerance to skip redundant scan |
| `motion/above_box_orientation_xyzw` | `[0.707, -0.707, 0.0, 0.0]` | Camera pointing down |
| `motion/center_camera_over_box` | `true` | Compensate camera offset from Link6 |
| `motion/max_velocity_scaling` | `0.2` | Sim speed |
| `frames/planning_frame` | `world` | MoveIt planning frame |

### `config/hardware.yaml` (real robot, `feat/hardware-demo` only)

Key differences from `demo.yaml`:

| Key | Value |
|---|---|
| `frames/planning_frame` | `dummy_link` |
| `motion/max_velocity_scaling` | `0.05` |
| `motion/max_acceleration_scaling` | `0.05` |
| `hardware/speed_factor` | `10` |
| `perception/mode` | `point_topic` |
| `motion/observation_joints[0]` | `-1.227` (rotated view for real layout) |

### `config/color_thresholds.yaml`

HSV ranges for detection. Tune these only after confirming that the camera image actually contains saturated color pixels.

---

## Troubleshooting

### Helper commands missing

```bash
source ~/.bashrc
# still missing:
cd /teamspace/studios/this_studio && ./setup-docker.sh && source ~/.bashrc
```

### Docker container missing

```bash
docker ps -a && docker images | grep cr5
cd /teamspace/studios/this_studio && ./setup-docker.sh
```

### Stale Gazebo / duplicate launch

```bash
docker exec -it cr5ros bash -lc \
  'pkill -f roslaunch || true; pkill -f rosmaster || true; pkill -f "gzserver" || true'
run-cr5-gazebo
```

### Robot collapses or moves wildly in Gazebo

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic echo -n 1 /joint_states'
```

Likely causes: wrong controller type, low effort limits, PID instability, strict abort tolerances.  
Control config files:

```text
cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
cr5_ws/src/CR5_ROS/cr5_moveit/config/gazebo_controllers.yaml
cr5_ws/src/CR5_ROS/cr5_moveit/scripts/unpause_after_controllers.py
```

### Camera topics missing after Gazebo launch

Gazebo requires the TurboVNC display `DISPLAY=:1` for camera rendering. If Gazebo was launched without a display, camera topics will not appear. Start the desktop first with `start-cr5-desktop`, then launch Gazebo.

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

If still empty, check `cr5_robot_gazebo.urdf` for `wrist_rgbd_camera_link`, `wrist_rgbd_camera_optical_frame`, and `libgazebo_ros_openni_kinect.so`.

### HSV finds no colors

1. View the camera image in `run-cr5-camera-rqt`.
2. Run the HSV sampling snippet above.
3. If all pixel counts are zero → the image rendering is wrong, not the thresholds. Check camera mount, scan pose, and Gazebo material scripts on the box SDF models.
4. If counts are nonzero but detection still fails → tune `config/color_thresholds.yaml`.

### Scan moves to wrong pose

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   timeout 5 rosrun tf tf_echo world wrist_rgbd_camera_optical_frame'
# expected: x≈0.525, y≈0.018, z≈0.704, optical +Z downward
```

Scan pose is configured in `config/demo.yaml` → `motion/observation_joints`.

### Hardware: "Control Mode Is Not Tcp"

Dashboard commands return this string while the CR5 is in Online/default mode. In DobotStudio Pro, navigate to the main robot page, click the current `Device mode` value, and switch to `TCP` / `TCP/IP Secondary Development`. Do not look under `Settings → Communication`.

### Command node shows no prompt

Normal when launched via `docker exec` without a PTY. Use `rostopic pub` from another terminal as shown above.

---

## Safety Rules

- Keep Gazebo gravity **ON**.
- Do **not** touch or grip the boxes.
- Keep all moves **above** the boxes (minimum 0.25 m + extra clearance).
- For hardware: verify the robot is enabled only after confirming the workspace is clear.
- Do not run the simulation Gazebo stack (`run-cr5-gazebo`) alongside hardware control.
- Use `hardware_gazebo_shadow.launch` instead for a Gazebo view during physical demos.

---

## Key Files

```text
# Setup
setup_cr5_lightning.sh              full environment setup (run once)
setup-docker.sh                     Docker-only recovery

# Host helper commands (~/.local/bin/)
start-cr5-desktop                   start TurboVNC/noVNC desktop
run-cr5-gazebo                      Gazebo + RViz + MoveIt
run-cr5-rviz                        RViz only
run-cr5-moveit                      MoveIt only
cr5-shell                           interactive shell in cr5ros
cr5-ensure-container                start/repair the container
run-cr5-camera-web                  web_video_server camera stream
run-cr5-camera-rqt                  rqt_image_view in VNC desktop

# Gazebo simulation
cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
cr5_ws/src/CR5_ROS/cr5_moveit/config/gazebo_controllers.yaml
cr5_ws/src/CR5_ROS/cr5_moveit/launch/gazebo.launch
cr5_ws/src/CR5_ROS/cr5_moveit/scripts/unpause_after_controllers.py

# Real robot URDF (feat/hardware-demo)
cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot.urdf

# Color pointing demo package
cr5_ws/src/cr5_color_pointing/config/demo.yaml           simulation config
cr5_ws/src/cr5_color_pointing/config/hardware.yaml       real-robot config
cr5_ws/src/cr5_color_pointing/config/color_thresholds.yaml
cr5_ws/src/cr5_color_pointing/launch/color_pointing.launch
cr5_ws/src/cr5_color_pointing/launch/spawn_colored_boxes.launch
cr5_ws/src/cr5_color_pointing/launch/hardware_color_pointing.launch
cr5_ws/src/cr5_color_pointing/launch/hardware_motion_only.launch
cr5_ws/src/cr5_color_pointing/launch/hardware_gazebo_shadow.launch
cr5_ws/src/cr5_color_pointing/scripts/color_pointing_node.py
cr5_ws/src/cr5_color_pointing/scripts/detect_color_once.py
cr5_ws/src/cr5_color_pointing/scripts/gazebo_joint_state_mirror.py
```

---

## Documentation Index

| Doc | Topic |
|---|---|
| [docs/README.md](docs/README.md) | Doc index |
| [docs/00_PROJECT_OVERVIEW.md](docs/00_PROJECT_OVERVIEW.md) | Project goals |
| [docs/01_LIGHTNING_DOCKER_ENVIRONMENT.md](docs/01_LIGHTNING_DOCKER_ENVIRONMENT.md) | Docker & Lightning setup |
| [docs/04_GAZEBO_CONTROL_FIX.md](docs/04_GAZEBO_CONTROL_FIX.md) | Effort controller fix history |
| [docs/05_WRIST_CAMERA_AND_PERCEPTION.md](docs/05_WRIST_CAMERA_AND_PERCEPTION.md) | Camera URDF, topics, TF |
| [docs/06_COLOR_POINTING_PACKAGE.md](docs/06_COLOR_POINTING_PACKAGE.md) | Package architecture |
| [docs/07_OPERATION_GUIDE.md](docs/07_OPERATION_GUIDE.md) | Step-by-step operation |
| [docs/08_SIM_TO_REAL_TRANSFER_PLAN.md](docs/08_SIM_TO_REAL_TRANSFER_PLAN.md) | Sim → real transfer |
| [docs/10_DECISIONS_LOG.md](docs/10_DECISIONS_LOG.md) | Design decisions |
| [docs/11_CHANGELOG.md](docs/11_CHANGELOG.md) | Change history |
| [docs/12_CURRENT_STATUS.md](docs/12_CURRENT_STATUS.md) | Latest verified state |
| [docs/15_REAL_ROBOT_BRINGUP.md](docs/15_REAL_ROBOT_BRINGUP.md) | Real robot bringup detail |
| [docs/CR5_TROUBLESHOOTING.md](docs/CR5_TROUBLESHOOTING.md) | Extended troubleshooting |
| [docs/CR5_CAMERA.md](docs/CR5_CAMERA.md) | Camera reference |
| [docs/CR5_VERIFICATION_CHECKLIST.md](docs/CR5_VERIFICATION_CHECKLIST.md) | Verification checklist |
