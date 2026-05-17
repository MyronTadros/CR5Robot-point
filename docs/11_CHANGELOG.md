# Changelog

Meaningful project changes should be recorded here.

## 2026-05-17 - Main Branch Submission Wording

Status: documented

Changes:

- Updated the root `README.md` to identify `main` as the software stack branch for the verified Gazebo/MoveIt color-pointing demo.
- Documented `hardware-demo` as the hardware stack branch for real CR5 integration.

Validation:

- Documentation-only change; no ROS rebuild required.

## 2026-05-17 - README Submission Polish

Status: documented

Changes:

- Added a concise Quick Start section to the root `README.md`.
- Clarified that commands should run from the repository root and that `/teamspace/studios/this_studio` is the Lightning default path, not a required clone location.
- Replaced several host-specific README paths with repository-relative paths.
- Clarified the difference between `run-cr5-camera-rqt` for TurboVNC viewing and `run-cr5-camera-web` for the browser stream on port `8080`.

Validation:

- Documentation-only change; no ROS rebuild required.

## 2026-05-17 - Portable Docker Setup Path

Status: implemented, script syntax/help verified

Changes:

- Updated `setup-docker.sh` to derive the project root from the script location instead of a developer-specific absolute path.
- The generated `cr5-ensure-container` helper now records the current clone's `cr5_ws` path when setup is run, so fresh GitHub checkouts can initialize Docker from their own location.

Validation:

- `bash -n setup-docker.sh` passed.
- `./setup-docker.sh --help` completed successfully.

## 2026-05-17 - Verified Simulation Wrist-Camera Color Pointing

Status: verified locally in Docker/Gazebo

Changes:

- Added `.gitignore` rules for timestamped local backup files.
- Updated `cr5_moveit/launch/gazebo.launch` so Gazebo can load ROS camera plugins and their Gazebo sensor dependencies.
- Preserved the fixed wrist-camera joint in Gazebo so `wrist_rgbd_camera_link` is not lumped away.
- Moved the simulated camera optical frame/sensors to the lens/front face.
- Split the simulated wrist camera into co-located RGB and depth sensors so HSV detection uses a true color image while depth remains available.

Validation:

- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- TurboVNC display `:1` was required for Gazebo camera rendering.
- Wrist RGB, depth, camera-info, and point-cloud topics published.
- Colored boxes spawned successfully.
- `Move above red.`, `Move above yellow.`, `Move above green.`, and `Return home.` completed through MoveIt/Gazebo.

## 2026-05-11 - Extra Gripper Clearance And Scan-Skip Latency Fix

Status: implemented, build passed, runtime verified for red

Changes:

- Added `motion/above_box_extra_clearance: 0.25`, so the above-box camera target now uses `cube_size + safety_height + extra_clearance`.
- Added `motion/scan_joint_tolerance: 0.035`.
- Updated `color_pointing_node.py` to skip the redundant observation-joint trajectory when a color command is issued from an already-scanned pose.

Validation:

- Python compile, YAML load, and `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- `run-cr5-gazebo` launched; controllers were running and wrist RGB-D topics were present.
- Colored boxes spawned successfully.
- Topic commands `scan`, `Move above red.`, and `Return home.` completed through the real trajectory controller with action status `3`.
- `Move above red.` skipped the redundant scan move with max joint error `0.0186 rad`.
- The color command received at `07:14:16.920` detected red by `07:14:17.319` and sent the above-red trajectory at `07:14:17.419`.
- The high-clearance red move left the camera frame near `world x=0.458, y=-0.240, z=0.535`, with optical +Z `[-0.032, 0.007, -0.999]`; the image still contained the red box.
- Simulated motion/detection fallbacks stayed disabled and unused.

## 2026-05-11 - Above-Box Wrist Camera Orientation Fix

Status: implemented, build passed, runtime verified for red

Changes:

- Changed the configured above-box orientation to `[0.7071068, -0.7071068, 0.0, 0.0]` so the merged wrist camera optical frame points down during color moves.
- Added `motion/center_camera_over_box: true`.
- Updated `color_pointing_node.py` to read the configured camera frame, normalize the above-box quaternion, look up the `Link6 -> wrist_rgbd_camera_optical_frame` offset, and compensate the Link6 target so the camera is centered over the detected box.

Validation:

- Python compile, YAML load, and `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- `run-cr5-gazebo` launched; controllers were running and wrist RGB-D topics were present.
- Colored boxes spawned successfully.
- Topic commands `scan` and `Move above red.` completed through the real trajectory controller with action status `3`.
- Detection logged red at `world x=0.454, y=-0.240, z=0.050`.
- After the red move, the camera frame was near `world x=0.452, y=-0.239, z=0.285`, the camera optical +Z axis in world was `[-0.033, 0.007, -0.999]`, and the RGB image contained `13924` red-mask pixels.
- Simulated motion/detection fallbacks stayed disabled and unused.

## 2026-05-11 - Main Camera Merge And Color Sequence Verification

Status: merged, build passed, runtime accepted

Changes:

- Merged `main` into `fix/camera-position-fix`.
- Resolved the Gazebo camera URDF conflict in favor of the main-branch VX500-style wrist mount: `Link6 -> wrist_rgbd_camera_link` at `xyz="0 -0.055 0"` and `rpy="1.5708 -1.5708 0"`.
- Kept the branch execution hardening in `color_pointing_node.py`: fresh `/joint_states` checks, strict controller result handling, configured home joints, and real controller-state tracking.
- Kept optional Cartesian scan support in code, but the current config uses the main-branch `observation_joints` scan pose.
- Marked `color_pointing_node.py` and `detect_color_once.py` executable so `roslaunch` and `rosrun` can start them from the source package.

Validation:

- Python compile, YAML load, XML parse, and `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- `run-cr5-gazebo` launched with gravity ON; `joint_state_controller` and `cr5_joint_trajectory_controller` were running.
- Wrist RGB-D topics published.
- Colored boxes spawned successfully.
- `scan` moved through the trajectory controller with status `3`.
- Camera image from scan contained red, yellow, and green pixels; center depth was about `0.706 m`.
- `detect_color_once.py red/yellow/green` detected tabletop-height points.
- Topic-command sequence `red -> scan -> yellow -> scan -> green -> home` completed through the real trajectory controller; all observed color/scan/home goals reported status `3`.
- Simulated motion/detection fallbacks were disabled and unused.

## 2026-05-10 - Wrist RGB-D Depth Frame Alignment

Status: runtime verified

Changes:

- Restored the standard ROS optical-frame fixed rotation on `wrist_rgbd_camera_optical_joint`.
- Kept the Gazebo depth sensor attached to the physical `wrist_rgbd_camera_link` while the plugin publishes `frameName=wrist_rgbd_camera_optical_frame`; this matches Gazebo camera sensor ray convention with ROS optical camera projection.
- Kept `/wrist_rgbd/...` topics unchanged.
- Added detection debug logging for color, pixel, median depth, camera info frame, camera-frame XYZ, and transformed target-frame XYZ.

Validation:

- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed inside `cr5ros`.
- Runtime command tests through `/cr5_color_pointing/command` passed after spawning colored boxes.
- A direct PTY CLI test also accepted typed `red` at the `cr5>` prompt and moved above red successfully.
- Red: pixel `(520,256)`, depth `0.6644`, world `(0.4543, -0.2395, 0.0501)`, moved above to `z=0.300`, controller status `3`.
- Yellow: pixel `(318,176)`, depth `0.6505`, world `(0.5513, 0.0019, 0.0500)`, moved above to `z=0.300`, controller status `3`.
- Green: pixel `(112,260)`, depth `0.6510`, world `(0.4545, 0.2446, 0.0500)`, moved above to `z=0.300`, controller status `3`.

## 2026-05-10 - Wrist Camera Scan/Home Runtime Repair

Status: implemented, build passed, runtime accepted on branch before the main-camera merge

Changes:

- Side-mounted the Gazebo wrist RGB-D camera near `Link6` at `xyz="0 0.12 0.08"` so the camera remained attached to the wrist while no longer looking through wrist geometry.
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

## 2026-05-09 - Gazebo/RViz Launch Error Diagnosis

Status: diagnosed, helper permission fixed

Changes:

- Diagnosed a `run-cr5-gazebo` failure where RViz was being started by `demo_gazebo.launch`, but the active ROS/Gazebo session was already stale/running.
- Confirmed launch output included `SpawnModel: Failure - entity already exists`, duplicate `robot_state_publisher` shutdowns, and a second RViz process.
- Fixed `cr5_moveit/scripts/unpause_after_controllers.py` permissions so roslaunch can execute the controller startup helper.
- Confirmed `rosrun cr5_moveit unpause_after_controllers.py` now resolves and starts the helper instead of reporting it as non-executable.

Notes:

- The existing launch from the user terminal was left running.
- Follow-up completed later: current docs record that `gazebo.launch` sets `reset_initial_pose=true`.

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
