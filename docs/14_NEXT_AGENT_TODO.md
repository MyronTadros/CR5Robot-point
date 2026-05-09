# Next Agent TODO

This document is a handoff for the next Codex/agent session. Read it before making more changes.

## Project Goal

Build a Gazebo + MoveIt demo where the Dobot CR5:

1. starts in Gazebo with gravity ON,
2. holds itself physically using Gazebo ROS control,
3. spawns red/yellow/green cubes on the ground plane,
4. moves the wrist RGB-D camera to `scan`,
5. detects a requested color using HSV + RGB-D,
6. moves safely above the detected box,
7. returns to `scan` or `home`,
8. never grips, touches, or descends onto the boxes.

The intended command sequence is:

```text
scan
red
scan
yellow
scan
green
home
```

or topic commands like:

```text
Move above red.
Move above yellow.
Move above green.
Return home.
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
- If perception fails, diagnose camera image content before changing HSV thresholds.

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

## What Is Already Achieved

### Docker/Desktop

Confirmed:

- Docker image/container can be restored with `./setup-docker.sh` without resetting source files.
- `start-cr5-desktop` starts the TurboVNC/noVNC desktop.
- `catkin_make -DCMAKE_BUILD_TYPE=Release` passes.

Useful commands:

```bash
source ~/.bashrc
start-cr5-desktop
cr5-ensure-container
cr5-shell
```

### Gazebo Control

Current Gazebo simulation uses:

```text
cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
cr5_ws/src/CR5_ROS/cr5_moveit/config/gazebo_controllers.yaml
```

Confirmed in latest runtime pass:

- `run-cr5-gazebo` launches Gazebo + RViz + MoveIt.
- Gravity remains ON.
- `cr5_joint_trajectory_controller` is `effort_controllers/JointTrajectoryController`.
- Controller claims `joint1` through `joint6` through `EffortJointInterface`.
- Strong Gazebo-only passive damping/friction in the URDF lets the robot settle at startup.
- Startup hold completed in the latest run.
- `/joint_states` settled near zero with very small velocities after startup.

Important: the latest stability improvement came from Gazebo-only dynamics changes plus loose controller abort tolerances. Do not casually remove them.

### Scan Motion

Current scan config is in:

```text
cr5_ws/src/cr5_color_pointing/config/demo.yaml
```

Current scan parameters:

```yaml
scan_target_link: wrist_rgbd_camera_optical_frame
scan_position: [0.55, 0.0, 0.85]
scan_orientation_xyzw: [1.0, 0.0, 0.0, 0.0]
```

Confirmed in latest runtime pass:

- The `scan` command moved the wrist camera to about:

```text
x=0.581, y=0.006, z=0.825 in dummy_link
RPY about [179 deg, 3 deg, 0 deg]
```

- This means scan motion is now close to the intended pose: high above the boxes and mostly pointing downward.

### Boxes

Box spawning works:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

Default model positions:

| Color | Model | x | y | z |
| --- | --- | ---: | ---: | ---: |
| red | `red_box` | `0.45` | `-0.25` | `0.025` |
| yellow | `yellow_box` | `0.55` | `0.0` | `0.025` |
| green | `green_box` | `0.45` | `0.25` | `0.025` |

## Current Blocking Problem

The full demo is not accepted yet.

Latest failing layer:

```text
camera image / Gazebo rendering / camera sensor orientation
```

Not currently failing first:

```text
Docker
Gazebo launch
controller loading
startup hold
box spawning
scan motion
command topic plumbing
```

Latest HSV test result:

- From the corrected scan pose, `detect_color_once.py red`, `yellow`, and `green` all failed with no blob found.
- Sampling the RGB image showed only grayscale pixels:

```text
BGR min: [41, 41, 41]
BGR max: [202, 202, 202]
red pixels: 0
yellow pixels: 0
green pixels: 0
```

Interpretation:

- Do not tune HSV thresholds first.
- The camera image does not contain visible colored boxes.
- Next work should inspect camera sensor view direction, rendered image content, and depth image.

## Files Most Relevant For Next Work

Gazebo camera/robot:

```text
cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
```

Controller:

```text
cr5_ws/src/CR5_ROS/cr5_moveit/config/gazebo_controllers.yaml
```

Color pointing config:

```text
cr5_ws/src/cr5_color_pointing/config/demo.yaml
cr5_ws/src/cr5_color_pointing/config/color_thresholds.yaml
```

Color pointing nodes:

```text
cr5_ws/src/cr5_color_pointing/scripts/color_pointing_node.py
cr5_ws/src/cr5_color_pointing/scripts/detect_color_once.py
cr5_ws/src/cr5_color_pointing/src/cr5_color_pointing/perception.py
```

Box models:

```text
cr5_ws/src/cr5_color_pointing/models/colored_box_red/model.sdf
cr5_ws/src/cr5_color_pointing/models/colored_box_yellow/model.sdf
cr5_ws/src/cr5_color_pointing/models/colored_box_green/model.sdf
```

## Exact Test Sequence To Reproduce Current State

Terminal 1:

```bash
source ~/.bashrc
start-cr5-desktop
```

Terminal 2:

```bash
source ~/.bashrc
run-cr5-gazebo
```

Wait for Gazebo, RViz, MoveIt, controllers, and physics unpause.

Terminal 3:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

Terminal 4:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /gazebo/get_physics_properties | grep -A4 gravity'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic echo -n 1 /joint_states'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && timeout 5 rosrun tf tf_echo dummy_link wrist_rgbd_camera_optical_frame'
```

Then test detector:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py yellow'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py green'
```

## Next Debugging Steps

### 1. Confirm Camera Sees Only Gray

Run after `scan`:

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
print("bgr minmax", bgr.reshape(-1,3).min(axis=0).tolist(), bgr.reshape(-1,3).max(axis=0).tolist())
for name, ranges in {
    "red": [((0,40,30),(15,255,255)), ((165,40,30),(180,255,255))],
    "yellow": [((15,40,30),(45,255,255))],
    "green": [((35,30,20),(95,255,255))],
}.items():
    mask = None
    for lo, hi in ranges:
        m = cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
        mask = m if mask is None else cv2.bitwise_or(mask, m)
    print(name, "pixels", int(np.count_nonzero(mask)))
PY'
```

If color pixels are still zero, continue below.

### 2. Sample Depth Image

Run after `scan`:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && python - <<'"'"'PY'"'"'
import rospy, numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
rospy.init_node("sample_depth", anonymous=True)
d = CvBridge().imgmsg_to_cv2(rospy.wait_for_message("/wrist_rgbd/depth/image_raw", Image, timeout=5), desired_encoding="passthrough")
a = np.asarray(d).astype("float32")
v = a[np.isfinite(a) & (a > 0)]
print("depth shape", a.shape)
print("depth min/median/max", float(np.min(v)), float(np.median(v)), float(np.max(v)))
print("center depth", float(a[a.shape[0]//2, a.shape[1]//2]))
PY'
```

Interpretation:

- If depth is around `0.8 m`, the camera likely sees the ground plane.
- If depth is very small, the camera may see the robot/wrist.
- If depth is empty or invalid, the camera plugin/sensor is failing.

### 3. Inspect Actual Camera View

Open:

```bash
run-cr5-camera-rqt
```

or:

```bash
run-cr5-camera-web
```

Then browse:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw
```

Look for:

- gray floor only,
- robot/wrist occluding camera,
- boxes outside frame,
- boxes visible but rendered gray,
- image black/invalid.

### 4. Inspect Box Materials

Read:

```bash
for f in /teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing/models/colored_box_*/model.sdf; do
  echo "$f"
  sed -n '1,200p' "$f"
done
```

Potential issue:

- SDF visual material may show color in Gazebo GUI but the camera may render ambient/diffuse differently.
- If needed, add explicit ambient and diffuse colors for each model.

Do this only after confirming the camera points at the boxes.

### 5. Verify Sensor Direction

Important camera links:

```text
wrist_rgbd_camera_link
wrist_rgbd_camera_optical_frame
```

In URDF:

```text
sensor is attached to wrist_rgbd_camera_link
plugin frameName is wrist_rgbd_camera_optical_frame
```

Potential issue:

- Gazebo sensor ray direction may use `wrist_rgbd_camera_link`, while the plugin publishes TF as `wrist_rgbd_camera_optical_frame`.
- The scan target currently makes the optical frame look down, but the Gazebo sensor may be looking along the camera link axis instead.

Check TF:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && timeout 5 rosrun tf tf_echo dummy_link wrist_rgbd_camera_link'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && timeout 5 rosrun tf tf_echo dummy_link wrist_rgbd_camera_optical_frame'
```

If the sensor is using the wrong axis, minimally patch the camera fixed joints or sensor reference so the rendered image and published optical frame agree.

### 6. Only Then Tune HSV

If the camera image visibly contains colored boxes and the HSV sampler shows colored pixels, but `detect_color_once.py` still fails, tune:

```text
cr5_ws/src/cr5_color_pointing/config/color_thresholds.yaml
```

Then retest:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py yellow'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py green'
```

## Acceptance Criteria

Do not claim success until all are true:

- Gazebo launches with gravity ON.
- Robot starts upright and stable.
- `joint_state_controller` is running.
- `cr5_joint_trajectory_controller` is running as an effort controller.
- `scan` moves the wrist camera above the boxes and holds.
- Wrist RGB-D topics publish.
- RGB image visibly contains red/yellow/green boxes.
- HSV detects red, yellow, and green from scan.
- Detected 3D points are plausible and near tabletop height.
- `red` moves safely above the red box.
- `scan` returns to the overhead scan pose.
- `yellow` moves safely above the yellow box.
- `scan` returns to the overhead scan pose.
- `green` moves safely above the green box.
- `home` returns safely.
- No teleport fallback is used as the normal path.
- Robot does not collapse or touch boxes.

## Documentation Updates Required After Next Fix

When behavior changes, update:

```text
README.md
docs/11_CHANGELOG.md
docs/12_CURRENT_STATUS.md
docs/14_NEXT_AGENT_TODO.md
```

If the next fix changes camera design, also update:

```text
docs/05_WRIST_CAMERA_AND_PERCEPTION.md
docs/06_COLOR_POINTING_PACKAGE.md
```
