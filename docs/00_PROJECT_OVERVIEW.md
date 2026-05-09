# Project Overview

## Identity

This is a Dobot CR5 student robotics project developed on Lightning AI and accessed from Windows through VS Code Remote-SSH.

The environment is intentionally Docker-based so the ROS stack stays reproducible and compatible with the legacy repository.

| Item | Value |
| --- | --- |
| Host workspace | `/teamspace/studios/this_studio` |
| ROS workspace | `/teamspace/studios/this_studio/cr5_ws` |
| Original robot repo | `/teamspace/studios/this_studio/cr5_ws/src/CR5_ROS` |
| Color demo package | `/teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing` |
| Docker image | `cr5-ros-melodic-turbovnc:local` |
| Docker container | `cr5ros` |
| GUI display | `:1` |
| Robot type | `DOBOT_TYPE=cr5` |

## Compatibility Contract

Use this stack unless the user explicitly approves a migration:

| Layer | Selected stack |
| --- | --- |
| OS inside container | Ubuntu 18.04 |
| ROS | ROS 1 Melodic |
| Build system | `catkin_make` |
| Motion planning | MoveIt 1 |
| Simulator | Gazebo Classic 9 |
| Visualization | RViz from ROS Melodic |
| GUI desktop | TurboVNC with Fluxbox/xterm |
| Browser GUI fallback | noVNC through websockify |
| Camera web viewing | `web_video_server` |

Do not migrate by default to ROS 2, ROS Noetic, Ubuntu 22.04 native ROS, Ignition/Gazebo Sim, or newer Gazebo.

## Project Goal

The main demo goal is a wrist-camera-based "point at colored boxes" workflow.

The intended user commands are:

```text
Move above red.
Move above yellow.
Move above green.
Return home.
```

The robot should:

1. move to an observation pose,
2. use the wrist RGB-D camera,
3. detect red/yellow/green boxes using HSV thresholding,
4. estimate a 3D point from depth and `CameraInfo`,
5. transform that point into the planning/base frame with TF,
6. use MoveIt to move above the requested box,
7. avoid contact, grasping, or descending onto the box.

## Geometry Assumption

Use the Gazebo ground plane as the tabletop surface.

| Object | Convention |
| --- | --- |
| Table/surface plane | `z = 0` |
| CR5 base mount | `z = 0` |
| Colored cube bottom | `z = 0` |
| Colored cube center | `cube_size / 2` |
| Initial cube size | `0.05 m` |
| Initial safe clearance | at least `0.25 m` above the box |

Do not add a raised table unless that becomes an explicit design decision.

## Current Confirmed Facts

- The CR5 repository is present under `cr5_ws/src/CR5_ROS`.
- A `cr5_color_pointing` package exists under `cr5_ws/src`.
- The CR5 repo contains uncommitted Gazebo-control changes.
- The root workspace is not a git repository; `CR5_ROS` is a git repository.
- The setup script defines Docker image/container names and helper commands.
- Existing docs and AGENTS guidance are present in the root workspace.

## Current Reported Results

These were confirmed during the Gazebo control fix session, but were not re-run live during this documentation pass:

- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- Gazebo started with gravity ON.
- `joint_state_controller` reached `running`.
- `cr5_joint_trajectory_controller` reached `running`.
- `/cr5_joint_trajectory_controller/follow_joint_trajectory` existed.
- A small MoveIt execution smoke test returned success.
- The final joint state remained stable instead of exploding or collapsing.

## Needs Verification

- Visually confirm in TurboVNC that Gazebo shows the arm standing, holding position, and moving when RViz Execute is pressed.
- Reconfirm wrist camera topics after a clean `run-cr5-gazebo` launch.
- Reconfirm colored boxes are visible from the observation pose.
- Re-test `cr5_color_pointing` after the Gazebo controller fix, because older README notes mention fallback behavior from before the controller repair.

