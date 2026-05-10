# Changelog

Meaningful project changes should be recorded here.

## 2026-05-10 - Wrist Camera Scan/Home Runtime Repair

Status: implemented, build passed, runtime accepted

Changes:

- Side-mounted the Gazebo wrist RGB-D camera near `Link6` at `xyz="0 0.12 0.08"` so the camera remains attached to the wrist while no longer looking through wrist geometry.
- Updated `scan` to target `Link6` at `[0.55, 0.12, 0.77]` with downward orientation `[0.0, 0.0, 1.0, 0.0]`.
- Added a fixed downward above-box orientation so red/yellow/green moves keep a predictable wrist pose.
- Changed `home` behavior to use configured launch/home joints directly.
- Hardened color-pointing execution to wait for fresh `/joint_states`, require usable MoveIt plans, wait for controller results, and record current joints from real controller state.
- Marked `cr5_moveit/scripts/unpause_after_controllers.py` executable so `roslaunch` starts it directly.

Validation:

- XML/YAML/Python checks, `check_urdf`, and `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- Fresh `run-cr5-gazebo` launched with gravity ON and both Gazebo controllers running.
- Colored boxes spawned; scan image contained red, yellow, and green pixels with plausible depth.
- `detect_color_once.py` detected all three colors at tabletop height.
- Runtime sequence `red -> scan -> yellow -> scan -> green -> home` completed through the real trajectory controller with simulated fallbacks disabled.

## 2026-05-09 - Next Agent TODO Handoff

Status: documented

Changes:

- Added `docs/14_NEXT_AGENT_TODO.md` as a dedicated handoff for future Codex/agent sessions.
- Captured what is already achieved, the current blocking layer, exact reproduction commands, next debugging steps, acceptance criteria, and required future documentation updates.
- Linked the new handoff document from `docs/README.md`.

## 2026-05-09 - Root README Operating Manual Rewrite

Status: documented

Changes:

- Replaced the short root `README.md` with a detailed operating guide covering setup, Docker recovery, desktop startup, RViz, MoveIt, Gazebo, camera topics, box spawning, color pointing commands, detection checks, full test sequence, troubleshooting, safety rules, and important files.
- Documented the latest verified state honestly: Gazebo startup and scan pose are improved, but HSV color detection is not accepted because the corrected scan image still contained no saturated red/yellow/green pixels.
- Updated `docs/12_CURRENT_STATUS.md` with the latest scan/control/perception findings.

## 2026-05-09 - Add Explicit Scan Command

Status: implemented

Changes:

- Added `scan` command support to `cr5_color_pointing`.
- `scan`, `move to scan`, `go to scan`, and `return to scan` now move the arm to a Cartesian wrist-camera overview pose.
- Color commands still move to the observation/scan pose before detection, then move above the requested color.
- Updated scan to target `Link6` at `[0.55, 0.0, 0.77]` with orientation `[0.0, 0.0, 1.0, 0.0]`, placing the wrist camera above the yellow box and pointing down toward the ground.
- Kept `[3.13, -0.8, 1.2, 0.0, 1.1, 0.0]` only as the joint fallback if the Cartesian scan pose is removed from config.
- Corrected an out-of-bounds scan value; joint1 is limited to `3.14`, so `3.1416` was rejected by MoveIt.
- Updated package docs to show the intended workflow: scan, move above a color, scan again.

## 2026-05-09 - Color Pointing Strict MoveIt/Camera Mode

Status: implemented, build passed, movement acceptance blocked

Changes:

- Updated `cr5_color_pointing` defaults to use the real MoveIt/Gazebo trajectory-controller path only: `motion/execution_mode: moveit`.
- Changed the configured camera frame to `wrist_rgbd_camera_optical_frame`.
- Disabled simulated detection fallback and simulated/configured box-pose fallback by default.
- Changed `color_pointing_node.py` so it does not publish fake `/joint_states` or create Gazebo joint-teleport fallback services unless fallback mode is explicitly enabled.
- Left the working Gazebo control URDF/YAML untouched.

Validation:

- Wrist RGB-D topics were present: RGB image, RGB camera info, depth image, depth camera info, and depth points.
- RGB camera info published `640x480` in `wrist_rgbd_camera_optical_frame`; RGB frames published around `10-11 Hz`.
- TF from `Link6` to `wrist_rgbd_camera_optical_frame` was present.
- Red/yellow/green boxes spawned successfully at the expected ground-plane positions.
- Python syntax checks, YAML parse, and `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- Runtime parameter checks confirmed strict mode: `execution_mode=moveit`, simulated fallbacks disabled, and `/joint_states` published only by Gazebo.

Blocked:

- The configured observation-pose MoveIt execution aborted at the controller action layer with status `4`; the pointing node therefore skipped detection and did not execute move-above commands.
- A one-shot red detector test from the current/attempted pose detected a red blob, but the transformed point was near the robot/wrist height rather than the tabletop; yellow and green were not visible. The failing layers for the demo are the observation motion/camera view and then perception, not box spawning or topic publication.

## 2026-05-09 - Clean Gazebo Effort Control Compatibility Repair

Status: implemented, build passed, physical Gazebo acceptance failed

Changes:

- Verified the user-installed clean Gazebo URDF parses and keeps the conservative chain `world -> dummy_link -> base_link -> Link1 -> ... -> Link6 -> wrist_rgbd_camera_link -> wrist_rgbd_camera_optical_frame`.
- Verified the clean URDF keeps normal joint bounds, nonzero effort/velocity limits, original CAD inertials, `EffortJointInterface` transmissions, `gazebo_ros_control`, and the wrist camera optical frame.
- Verified the clean controller YAML uses `effort_controllers/JointTrajectoryController`, joints `joint1` through `joint6`, PID gains for all six joints, and `joint_state_controller`.
- Made the minimal launch compatibility patch in `cr5_moveit/launch/gazebo.launch`: restored all six configured initial joints to SRDF home `0.0` and set `reset_initial_pose=false`.
- Kept `ros_controllers.launch` spawning `joint_state_controller cr5_joint_trajectory_controller --stopped --timeout 60`.
- Kept MoveIt mapped to `cr5_joint_trajectory_controller/follow_joint_trajectory`.
- Did not rewrite the clean URDF, widen joint limits, replace inertials, invert `dummy_link`/`base_link`, remove the optical frame, or touch real robot bringup.

Validation:

- `xmllint` passed for the clean URDF and Gazebo launch files.
- YAML parse passed for `gazebo_controllers.yaml`.
- `check_urdf` passed inside `cr5ros`.
- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed inside `cr5ros`.
- Runtime checks showed gravity ON, `joint_state_controller` running, `cr5_joint_trajectory_controller` running as an effort controller, all six joints claimed through `hardware_interface::EffortJointInterface`, `follow_joint_trajectory` topics present, and wrist RGB-D topics present.
- Acceptance still failed before manual RViz Execute: the initial hold trajectory aborted with action state `4`; `/joint_states` values were finite but unstable, with high velocities and saturated efforts. The failing layer is Gazebo physics/controller dynamics.

## 2026-05-09 - Gazebo Effort Control Re-Test

Status: not accepted yet

Changes:

- Fixed the paused-start deadlock by loading controllers stopped, briefly unpausing only to switch them to `running`, then sending the initial hold goal.
- Kept MoveIt mapped to `cr5_joint_trajectory_controller/follow_joint_trajectory`.
- Reworked the Gazebo-only URDF with effort interfaces, widened sim joint bounds, primitive collision geometry, and simplified diagonal inertias while preserving the real robot URDF path.

Validation:

- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- Gravity remained ON and physics remained enabled.
- `cr5_joint_trajectory_controller` ran as an `effort_controllers/JointTrajectoryController` and claimed `EffortJointInterface` resources for `joint1` through `joint6`.
- A small MoveIt execution returned `SUCCEEDED` at the action layer after widening sim joint bounds.
- Acceptance still failed: Gazebo joint feedback either produced `nan` velocities/no physical motion, or with simplified inertias produced finite but unstable motion and an aborted initial hold. Do not treat Gazebo control as visually fixed yet.

## 2026-05-09 - Docker-Only Runtime Restore

Status: implemented and verified

Changes:

- Added `setup-docker.sh` as a Docker-only recovery helper that uses the existing workspace and Dockerfile.
- Kept source checkout and project files intact; no repository reclone/reset is performed.
- Rebuilt `cr5-ros-melodic-turbovnc:local` and recreated `cr5ros`.
- Fixed TurboVNC 3.3 startup flags and made the Fluxbox session stay alive.
- Added `xfonts-base` for `xterm` startup.
- Started VNC/noVNC in separate sessions so they survive detaching from the helper log tail.

Validation:

- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed inside the rebuilt container.
- `rospack find` passed for `dobot_description`, `cr5_moveit`, `cr5_color_pointing`, and `effort_controllers`.
- `start-cr5-desktop` launched `Xvnc`, `fluxbox`, `websockify`, and `xterm`.
- Ports `5901` and `6080` were listening after detaching from the log tail.
- `curl -I http://127.0.0.1:6080/` returned `HTTP/1.1 200 OK`.

## 2026-05-09 - Effort-Based Gazebo Control Repair

Status: implemented, build passed, Gazebo visual verification still pending

Changes:

- Switched the Gazebo-only CR5 transmissions from `PositionJointInterface` to `EffortJointInterface`.
- Increased Gazebo simulation effort limits for `joint1` through `joint6`.
- Changed `cr5_joint_trajectory_controller` to `effort_controllers/JointTrajectoryController`.
- Moved PID gains under the effort trajectory controller namespace.
- Kept MoveIt mapped to `cr5_joint_trajectory_controller/follow_joint_trajectory`.
- Added an initial hold trajectory before Gazebo physics unpauses.
- Added runtime dependencies for effort control and the startup hold action client.

Validation:

- Local Python 3 syntax check passed for `unpause_after_controllers.py`.
- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed after restoring the Docker image/container.
- Controller/gravity/joint-state runtime checks still require launching `run-cr5-gazebo`.

## 2026-05-09 - Documentation Topic Set

Status: documented

Changes:

- Added numbered topic-based documentation files under `docs/`.
- Added documentation maintenance rules to `AGENTS.md`.
- Recorded Gazebo control fix, environment, package architecture, operation guide, roadmap, decisions, and current status.

## 2026-05-09 - Gazebo ROS Control Fix

Status: superseded by effort-based repair; previous visual acceptance was not confirmed

Changes:

- Added Gazebo-specific CR5 URDF: `cr5_robot_gazebo.urdf`.
- Added fixed world-to-`dummy_link` anchor in the Gazebo URDF.
- Added nonzero simulation joint limits and dynamics for `joint1` through `joint6`.
- Added `SimpleTransmission` entries with `PositionJointInterface`.
- Added `gazebo_ros_control` plugin.
- Added `gazebo_controllers.yaml`.
- Added `gazebo_moveit_controllers.yaml`.
- Fixed controller spawner args.
- Added Gazebo MoveIt controller-manager mapping.
- Removed Gazebo demo fake `joint_state_publisher`.
- Added paused startup and `unpause_after_controllers.py`.
- Added CR5 MoveIt runtime dependencies for Gazebo control packages.

Validation reported:

- catkin build passed,
- gravity ON,
- controllers running,
- FollowJointTrajectory action exists,
- MoveIt smoke execution passed.

## Earlier - Color Pointing Package

Status: implemented, needs re-test after Gazebo control fix

Changes:

- Added `cr5_color_pointing` package.
- Added HSV/depth detector.
- Added interactive command node.
- Added colored cube Gazebo models.
- Added launch/config files for boxes and pointing node.
- Added package README.

Known caveat:

- Package includes simulation fallback behavior from before the Gazebo controller fix.

## Earlier - Wrist RGB-D Camera

Status: implemented, needs clean runtime verification

Changes:

- Added wrist-mounted RGB-D camera block to `cr5_robot.urdf`.
- Camera uses `libgazebo_ros_openni_kinect.so`.
- Expected topic family is `/wrist_rgbd/...`.

## Earlier - Docker Lightning Setup

Status: setup script completed successfully in project history

Changes:

- Created Docker-based Ubuntu 18.04/ROS Melodic environment.
- Added TurboVNC/noVNC GUI support.
- Added helper commands under `~/.local/bin`.
- Built catkin workspace.

Fixes included:

- ROS apt ordering,
- Python ROS helper package conflicts,
- TurboVNC apt repository,
- ROS `set -u` issue,
- TurboVNC startup/xstartup issue.
