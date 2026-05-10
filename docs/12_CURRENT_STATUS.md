# Current Status

Last documentation update: 2026-05-09

## Live Gazebo/RViz Launch Check

Confirmed during a later launch diagnosis:

- `run-cr5-gazebo` maps to `roslaunch cr5_moveit demo_gazebo.launch`.
- `demo_gazebo.launch` does include `moveit_rviz.launch`, so RViz is intended to start with Gazebo + MoveIt.
- A live check showed RViz processes had started, but the ROS/Gazebo graph was stale/running from an earlier launch.
- The captured launch output included `SpawnModel: Failure - entity already exists` and repeated duplicate `robot_state_publisher` shutdowns.
- `cr5_moveit/scripts/unpause_after_controllers.py` existed but lacked executable permission, causing roslaunch to report that it could not locate the node type.
- The helper script is now executable and `rosrun cr5_moveit unpause_after_controllers.py` resolves to the script.

Needs operator cleanup before the next clean launch:

- Stop the currently running `run-cr5-gazebo` terminal or restart the `cr5ros` container before launching again.
- Start only one Gazebo launch at a time; otherwise Gazebo model spawning fails because `robot` already exists.
- Re-check the current `gazebo.launch` startup parameters before relying on this file: the checked launch file currently sets `reset_initial_pose=true`, while an earlier status note below says `false`.

## Previous Camera/Scan Repair Pass

Confirmed in the latest runtime pass:

- `run-cr5-gazebo` launched with gravity ON.
- `cr5_joint_trajectory_controller` loaded as `effort_controllers/JointTrajectoryController`.
- After loosening Gazebo trajectory abort tolerances and adding strong Gazebo-only passive joint damping/friction, startup hold completed and `/joint_states` settled near zero with very small velocities.
- Colored boxes spawned successfully.
- The `scan` command moved the wrist camera to a good overhead pose near `x=0.581, y=0.006, z=0.825` in `dummy_link`.
- The scan optical-frame orientation was nearly straight down, with RPY about `[179 deg, 3 deg, 0 deg]`.

Still not accepted:

- HSV detection is not working yet.
- From the corrected scan pose, the latest sampled RGB frame had only grayscale pixels: BGR min/max channels were equal and red/yellow/green broad HSV masks all had `0` pixels.
- Therefore the current failing layer is camera image/rendering content or Gazebo camera sensor orientation, not scan motion or controller startup.
- Full sequence `scan -> red -> scan -> yellow -> scan -> green` is not accepted yet.

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

Blocked:

- Gazebo control is not accepted yet. Runtime checks showed gravity ON and the effort controller running, but the arm still failed the physical acceptance criterion.
- The clean-baseline launch produced finite `/joint_states`, but the initial hold trajectory aborted with action state `4`.
- Runtime feedback showed high/unstable velocities and saturated efforts on several joints, so the failing layer is Gazebo physics/controller dynamics rather than URDF parsing, YAML loading, controller resource claiming, camera topics, or MoveIt action namespace mapping.

Needs manual verification:

- Do not proceed to color pointing yet.
- Continue Gazebo dynamics/controller tuning until TurboVNC shows the arm holding before, during, and after RViz MoveIt Execute with gravity ON.

## Wrist Camera Status

Implemented:

- camera link/joint/plugin identifiers exist in URDF,
- expected topic family is `/wrist_rgbd/...`,
- runtime camera topics were present after Gazebo launch,
- RGB camera info published `640x480` in `wrist_rgbd_camera_optical_frame`,
- RGB frames published around `10-11 Hz`,
- TF from `Link6` to `wrist_rgbd_camera_optical_frame` was present.
- Gazebo depth sensor remains attached to `wrist_rgbd_camera_link`, with plugin `frameName=wrist_rgbd_camera_optical_frame`.
- `wrist_rgbd_camera_optical_joint` uses the standard ROS optical rotation `rpy="-1.5708 0 -1.5708"`.
- Detection logs now include color, pixel, median depth, camera info frame, camera-frame XYZ, and transformed planning-frame XYZ.

Needs verification:

- RGB image shows colored boxes,
- depth data is usable,
- TF transform to `dummy_link` is correct.

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
- scan currently targets `Link6` at `[0.55, 0.0, 0.77]` with orientation `[0.0, 0.0, 1.0, 0.0]`, which should place the camera above the yellow box and point it down at the ground-plane boxes.
- scan joints `[3.13, -0.8, 1.2, 0.0, 1.1, 0.0]` remain only as fallback if the Cartesian scan pose is removed from config.

Needs verification:

- continue checking repeated runs after full Gazebo relaunches.

Verified on 2026-05-10:

- `scan` moved to `observation_joints`.
- Red detected at world `(0.4543, -0.2395, 0.0501)` and moved above to `z=0.300`; controller status `3`.
- Yellow detected at world `(0.5513, 0.0019, 0.0500)` and moved above to `z=0.300`; controller status `3`.
- Green detected at world `(0.4545, 0.2446, 0.0500)` and moved above to `z=0.300`; controller status `3`.
- A direct PTY run accepted typed `red` at the `cr5>` prompt and again detected red at world `(0.4544, -0.2395, 0.0501)` before moving above it; controller status `3`.
