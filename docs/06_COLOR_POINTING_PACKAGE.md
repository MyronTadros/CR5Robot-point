# Color Pointing Package

## Package Location

```text
/teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing
```

This package is separate from the original `CR5_ROS` repository so the student demo can evolve without changing upstream robot files unless necessary.

## Purpose

Implement the "point at colored boxes" demo:

```text
Move above red.
Move above yellow.
Move above green.
Return home.
Scan.
```

The robot should point above boxes, not grip or touch them.

## Files

| File | Purpose |
| --- | --- |
| `package.xml` | Catkin package manifest |
| `CMakeLists.txt` | Catkin build/install config |
| `setup.py` | Python package install config |
| `scripts/color_pointing_node.py` | Interactive command node |
| `scripts/detect_color_once.py` | Debug detector node |
| `src/cr5_color_pointing/perception.py` | HSV/depth/TF perception helper |
| `config/demo.yaml` | Topics, frames, MoveIt, motion, scene config |
| `config/color_thresholds.yaml` | HSV thresholds and detector params |
| `launch/color_pointing.launch` | Launch pointing node with configs |
| `launch/spawn_colored_boxes.launch` | Spawn red/yellow/green cubes |
| `models/colored_box_*` | Gazebo SDF models for colored cubes |
| `README.md` | Package-specific runbook |

## Default Demo Config

From `config/demo.yaml`:

| Setting | Value |
| --- | --- |
| RGB topic | `/wrist_rgbd/rgb/image_raw` |
| Depth topic | `/wrist_rgbd/depth/image_raw` |
| CameraInfo topic | `/wrist_rgbd/rgb/camera_info` |
| Planning frame | `world` |
| Camera frame | `wrist_rgbd_camera_optical_frame` |
| MoveIt group | `cr5_arm` |
| End link | `Link6` |
| Safety height | `0.25 m` |
| Cube size | `0.05 m` |
| Scan target link | `wrist_rgbd_camera_optical_frame` |
| Scan behavior | configured `observation_joints` |
| Above-box Link6 orientation xyzw | `[0.0, 0.0, 1.0, 0.0]` |
| Observation/scan joints | `[0.34378241586489544, -0.207839157537828, -0.5200047031534822, -0.8883737435138563, 1.5699748257363364, 0.3523303922635028]` |
| Home state | `home` |
| Command topic | `/cr5_color_pointing/command` |
| Execution mode | `moveit` |
| Simulated detection fallback | disabled |
| Simulated box-pose fallback | disabled |

Default box centers:

| Color | Position |
| --- | --- |
| red | `[0.45, -0.25, 0.025]` |
| yellow | `[0.55, 0.0, 0.025]` |
| green | `[0.45, 0.25, 0.025]` |

## Command Input Modes

Interactive launch:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

At the `cr5>` prompt, type only robot commands:

```text
scan
red
Move above yellow.
Return home.
quit
```

Topic command from another terminal:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic pub -1 /cr5_color_pointing/command std_msgs/String "data: '\''Move above red.'\''"'
```

Do not paste the full `docker exec ... rostopic pub ...` command at the `cr5>` prompt.

## Scan Pose

`scan` currently uses the configured joint-space observation pose. In the latest verification run, it placed `wrist_rgbd_camera_optical_frame` near:

```text
x=0.525, y=0.018, z=0.704 in world
```

with the optical frame mostly pointing down toward the boxes:

```text
RPY about [176 deg, -2 deg, -90 deg]
```

The command node still supports a configured Cartesian scan target if `motion/scan_position` and `motion/scan_orientation_xyzw` are reintroduced, but the current default intentionally uses `observation_joints` because that is the pose verified with the merged camera geometry.

The same downward Link6 orientation is used for above-box pointing targets so MoveIt does not choose arbitrary wrist orientations.

## Fallback Policy

The package was originally made usable before the Gazebo controller fix and included Gazebo fallback behavior:

- fallback to direct Gazebo joint configuration if MoveIt execution failed,
- fallback to simulated box model poses if camera detection failed or produced an implausible tabletop point.

Now that the Gazebo ROS control path is the intended baseline, the normal/default mode is strict:

- `motion/execution_mode: moveit`,
- no fake `/joint_states` publisher,
- no `/gazebo/set_model_configuration` motion fallback,
- no simulated detection or configured box-pose fallback.

Fallback code remains available only if explicitly re-enabled for emergency simulation debugging. It should not be used for the final camera/pointing acceptance test.

## Basic Launch Sequence

Start desktop:

```bash
start-cr5-desktop
```

Start Gazebo:

```bash
run-cr5-gazebo
```

Spawn boxes:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

Debug one color:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
```

Run command node:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

## Latest Verification

- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- `color_pointing_node.py` and `detect_color_once.py` are executable for `roslaunch`/`rosrun`.
- `detect_color_once.py red/yellow/green` passed from scan with tabletop-height points.
- Full topic-command sequence `red -> scan -> yellow -> scan -> green -> home` completed through the real MoveIt/Gazebo trajectory controller.
- Simulated motion/detection fallbacks remained disabled and unused.
