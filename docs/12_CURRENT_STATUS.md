# Current Status

Last documentation update: 2026-05-17

## Latest Update From Simulation Verification

Confirmed in the 2026-05-17 Docker/Gazebo runtime pass on `fix/camera-position-fix`:

- Source Control backup-file noise was from untracked timestamped `*.backup_before_*` and `*.backup_offsets_*` files; these are now ignored by `.gitignore`.
- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- Gazebo camera rendering required the TurboVNC display `DISPLAY=:1`; purely headless Gazebo disabled depth-camera rendering.
- `gazebo.launch` now exports Gazebo plugin paths needed by ROS camera plugins.
- Gazebo preserved `wrist_rgbd_camera_link` and `wrist_rgbd_camera_joint` instead of lumping the fixed camera link away.
- The wrist camera publishes `/wrist_rgbd/rgb/image_raw`, `/wrist_rgbd/rgb/camera_info`, `/wrist_rgbd/depth/image_raw`, `/wrist_rgbd/depth/camera_info`, and `/wrist_rgbd/depth/points`.
- The simulated wrist camera uses co-located RGB and depth sensors at the lens/front face so HSV detection sees real color while depth remains available.
- Colored boxes spawned successfully at the configured tabletop positions.
- From the observation workflow, the RGB image contained red, yellow, and green masks.
- `detect_color_once.py red` succeeded during the run.
- `Move above red.` completed; after the move `Link6` was near `dummy_link x=0.404, y=-0.240, z=0.577` while the red box was at `world x=0.45, y=-0.25, z=0.025`.
- `Move above yellow.` completed; after the move `Link6` was near `dummy_link x=0.502, y=0.005, z=0.575` while yellow was configured at `x=0.55, y=0.0`.
- `Move above green.` completed; after the move `Link6` was near `dummy_link x=0.401, y=0.249, z=0.576` while green was configured at `x=0.45, y=0.25`.
- `Return home.` completed and returned joints to near zero.


## Latest Update From Real Robot Motion-Only Prep

Implemented on 2026-05-14:

- Added `cr5_color_pointing/launch/hardware_motion_only.launch`.
- Added `hardware/motion_only` handling in `color_pointing_node.py`.
- In motion-only mode, the node still allows `scan` and `home`, but rejects red/yellow/green commands immediately.
- This path does not require camera topics for `scan` or `home`.
- Added `hardware_gazebo_shadow.launch` plus `gazebo_joint_state_mirror.py` for a hardware-safe Gazebo view.
- Split the Dobot driver TCP sockets into dashboard, realtime feedback, and motion-command connections.
- The hardware launch now uses dashboard port `29999`, realtime feedback port `30004`, and motion-command port `29999`.
- This CR5A controller accepts dashboard commands in TCP mode but still refuses port `30003`; no-op `ServoJ` on dashboard port `29999` returned success.
- Smoothed physical MoveIt execution by interpolating timed trajectories and streaming `ServoJ` every `0.05 s` instead of sending sparse trajectory waypoints as chunks.
- Restored `dobot_bringup/msg/RobotStatus.msg` after it was missing from the worktree.
- Dashboard services now read the Dobot response and return `res: -1` when the controller rejects the command.
- Fixed action cancellation so timed-out/cancelled goals no longer report succeeded.
- Added NetworkManager profile `cr5-direct` on host interface `enp4s0` with static address `192.168.5.10/24`.

Validation completed:

- Python syntax passed.
- XML parsing passed for the hardware launch files and real URDF.
- `roslaunch --nodes` resolved `hardware_motion_only.launch`.
- `roslaunch --nodes` resolved `hardware_gazebo_shadow.launch`.
- `roslaunch --nodes` resolved `hardware_color_pointing.launch motion_only:=true`.
- `check_urdf` passed for `cr5_robot.urdf`.
- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed inside `cr5ros`.
- Host and Docker reached `192.168.5.1:29999`.
- Host and Docker reached `192.168.5.1:30004`; sampled packets matched the expected realtime packet layout.
- Dashboard commands now return success in TCP mode: `RobotMode()`, `GetAngle()`, `GetPose()`, `GetErrorID()`, and `EnableRobot()` returned `0`.
- Port `30003` is still refused, while `30004` and `30005` stream realtime feedback.
- Driver-only bringup with `motion_port:=29999` reports `is_enable: True` and `is_connected: True`.
- `/dobot_bringup/srv/ClearError` and `/dobot_bringup/srv/EnableRobot` return `res: 0`.
- A no-op `/dobot_bringup/srv/ServoJ` call at the current joint angles returned `res: 0`.
- A no-op `FollowJointTrajectory` action through `/follow_joint_trajectory/follow_joint_trajectory` completed with action state `3`.
- Driver-only bringup publishes live `/joint_states` from `30004` feedback.
- `hardware_gazebo_shadow.launch gazebo_gui:=false` spawned a display-only `hardware_robot` model in Gazebo and used the real `/joint_states` source.
- Full motion-only launch brought up `cr5_robot`, `move_group`, RViz, `robot_state_publisher`, and `cr5_color_pointing`.
- Color command `red` was rejected by motion-only mode.
- `scan` is blocked by hardware preflight until both `is_enable` and `is_connected` are true.

Still pending:

- Supervised low-speed `scan` and `home` live tests.
- Camera-dependent color tests.

Operational note:

- Do not run the normal `run-cr5-gazebo` / `cr5_moveit demo_gazebo.launch` simulation stack during hardware control. It starts a separate simulated robot, controllers, MoveIt, `robot_state_publisher`, and `/joint_states`. Use `hardware_gazebo_shadow.launch` for a Gazebo view that follows the physical robot.

## Latest Update From Real Robot Bringup Prep

Implemented on 2026-05-13:

- Added `cr5_color_pointing/config/hardware.yaml` for the real CR5 path.
- Added `cr5_color_pointing/launch/hardware_color_pointing.launch`.
- Real hardware motion targets the Dobot driver action `/follow_joint_trajectory/follow_joint_trajectory`.
- Hardware mode disables Gazebo fallbacks and uses low speed settings: MoveIt velocity/acceleration scaling `0.05` and Dobot speed factor `10`.
- Hardware preflight now checks `/dobot_bringup/msg/RobotStatus`, requires the robot to be connected/enabled, and checks the configured detection source topic before color commands.
- Added `perception/mode: point_topic`, expecting `geometry_msgs/PointStamped` detections at `/cr5_color_pointing/detections/{color}`.
- Kept `perception/mode: rgbd` for the existing HSV + RGB-D detector.
- Added `cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot.urdf`, a non-Gazebo real MoveIt URDF with the verified wrist camera TF.
- The VX500 guide was checked: the camera is Mono 8, not RGB-D, so direct red/yellow/green HSV color detection requires a separate RGB/RGB-D stream or a calibrated VX500 point/result bridge.

Validation completed:

- Python compile passed for the modified Python files.
- YAML load checks passed for demo, hardware, and color-threshold configs.
- XML parse checks passed for the launch files and real URDF.
- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed inside `cr5ros`.
- `check_urdf` passed for `cr5_robot.urdf`.
- `roslaunch --nodes` resolved both the simulation and hardware color-pointing launches.

Not yet runtime verified:

- No physical CR5 controller was connected in this session.
- No live VX500/point bridge was available.
- Hardware motion still needs a supervised low-speed live test.

Local workspace note:

- `cr5_color_pointing/config/demo.yaml` had a pre-existing user edit changing simulation `motion/above_box_extra_clearance` to `0.15`; this session preserved that file content. The new hardware config uses `0.25`.

## Gazebo Box RGB Visibility Fix

Confirmed on 2026-05-13:

- The original simulation stack was already running with Gazebo, MoveIt, RViz, `cr5_color_pointing`, wrist RGB-D topics, controllers, and colored box models.
- `scan` moved to the observation pose through `cr5_joint_trajectory_controller` with action status `3`.
- At the scan pose, depth at the projected red/yellow/green box pixels was correct, but RGB pixels were gray and HSV mask counts were zero.
- The red, yellow, and green SDF models now use explicit Gazebo material scripts and emissive color terms.
- After deleting and respawning the boxes, the wrist RGB image contained red `2419`, yellow `1810`, and green `2455` mask pixels.
- `detect_color_once.py red`, `yellow`, and `green` all detected tabletop-height points.
- `Move above red.` completed through the trajectory controller with action status `3`.
- `Return home.` completed through the trajectory controller with action status `3`, and joints returned near zero.
- XML parse checks passed for the three box SDF files.
- `catkin_make -DCMAKE_BUILD_TYPE=Release` passed inside `cr5ros`.

## Latest Update From Gripper Clearance And Scan-Skip Fix

Confirmed in the 2026-05-11 high-clearance red-command runtime pass:

- `motion/above_box_extra_clearance` is now `0.25`.
- The default above-box camera target z is `ground_plane_z + cube_size + safety_height + above_box_extra_clearance`, which is `0.55 m`.
- `motion/scan_joint_tolerance` is now `0.035 rad`.
- Color commands skip the redundant observation-joint trajectory when live `/joint_states` are already within that tolerance.
- Python compile, YAML load, and `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- `run-cr5-gazebo` launched with gravity ON.
- `joint_state_controller` and `cr5_joint_trajectory_controller` were running.
- Wrist RGB-D topics were present.
- Colored boxes spawned successfully.
- Topic commands `scan`, `Move above red.`, and `Return home.` completed through the real trajectory controller; the red and home goals reported action status `3`.
- `Move above red.` skipped the redundant scan move with max joint error `0.0186 rad`.
- The color command received at `07:14:16.920` detected red by `07:14:17.319` and sent the above-red trajectory at `07:14:17.419`.
- Red detection logged `world x=0.454, y=-0.240, z=0.050`.
- After the red move, the camera frame was near `world x=0.458, y=-0.240, z=0.535`.
- The post-move camera optical +Z axis in world was `[-0.032, 0.007, -0.999]`, confirming the camera remained looking down.
- The post-move RGB image still contained the red box, with `2419` red-mask pixels.
- `home` returned to near-zero launch/home joints.

## Above-Box Camera Orientation Runtime Pass

Confirmed in the 2026-05-11 red-command runtime pass:

- The above-box orientation is now `[0.7071068, -0.7071068, 0.0, 0.0]`.
- `motion/center_camera_over_box` is enabled.
- The command node compensates for the fixed `Link6 -> wrist_rgbd_camera_optical_frame` camera offset before sending the Link6 above-box pose.
- Python compile, YAML load, and `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- `run-cr5-gazebo` launched with gravity ON.
- `joint_state_controller` and `cr5_joint_trajectory_controller` were running.
- Wrist RGB-D topics were present.
- Colored boxes spawned successfully.
- Topic commands `scan` and `Move above red.` completed through the real trajectory controller; the red goal reported action status `3`.
- Red detection logged `world x=0.454, y=-0.240, z=0.050`.
- After the red move, the camera frame was near `world x=0.452, y=-0.239, z=0.285`.
- The post-move camera optical +Z axis in world was `[-0.033, 0.007, -0.999]`, which confirms the camera is looking down rather than up.
- The post-move RGB image still contained the red box, with `13924` red-mask pixels.

## Main Camera Merge Runtime Pass

Confirmed in the 2026-05-11 runtime pass:

- `main` was merged into `fix/camera-position-fix` and conflicts were resolved.
- The active Gazebo camera mount is the main-branch VX500-style transform: `Link6 -> wrist_rgbd_camera_link` at `xyz="0 -0.055 0"` and `rpy="1.5708 -1.5708 0"`.
- The branch's stricter controller execution and joint-state tracking are still present in `color_pointing_node.py`.
- `color_pointing_node.py` and `detect_color_once.py` are executable.
- Python compile, YAML load, XML parse, and `catkin_make -DCMAKE_BUILD_TYPE=Release` passed.
- `run-cr5-gazebo` launched with gravity ON.
- `joint_state_controller` and `cr5_joint_trajectory_controller` were running; the trajectory controller type was `effort_controllers/JointTrajectoryController`.
- Wrist RGB-D topics were present.
- Colored boxes spawned successfully.
- `scan` moved through the trajectory controller with status `3`; latest scan placed the optical frame around `world x=0.525, y=0.018, z=0.704`.
- RGB sampling after scan found red `2418`, yellow `1806`, and green `2463` broad-mask pixels.
- Depth sampling after scan showed center depth around `0.706 m`.
- `detect_color_once.py` detected red, yellow, and green at tabletop-height points.
- The topic-command sequence `red -> scan -> yellow -> scan -> green -> home` completed through the real trajectory controller.
- All observed scan/color/home goals in the command sequence reported action status `3`.
- Simulated motion/detection fallbacks were disabled and unused.
- `home` returned to near-zero launch/home joints.

## Historical Gazebo/RViz Launch Check

Historical note from an earlier launch diagnosis:

- `run-cr5-gazebo` maps to `roslaunch cr5_moveit demo_gazebo.launch`.
- `demo_gazebo.launch` does include `moveit_rviz.launch`, so RViz is intended to start with Gazebo + MoveIt.
- A live check showed RViz processes had started, but the ROS/Gazebo graph was stale/running from an earlier launch.
- The captured launch output included `SpawnModel: Failure - entity already exists` and repeated duplicate `robot_state_publisher` shutdowns.
- `cr5_moveit/scripts/unpause_after_controllers.py` existed but lacked executable permission, causing roslaunch to report that it could not locate the node type.
- The helper script is now executable and `rosrun cr5_moveit unpause_after_controllers.py` resolves to the script.

General launch hygiene:

- Start only one Gazebo launch at a time; otherwise Gazebo model spawning fails because `robot` already exists.
- If a stale launch is running, stop that terminal or restart the `cr5ros` container before launching again.

## Previous Camera/Scan Repair Pass

Reported from the 2026-05-10 runtime passes before this merge session:

- `run-cr5-gazebo` launched with gravity ON.
- `cr5_joint_trajectory_controller` loaded as `effort_controllers/JointTrajectoryController`.
- Startup hold completed and `/joint_states` settled near zero with very small velocities.
- `cr5_moveit/scripts/unpause_after_controllers.py` is executable and starts from `roslaunch`.
- Colored boxes spawned successfully.
- Main branch camera geometry used a VX500-style wrist camera transform from `Link6` to `wrist_rgbd_camera_link`.
- `scan` moved to the configured `observation_joints`.
- Red was detected at world `(0.4543, -0.2395, 0.0501)` and moved above to `z=0.300`.
- Yellow was detected at world `(0.5513, 0.0019, 0.0500)` and moved above to `z=0.300`.
- Green was detected at world `(0.4545, 0.2446, 0.0500)` and moved above to `z=0.300`.
- Controller action status was `3` for the reported color moves.

Known non-blocking runtime noise:

- MoveIt still warns that the SRDF virtual joint child frame differs from the URDF root frame.
- MoveIt still warns that `kinematics_solver_attempts` is obsolete.
- A transient rospy topic-close traceback appeared during one green detection, but detection and motion completed.

## Workspace Git Layout

Confirmed:

- active workspace path in this session: `/home/mo-sameh1/Documents/GitHub/CR5Robot-point`,
- `AGENTS.md` exists,
- root `README.md` exists,
- `docs/` exists,
- `cr5_ws/src/CR5_ROS` exists,
- `cr5_ws/src/cr5_color_pointing` exists,
- the active git repository is the workspace root,
- `cr5_ws/src/CR5_ROS` is not a separate nested git repository in this checkout,
- Docker image `cr5-ros-melodic-turbovnc:local` exists,
- Docker container `cr5ros` exists and can be started by `cr5-ensure-container`,
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

## Root Git Status Summary

As of the 2026-05-11 merge session, meaningful pending changes are in the root git repository and include:

- the main-branch camera/SRDF updates,
- the branch color-pointing execution hardening,
- executable mode fixes for color-pointing scripts,
- documentation updates recording the merge and runtime verification.

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
- `gazebo.launch` sets all six configured initial joints to `0.0` and `reset_initial_pose=true`; the startup helper resets the model to the hold configuration before unpausing physics.
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
- Gazebo depth sensor remains attached to `wrist_rgbd_camera_link`, with plugin `frameName=wrist_rgbd_camera_optical_frame`.
- `wrist_rgbd_camera_optical_joint` uses the standard ROS optical rotation `rpy="-1.5708 0 -1.5708"`.
- Detection logs now include color, pixel, median depth, camera info frame, camera-frame XYZ, and transformed planning-frame XYZ.

Verified:

- RGB image from scan shows red, yellow, and green boxes.
- Depth data is usable for the boxes.
- TF from the camera optical frame to `world`/`dummy_link` is available during runtime.

## Color Pointing Status

Implemented:

- `cr5_color_pointing` package,
- HSV threshold config,
- RGB-D detector,
- command node,
- colored cube models and spawn launch.
- default command mode now uses MoveIt only and does not publish fake `/joint_states`,
- simulated detection and box-pose fallbacks are disabled by default.
- explicit `scan` command moves to a configured Cartesian scan pose when one is present, otherwise it moves to `observation_joints`.
- current merged config uses `observation_joints` for scan because the main-branch camera fix was verified with that pose.
- above-box commands use a fixed downward Link6 orientation and compensate the wrist-camera offset from `Link6`.
- above-box commands add `0.25 m` extra gripper clearance above the original camera safety height.
- color commands skip redundant scan motion when the current joints are already close to `observation_joints`.
- optional Cartesian scan config remains supported in code for debugging, but it is not the current default.

Verified:

- `scan` moved to `observation_joints`.
- Red detected at world `(0.4543, -0.2395, 0.0501)` and moved above; latest high-clearance run left the camera frame near `(0.4581, -0.2404, 0.5348)` with optical +Z `[-0.0319, 0.0069, -0.9995]`; controller status `3`.
- Yellow detected at world `(0.5513, 0.0019, 0.0500)` and moved above to `z=0.300`; controller status `3`.
- Green detected at world `(0.4545, 0.2446, 0.0500)` and moved above to `z=0.300`; controller status `3`.
- A direct PTY run accepted typed `red` at the `cr5>` prompt and again detected red at world `(0.4544, -0.2395, 0.0501)` before moving above it; controller status `3`.
