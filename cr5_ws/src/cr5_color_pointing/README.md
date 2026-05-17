# cr5_color_pointing

ROS Melodic package for the Dobot CR5 wrist-camera color-pointing demo.

The robot moves to a joint-space observation pose, detects red/yellow/green boxes on the ground plane using HSV color thresholding and an RGB-D depth camera, then moves safely **above** the requested box with MoveIt. It does not grip or touch the boxes.

> **Branch:** `fix/camera-position-fix` — simulation only.  
> Hardware launches (`hardware_color_pointing.launch`, `hardware_motion_only.launch`, `hardware_gazebo_shadow.launch`) exist only in `feat/hardware-demo`.

---

## Package Layout

```text
config/
  demo.yaml               simulation config (Gazebo + MoveIt)
  color_thresholds.yaml   HSV detection ranges (tune here)
launch/
  color_pointing.launch         start MoveIt + pointing node
  spawn_colored_boxes.launch    spawn red/yellow/green SDF boxes in Gazebo
models/
  colored_box_red/    SDF with explicit Gazebo material + emissive color
  colored_box_yellow/
  colored_box_green/
scripts/
  color_pointing_node.py   main demo node (interactive prompt + topic interface)
  detect_color_once.py     standalone one-shot debug detector
src/cr5_color_pointing/
  perception.py            HSV + RGB-D detector
```

---

## Prerequisites

Start the TurboVNC desktop and Gazebo **before** this package:

```bash
start-cr5-desktop          # Terminal 1 — keep running (needed for camera rendering)
run-cr5-gazebo             # Terminal 2 — keep running
```

> Gazebo camera rendering requires `DISPLAY=:1` (TurboVNC). Camera topics will not appear if Gazebo was launched without a display.

---

## Simulation Quickstart

**1. Spawn colored boxes:**

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

Default positions:

| Color | x | y | z |
|---|---|---|---|
| red | 0.45 | −0.25 | 0.025 |
| yellow | 0.55 | 0.00 | 0.025 |
| green | 0.45 | 0.25 | 0.025 |

If boxes from a previous run appear gray in the camera, delete and respawn:

```bash
docker exec -it cr5ros bash -lc '
  source /usr/local/bin/cr5-env
  rosservice call /gazebo/delete_model "model_name: red_box"
  rosservice call /gazebo/delete_model "model_name: yellow_box"
  rosservice call /gazebo/delete_model "model_name: green_box"
  roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

**2. Verify camera topics:**

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
# expected:
# /wrist_rgbd/rgb/image_raw
# /wrist_rgbd/rgb/camera_info
# /wrist_rgbd/depth/image_raw
# /wrist_rgbd/depth/camera_info
# /wrist_rgbd/depth/points
```

**3. Launch the demo node:**

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

---

## Commands

The node accepts commands via:

1. **Interactive prompt** `cr5>` — type directly when stdin is a PTY.
2. **ROS topic** `/cr5_color_pointing/command` as `std_msgs/String`.

| Command | Aliases | Effect |
|---|---|---|
| `scan` | `Scan.` | Move to joint-space observation pose |
| `red` | `Move above red.` | Detect red box → move above it |
| `yellow` | `Move above yellow.` | Detect yellow box → move above it |
| `green` | `Move above green.` | Detect green box → move above it |
| `home` | `Return home.` | Return joints to `[0,0,0,0,0,0]` |
| `quit` | — | Shut down the node |

Sending commands from another terminal when no prompt is visible:

```bash
# Scan (move to observation pose)
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && \
   rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '"'"'scan'"'"'"'

# Move above a box
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

> `rostopic pub -1` sends one message to the **already-running** node. It does not start a second node.  
> At the `cr5>` prompt, type only the robot command (`red`, `Move above red.`, etc.) — not the full shell command.

---

## Verifying Detection

After `scan` completes, run the standalone debug detector:

```bash
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py yellow'
docker exec -it cr5ros bash -lc \
  'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py green'
```

Expected: blob found, valid depth, `z ≈ 0.0–0.20 m`.

Check pixel-level HSV content:

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

Healthy counts: red ≈ 2419, yellow ≈ 1810, green ≈ 2455.  
**If all counts are zero** → fix camera rendering before tuning HSV thresholds.

---

## Behavior Notes

- **Scan skip**: color commands skip the scan trajectory when current joints are within `0.035 rad` of `observation_joints`.
- **Camera offset compensation**: the node reads the `Link6 → wrist_rgbd_camera_optical_frame` TF and shifts the Link6 target so the camera is centered over the detected box.
- **Above-box height**: `ground_plane_z + cube_size/2 + safety_height + extra_clearance` = `0 + 0.025 + 0.25 + 0.25 = 0.525 m`.
- **Fallbacks disabled**: simulated detection and box-pose fallbacks are off; detection failures surface as real errors.

---

## Tuning

**HSV thresholds** → `config/color_thresholds.yaml`

**Motion behavior** → `config/demo.yaml`:

| Key | Value | Description |
|---|---|---|
| `motion/observation_joints` | `[0.344, -0.208, -0.520, -0.888, 1.570, 0.352]` | Scan pose |
| `motion/scan_joint_tolerance` | `0.035` | Tolerance (rad) to skip redundant scan |
| `motion/safety_height` | `0.25` | Min height above box (m) |
| `motion/above_box_extra_clearance` | `0.25` | Extra gripper clearance (m) |
| `motion/above_box_orientation_xyzw` | `[0.707, -0.707, 0.0, 0.0]` | Camera pointing down |
| `motion/center_camera_over_box` | `true` | Compensate Link6→camera TF offset |
| `motion/max_velocity_scaling` | `0.2` | MoveIt velocity scale |
| `scene/boxes` | red/yellow/green positions | Only used if fallback is enabled |
