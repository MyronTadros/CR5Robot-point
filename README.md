# Dobot CR5 ROS Melodic Lightning Guide

This is the main operating guide for the CR5 student robotics workspace on Lightning AI. It explains how to set up Docker, start the desktop, launch RViz/MoveIt/Gazebo, test the wrist RGB-D camera, spawn colored boxes, run the color-pointing package, rebuild after changes, and recover from common failures.

Current workspace:

```text
host workspace: /teamspace/studios/this_studio
ROS workspace:  /teamspace/studios/this_studio/cr5_ws
CR5 repo:       /teamspace/studios/this_studio/cr5_ws/src/CR5_ROS
demo package:   /teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing
container:      cr5ros
image:          cr5-ros-melodic-turbovnc:local
container ws:   /root/cr5_ws
```

## Read This First

This project intentionally uses the old CR5-compatible stack:

- Ubuntu 18.04 inside Docker
- ROS 1 Melodic
- Gazebo Classic 9
- MoveIt 1
- RViz
- `catkin_make`
- TurboVNC/noVNC for GUI access
- `DOBOT_TYPE=cr5`

Do not migrate this project to ROS 2, ROS Noetic, Ubuntu 22.04 native ROS, Ignition/Gazebo Sim, or a newer Gazebo unless that becomes an explicit project decision.

The current milestone is the wrist-camera colored-box demo:

1. Run Gazebo + MoveIt.
2. Spawn red, yellow, and green boxes on the ground plane.
3. Move the wrist camera to `scan`, above the boxes.
4. Detect the requested color with HSV + RGB-D.
5. Move safely above the requested box.
6. Return home or scan again.

No gripper logic is in scope. The robot should not touch boxes.

## Current Status

Confirmed working or recently verified:

- Docker image/container can be restored without resetting source files using `./setup-docker.sh`.
- `start-cr5-desktop` starts TurboVNC/noVNC.
- `catkin_make -DCMAKE_BUILD_TYPE=Release` passes.
- `run-cr5-gazebo` launches Gazebo + RViz + MoveIt.
- Gazebo gravity remains ON.
- Gazebo controllers load as `effort_controllers/JointTrajectoryController`.
- Startup hold now completes after loosening controller abort tolerances and adding strong Gazebo-only passive joint damping.
- The robot can settle at startup with near-zero joint velocities.
- The wrist RGB-D camera is side-mounted near `Link6` with a small `0.12 m` side standoff and `0.08 m` vertical standoff to avoid self-occluding on the wrist.
- The `scan` command positions the wrist camera above the yellow-box area at about `x=0.57, y=0.01, z=0.83`, pointing downward.
- Wrist RGB-D camera topics exist.
- Colored boxes spawn successfully.
- HSV + RGB-D detection works for red, yellow, and green from scan.
- The full command sequence `red -> scan -> yellow -> scan -> green -> home` has been runtime-tested through the real MoveIt/Gazebo trajectory controller with simulated fallbacks disabled.

## What Has Been Done So Far

Docker and setup:

- Full project setup is in `setup_cr5_lightning.sh`.
- Docker-only recovery is in `setup-docker.sh`.
- Helper commands are installed in `~/.local/bin`.
- The Docker image is `cr5-ros-melodic-turbovnc:local`.
- The container is `cr5ros`.

Gazebo control:

- Gazebo simulation uses a separate URDF:

```text
/teamspace/studios/this_studio/cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
```

- The Gazebo URDF keeps the original CR5 kinematic chain and CAD inertials.
- The Gazebo URDF adds:
  - fixed `world -> dummy_link` anchor,
  - `EffortJointInterface` transmissions for `joint1` through `joint6`,
  - `gazebo_ros_control`,
  - wrist RGB-D camera links and plugin,
  - Gazebo-only effort/damping values.

- Gazebo controllers are configured here:

```text
/teamspace/studios/this_studio/cr5_ws/src/CR5_ROS/cr5_moveit/config/gazebo_controllers.yaml
```

- MoveIt Gazebo controller mapping remains:

```text
cr5_joint_trajectory_controller/follow_joint_trajectory
```

Color pointing:

- The demo package is:

```text
/teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing
```

- It includes:
  - HSV + RGB-D detector,
  - `scan`, `red`, `yellow`, `green`, `home`, `quit` commands,
  - colored box SDF models,
  - box spawn launch file,
  - color pointing launch file,
  - config in `config/demo.yaml`.

## First Terminal Setup

Every new Lightning terminal should start with:

```bash
source ~/.bashrc
```

Check that helper commands exist:

```bash
command -v start-cr5-desktop
command -v run-cr5-gazebo
command -v cr5-ensure-container
```

If those commands are missing, source bash again:

```bash
source ~/.bashrc
```

If they are still missing, run Docker recovery:

```bash
cd /teamspace/studios/this_studio
./setup-docker.sh
source ~/.bashrc
```

## Start The Desktop

Terminal 1:

```bash
source ~/.bashrc
start-cr5-desktop
```

Forward port `5901` in VS Code Remote-SSH.

Connect from Windows TurboVNC Viewer:

```text
localhost::5901
```

Expected desktop:

```text
black Fluxbox desktop with an xterm
```

Browser fallback:

```text
http://localhost:6080/
```

Forward port `6080` first if using noVNC.

## Docker Basics

Check Docker state:

```bash
docker ps
docker ps -a
docker images | grep cr5
```

Start or repair the container:

```bash
cr5-ensure-container
```

Open a shell inside the container:

```bash
cr5-shell
```

Run one command inside the container:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list'
```

Use this pattern for almost every ROS command:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && COMMAND_HERE'
```

## Docker-Only Recovery

Use this when Docker lost the image/container but the workspace files still exist:

```bash
cd /teamspace/studios/this_studio
./setup-docker.sh
source ~/.bashrc
```

This does not reclone the CR5 repository and does not reset source files. It rebuilds the local Docker image from the existing Dockerfile/workspace, recreates `cr5ros`, rebuilds the catkin workspace, and rewrites helper commands.

Use full setup only when intentionally starting over:

```bash
./setup_cr5_lightning.sh
```

Do not run full setup casually because it can redo broad setup work.

## Build

Run after changing ROS package files, Python nodes, launch files, configs, or URDFs:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && cd /root/cr5_ws && catkin_make -DCMAKE_BUILD_TYPE=Release'
```

Documentation-only changes do not need a rebuild.

Syntax checks:

```bash
xmllint --noout /teamspace/studios/this_studio/cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
python -c 'import yaml,sys; yaml.safe_load(open(sys.argv[1])); print("yaml ok")' /teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing/config/demo.yaml
python -m py_compile /teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing/scripts/color_pointing_node.py
```

## RViz Only

Terminal 1:

```bash
start-cr5-desktop
```

Terminal 2:

```bash
run-cr5-rviz
```

Expected:

- RViz opens in TurboVNC.
- CR5 model appears.
- No Gazebo physics is involved.

## MoveIt Only

Terminal 1:

```bash
start-cr5-desktop
```

Terminal 2:

```bash
run-cr5-moveit
```

Expected:

- RViz opens.
- MotionPlanning panel loads.
- Planning group is `cr5_arm`.

## Gazebo + MoveIt

Terminal 1:

```bash
start-cr5-desktop
```

Terminal 2:

```bash
run-cr5-gazebo
```

Expected:

- Gazebo Classic opens.
- RViz opens.
- CR5 spawns upright.
- Controllers start.
- Physics unpauses.
- Gravity remains ON.

Controller checks:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosparam get /cr5_joint_trajectory_controller/type'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep follow_joint_trajectory'
```

Gravity check:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /gazebo/get_physics_properties | grep -A4 gravity'
```

Joint-state stability check:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic echo -n 1 /joint_states'
```

Healthy startup should show finite positions and small velocities after a few seconds.

Manual MoveIt acceptance test:

1. In RViz, select planning group `cr5_arm`.
2. Plan a small safe motion.
3. Execute.
4. Watch Gazebo.
5. The arm should not collapse.
6. The arm should hold after execution.

## Camera Topics

Start Gazebo first:

```bash
run-cr5-gazebo
```

Check wrist topics:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

Expected topics include:

```text
/wrist_rgbd/rgb/image_raw
/wrist_rgbd/rgb/camera_info
/wrist_rgbd/depth/image_raw
/wrist_rgbd/depth/camera_info
/wrist_rgbd/depth/points
```

Check camera info:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic echo -n 1 /wrist_rgbd/rgb/camera_info'
```

Check image rate:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic hz /wrist_rgbd/rgb/image_raw'
```

Open image viewer:

```bash
run-cr5-camera-rqt
```

Or browser stream:

```bash
run-cr5-camera-web
```

Forward port `8080`, then open:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw
```

Camera TF check:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && timeout 5 rosrun tf tf_echo dummy_link wrist_rgbd_camera_optical_frame'
```

After `scan`, a good pose recently looked like:

```text
translation about [0.58, 0.01, 0.83]
RPY about [179 deg, 3 deg, 0 deg]
```

That means the optical frame is high above the boxes and pointing mostly down.

## Spawn Colored Boxes

Start Gazebo first:

```bash
run-cr5-gazebo
```

Spawn boxes:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

Default positions:

| Color | Model | x | y | z |
| --- | --- | ---: | ---: | ---: |
| red | `red_box` | `0.45` | `-0.25` | `0.025` |
| yellow | `yellow_box` | `0.55` | `0.0` | `0.025` |
| green | `green_box` | `0.45` | `0.25` | `0.025` |

Verify model states:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic echo -n 1 /gazebo/model_states'
```

## Color Pointing Commands

Launch Gazebo first:

```bash
run-cr5-gazebo
```

Spawn boxes:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

Start the pointing node:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

If an interactive prompt appears, use:

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

If there is no prompt, send ROS topic commands from another terminal:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Move above red.'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Move above yellow.'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Move above green.'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Return home.'\''"'
```

Important current note: `scan` movement works better now, but HSV detection is still not fully working because the latest camera image had no saturated red/yellow/green pixels. Use the detection checks below before trusting movement-to-color commands.

## Color Detection Checks

Run these after Gazebo is running, boxes are spawned, and `scan` has completed:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py yellow'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py green'
```

Accepted detection should report:

- blob found,
- valid depth,
- transformed point in `dummy_link`,
- z near the tabletop, roughly `0.0` to `0.20`.

Bad signs:

- `No red blob found in RGB image.`
- `No yellow blob found in RGB image.`
- `No green blob found in RGB image.`
- target z is near the wrist/camera height instead of tabletop height,
- image is gray/black with no saturated pixels.

Sample actual image HSV content:

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

If all color pixel counts are zero, fix the camera image/rendering view before editing HSV thresholds.

## Full Test Sequence

Use this sequence for a clean test:

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

Terminal 3:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

Terminal 4:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /gazebo/get_physics_properties | grep -A4 gravity'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && timeout 5 rosrun tf tf_echo dummy_link wrist_rgbd_camera_optical_frame'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py yellow'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py green'
```

Only after detection works, test:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Move above red.'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Move above yellow.'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Move above green.'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Return home.'\''"'
```

## Troubleshooting By Symptom

### Helper Command Not Found

Run:

```bash
source ~/.bashrc
command -v run-cr5-gazebo
```

If still missing:

```bash
cd /teamspace/studios/this_studio
./setup-docker.sh
source ~/.bashrc
```

### Docker Container Missing

Check:

```bash
docker ps
docker ps -a
docker images | grep cr5
```

Recover:

```bash
cd /teamspace/studios/this_studio
./setup-docker.sh
```

### Docker Exists But ROS Commands Fail

Use:

```bash
cr5-ensure-container
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack profile'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find cr5_moveit'
```

### TurboVNC Does Not Open

Run:

```bash
start-cr5-desktop
```

Check ports:

```bash
docker exec -it cr5ros bash -lc 'pgrep -a Xvnc || true'
```

Forward port `5901` again in VS Code Remote-SSH and connect to:

```text
localhost::5901
```

### Gazebo Does Not Launch

Check if a stale stack is running:

```bash
docker exec -it cr5ros bash -lc 'pgrep -a roslaunch || true; pgrep -a rosmaster || true; pgrep -a gzserver || true'
```

Stop live ROS/Gazebo processes only when you are intentionally cleaning the test:

```bash
docker exec -it cr5ros bash -lc 'pkill -f roslaunch || true; pkill -f rosmaster || true; pkill -f "gzserver -u" || true'
```

Then relaunch:

```bash
run-cr5-gazebo
```

### Robot Collapses Or Moves Wildly

Check controllers:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
```

Check gravity:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /gazebo/get_physics_properties | grep -A4 gravity'
```

Check joint states:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic echo -n 1 /joint_states'
```

Likely failing layer:

- controller not running,
- wrong controller type,
- effort limits too low,
- PID/damping unstable,
- trajectory abort tolerance too strict,
- Gazebo physics instability.

Current sim-only control files:

```text
cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
cr5_ws/src/CR5_ROS/cr5_moveit/config/gazebo_controllers.yaml
cr5_ws/src/CR5_ROS/cr5_moveit/scripts/unpause_after_controllers.py
```

### Camera Topics Missing

Gazebo must be running first.

Run:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

If missing, inspect:

```text
cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
```

Look for:

```text
wrist_rgbd_camera_link
wrist_rgbd_camera_optical_frame
libgazebo_ros_openni_kinect.so
frameName>wrist_rgbd_camera_optical_frame
```

### Scan Moves To Wrong Side

Run:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && timeout 5 rosrun tf tf_echo dummy_link wrist_rgbd_camera_optical_frame'
```

Expected scan is near:

```text
x: 0.55 to 0.60
y: near 0.0
z: around 0.8
orientation: optical z mostly downward
```

Scan config is here:

```text
cr5_ws/src/cr5_color_pointing/config/demo.yaml
```

Current scan settings:

```yaml
scan_target_link: Link6
scan_position: [0.55, 0.12, 0.77]
scan_orientation_xyzw: [0.0, 0.0, 1.0, 0.0]
above_box_orientation_xyzw: [0.0, 0.0, 1.0, 0.0]
```

### HSV Finds No Colors

First confirm the camera image actually contains color:

```bash
run-cr5-camera-rqt
```

or run the HSV sampling command in the Color Detection Checks section.

If the image has no saturated pixels, do not tune HSV thresholds yet. Fix camera image content first:

- camera sensor orientation,
- camera mount,
- scan pose,
- box visibility,
- Gazebo material/rendering.

If the image contains colored pixels but detector fails, then tune:

```text
cr5_ws/src/cr5_color_pointing/config/color_thresholds.yaml
cr5_ws/src/cr5_color_pointing/src/cr5_color_pointing/perception.py
```

### Command Node Has No Prompt

That is normal when launched through `docker exec` without interactive stdin. Send commands through the topic:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''scan'\''"'
```

Check subscriber:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic info /cr5_color_pointing/command'
```

If callback logs do not appear in the terminal, check `/rosout`:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && timeout 5 rostopic echo /rosout | grep cr5_color_pointing'
```

## Safety Rules

- Keep gravity ON.
- Do not set the robot static.
- Do not disable physics globally.
- Do not use direct Gazebo joint teleporting as the normal solution.
- Do not make the robot touch boxes.
- Do not add gripper logic for this demo.
- Keep all motions slow and above the boxes.
- Prefer sim-specific files for Gazebo fixes.
- Do not touch real robot bringup unless explicitly required.

## Important Files

Setup:

```text
setup_cr5_lightning.sh
setup-docker.sh
```

Host helper commands:

```text
~/.local/bin/start-cr5-desktop
~/.local/bin/run-cr5-gazebo
~/.local/bin/run-cr5-rviz
~/.local/bin/run-cr5-moveit
~/.local/bin/cr5-shell
~/.local/bin/cr5-ensure-container
~/.local/bin/run-cr5-camera-web
~/.local/bin/run-cr5-camera-rqt
```

Gazebo control:

```text
cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
cr5_ws/src/CR5_ROS/cr5_moveit/config/gazebo_controllers.yaml
cr5_ws/src/CR5_ROS/cr5_moveit/config/gazebo_moveit_controllers.yaml
cr5_ws/src/CR5_ROS/cr5_moveit/launch/gazebo.launch
cr5_ws/src/CR5_ROS/cr5_moveit/launch/ros_controllers.launch
cr5_ws/src/CR5_ROS/cr5_moveit/scripts/unpause_after_controllers.py
```

Color pointing:

```text
cr5_ws/src/cr5_color_pointing/config/demo.yaml
cr5_ws/src/cr5_color_pointing/config/color_thresholds.yaml
cr5_ws/src/cr5_color_pointing/launch/spawn_colored_boxes.launch
cr5_ws/src/cr5_color_pointing/launch/color_pointing.launch
cr5_ws/src/cr5_color_pointing/scripts/color_pointing_node.py
cr5_ws/src/cr5_color_pointing/scripts/detect_color_once.py
cr5_ws/src/cr5_color_pointing/src/cr5_color_pointing/perception.py
```

Docs:

```text
docs/README.md
docs/04_GAZEBO_CONTROL_FIX.md
docs/05_WRIST_CAMERA_AND_PERCEPTION.md
docs/06_COLOR_POINTING_PACKAGE.md
docs/07_OPERATION_GUIDE.md
docs/11_CHANGELOG.md
docs/12_CURRENT_STATUS.md
```

## More Documentation

- [Project documentation index](docs/README.md)
- [Lightning Docker environment](docs/01_LIGHTNING_DOCKER_ENVIRONMENT.md)
- [Gazebo control fix notes](docs/04_GAZEBO_CONTROL_FIX.md)
- [Wrist camera and perception](docs/05_WRIST_CAMERA_AND_PERCEPTION.md)
- [Color pointing package](docs/06_COLOR_POINTING_PACKAGE.md)
- [Operation guide](docs/07_OPERATION_GUIDE.md)
- [Lightning workflow](docs/CR5_LIGHTNING_WORKFLOW.md)
- [Verification checklist](docs/CR5_VERIFICATION_CHECKLIST.md)
- [Camera guide](docs/CR5_CAMERA.md)
- [Troubleshooting](docs/CR5_TROUBLESHOOTING.md)
- [Maintenance notes](docs/CR5_MAINTENANCE.md)
