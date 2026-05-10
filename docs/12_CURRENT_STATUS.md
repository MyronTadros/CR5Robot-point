# Current Status

Last documentation update: 2026-05-10

## Latest Update From Wrist Camera Scan/Home Repair

Confirmed in the latest runtime pass on 2026-05-10:

- `run-cr5-gazebo` launched with gravity ON.
- `cr5_joint_trajectory_controller` loaded as `effort_controllers/JointTrajectoryController`.
- Startup hold completed and `/joint_states` settled near zero with very small velocities.
- `cr5_moveit/scripts/unpause_after_controllers.py` is executable and starts from `roslaunch`.
- Colored boxes spawned successfully.
- The wrist camera is side-mounted near `Link6` at `xyz="0 0.12 0.08"` to avoid looking through wrist geometry.
- The `scan` command moved the wrist camera to a good overhead pose near `x=0.57, y=0.01, z=0.83` in `dummy_link`.
- The scan optical-frame orientation points down toward the ground-plane boxes.
- The scan RGB image contained red, yellow, and green boxes, with median depth around `0.83 m`.
- `detect_color_once.py` detected red, yellow, and green at plausible tabletop-height points.
- The command sequence `red -> scan -> yellow -> scan -> green -> home` completed through the real trajectory controller with simulated fallbacks disabled.
- `home` returned to near-zero launch/home joints.

Known non-blocking runtime noise:

- MoveIt still warns that the SRDF virtual joint child frame differs from the URDF root frame.
- MoveIt still warns that `kinematics_solver_attempts` is obsolete.
- A transient rospy topic-close traceback appeared during one green detection, but detection and motion completed.

## Live Inspection During This Docs Pass

Confirmed:

- workspace path: `/teamspace/studios/this_studio`,
- `AGENTS.md` exists,
- root `README.md` exists,
- `docs/` exists,
- `setup_cr5_lightning.sh` exists,
- `cr5_ws/src/CR5_ROS` exists,
- `cr5_ws/src/cr5_color_pointing` exists,
- root workspace is not a git repository,
- `CR5_ROS` is a git repository with uncommitted Gazebo-control changes,
- Docker image `cr5-ros-melodic-turbovnc:local` exists,
- Docker container `cr5ros` exists and is running,
- TurboVNC/noVNC desktop starts successfully.

Live Docker note:

- Earlier in the session, `docker ps -a` and `docker images` were empty. The source workspace was still present; only Docker local state had been wiped/reset.
- `setup-docker.sh` restored the Docker runtime from existing project files without recloning or resetting the source workspace.
- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed inside the restored container.
- `start-cr5-desktop` was verified: `Xvnc`, `fluxbox`, `websockify`, and `xterm` ran; ports `5901` and `6080` listened; noVNC returned `HTTP/1.1 200 OK`.

## Reported/Expected Environment

| Item | Value |
| --- | --- |
| Docker image | `cr5-ros-melodic-turbovnc:local` |
| Docker container | `cr5ros` |
| GUI display | `:1` |
| TurboVNC port | `5901` |
| noVNC port | `6080` |
| Camera stream port | `8080` |
| ROS stack | Ubuntu 18.04, ROS Melodic, Gazebo Classic 9, MoveIt 1 |

## Main Commands

```bash
start-cr5-desktop
run-cr5-rviz
run-cr5-moveit
run-cr5-gazebo
cr5-shell
run-cr5-camera-web
run-cr5-camera-rqt
```

Docker ROS command pattern:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && COMMAND_HERE'
```

## CR5_ROS Git Status Summary

Known modified files:

```text
cr5_moveit/launch/demo_gazebo.launch
cr5_moveit/launch/gazebo.launch
cr5_moveit/launch/move_group.launch
cr5_moveit/launch/ros_controllers.launch
cr5_moveit/package.xml
dobot_description/urdf/cr5_robot.urdf deleted in git status
```

Known untracked files:

```text
cr5_moveit/config/gazebo_controllers-old.yaml
cr5_moveit/config/gazebo_controllers.yaml
cr5_moveit/config/gazebo_moveit_controllers.yaml
cr5_moveit/launch/gazebo_moveit_controller_manager.launch.xml
cr5_moveit/scripts/unpause_after_controllers.py
dobot_description/urdf/cr5_robot-old.urdf
dobot_description/urdf/cr5_robot_gazebo-old.urdf
dobot_description/urdf/cr5_robot_gazebo.urdf
```

## Gazebo Control Status

Current implementation:

- The user-installed clean Gazebo URDF parses and preserves the conservative CR5 chain: `world -> dummy_link -> base_link -> Link1 -> ... -> Link6 -> wrist_rgbd_camera_link -> wrist_rgbd_camera_optical_frame`.
- The clean Gazebo URDF uses `EffortJointInterface` transmissions for `joint1` through `joint6`.
- The clean Gazebo URDF keeps normal joint bounds near `-3.14` and `3.14`; it does not use the earlier experimental `+/-4*pi` bounds.
- The clean Gazebo URDF keeps the original CAD inertials; it does not use the earlier guessed inertias.
- The clean Gazebo URDF keeps the wrist RGB-D camera and optical frame, with the camera plugin publishing from `wrist_rgbd_camera_optical_frame`.
- `cr5_joint_trajectory_controller` uses `effort_controllers/JointTrajectoryController`.
- MoveIt still maps to `cr5_joint_trajectory_controller/follow_joint_trajectory`.
- Startup loads controllers stopped, briefly unpauses to switch them to `running`, sends an initial hold trajectory, then leaves physics unpaused.
- `gazebo.launch` now sets all six configured initial joints to `0.0` and `reset_initial_pose=false`, so the startup helper does not call the direct model-configuration reset.
- XML/YAML syntax checks, `check_urdf`, and `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.

Accepted in the latest runtime pass:

- Gravity stayed ON.
- `joint_state_controller` and `cr5_joint_trajectory_controller` were running.
- The startup hold trajectory succeeded.
- The full color-pointing sequence returned home with near-zero joints and without Gazebo joint teleport fallback.

## Wrist Camera Status

Implemented:

- camera link/joint/plugin identifiers exist in URDF,
- expected topic family is `/wrist_rgbd/...`,
- runtime camera topics were present after Gazebo launch,
- RGB camera info published `640x480` in `wrist_rgbd_camera_optical_frame`,
- RGB frames published around `10-11 Hz`,
- TF from `Link6` to `wrist_rgbd_camera_optical_frame` was present.

Verified:

- RGB image from scan shows red, yellow, and green boxes.
- Depth data is usable for the boxes.
- TF from the camera optical frame to `dummy_link` is available during runtime.

## Color Pointing Status

Implemented:

- `cr5_color_pointing` package,
- HSV threshold config,
- RGB-D detector,
- command node,
- colored cube models and spawn launch.
- default command mode now uses MoveIt only and does not publish fake `/joint_states`,
- simulated detection and box-pose fallbacks are disabled by default.
- explicit `scan` command moves to a Cartesian wrist-camera overview pose.
- scan currently targets `Link6` at `[0.55, 0.12, 0.77]` with orientation `[0.0, 0.0, 1.0, 0.0]`, which places the side-mounted wrist camera above the yellow box and points it down at the ground-plane boxes.
- above-box commands use the same downward Link6 orientation.
- scan joints `[3.13, -0.8, 1.2, 0.0, 1.1, 0.0]` remain only as fallback if the Cartesian scan pose is removed from config.

Verified:

- red/yellow/green boxes spawned successfully at expected positions in the latest run.
- red detection returned about `x=0.451, y=-0.245, z=0.050`.
- yellow detection returned about `x=0.547, y=0.000, z=0.050`.
- green detection returned about `x=0.450, y=0.227, z=0.050`.
- red/yellow/green/home commands completed through MoveIt/Gazebo controller execution with fallbacks disabled.
