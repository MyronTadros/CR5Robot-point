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
| Planning frame | `dummy_link` |
| Camera frame | `wrist_rgbd_camera_optical_frame` |
| MoveIt group | `cr5_arm` |
| End link | `Link6` |
| Safety height | `0.25 m` |
| Cube size | `0.05 m` |
| Scan Link6 position | `[0.55, 0.0, 0.77]` |
| Scan Link6 orientation xyzw | `[0.0, 0.0, 1.0, 0.0]` |
| Observation/scan joints | `[3.13, -0.8, 1.2, 0.0, 1.1, 0.0]` |
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

`scan` uses a Cartesian MoveIt target instead of a guessed joint pose. The target places `Link6` near:

```text
x=0.55, y=0.0, z=0.77
```

with orientation:

```text
xyzw=[0.0, 0.0, 1.0, 0.0]
```

Because the wrist camera is fixed slightly above `Link6`, this puts the camera roughly above the yellow box and points the optical axis down toward the ground where the boxes sit.

The older `motion/observation_joints` value remains as a fallback if the Cartesian scan pose is removed from config.

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

## Needs Verification

- Rebuild after the Gazebo control fix.
- Re-test `detect_color_once.py red/yellow/green` from a settled observation pose.
- Re-test interactive commands.
- Tune the observation pose/camera view so the wrist camera sees the boxes without fallback.
