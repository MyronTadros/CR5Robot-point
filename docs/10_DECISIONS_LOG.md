# Decisions Log

Record design decisions here when they change.

## D001 - Keep Legacy ROS Melodic Stack

Status: confirmed

Decision:

Use Ubuntu 18.04 in Docker, ROS 1 Melodic, Gazebo Classic 9, MoveIt 1, RViz, and `catkin_make`.

Reason:

The upstream CR5 repository is ROS 1/catkin and was treated as Melodic-era software.

## D002 - Use Docker On Lightning AI

Status: confirmed

Decision:

Run the ROS stack inside Docker rather than on the Lightning host directly.

Reason:

Docker preserves the old Ubuntu/ROS/Gazebo compatibility stack and makes the environment reproducible.

## D003 - Use TurboVNC/noVNC For GUI

Status: confirmed

Decision:

Use TurboVNC as the primary GUI desktop and noVNC/websockify as fallback.

Reason:

RViz and Gazebo require a GUI, and the user connects from Windows through VS Code Remote-SSH.

## D004 - Ground Plane Is The Tabletop

Status: confirmed

Decision:

Treat Gazebo ground plane as the table/surface at `z = 0`.

Reason:

This matches the planned real setup where robot base and boxes are on the same surface.

## D005 - Point Above Boxes, Do Not Grip

Status: confirmed

Decision:

The demo points above red/yellow/green boxes and does not implement grasping.

Reason:

This keeps the student project safer and focused on camera perception, TF, and MoveIt motion.

## D006 - HSV Color Thresholding, Not ML

Status: confirmed

Decision:

Use OpenCV HSV thresholding with RGB-D geometry instead of YOLO/ML.

Reason:

The objects are simple colored cubes, and the project does not need training, GPU inference, or classification complexity.

## D007 - Gravity Must Stay ON In Gazebo

Status: confirmed

Decision:

Fix Gazebo with ROS control, not by disabling gravity or making the robot static.

Reason:

The simulation should represent a powered, bolted-down robot and remain useful for sim-to-real work.

## D008 - Use Gazebo-Specific URDF For Control

Status: confirmed

Decision:

Create `cr5_robot_gazebo.urdf` for simulation-only anchors, transmissions, joint limits, and Gazebo ROS control plugin.

Reason:

This avoids mixing simulation-only controller infrastructure into the normal display/description path.

## D009 - Use Effort Trajectory Control In Gazebo

Status: confirmed for current simulation demo

Decision:

Use `hardware_interface/EffortJointInterface` and `effort_controllers/JointTrajectoryController` in the Gazebo-specific CR5 control path.

Reason:

The position-interface Gazebo path exposed a trajectory action but was not sufficient evidence that the robot could hold against gravity during manual MoveIt execution. Effort control with PID gains better matches the acceptance criterion: gravity ON, physics enabled, base fixed, and the arm visually holding before, during, and after MoveIt Execute.

Runtime update:

Effort control loads and claims the joints in the merged Gazebo baseline. The current URDF preserves the original CR5 chain, normal joint bounds, and CAD inertials while adding the Gazebo-only anchor, effort transmissions, Gazebo ROS control plugin, and wrist camera. The 2026-05-11 runtime pass accepted this setup for the color-pointing demo: startup completed with gravity ON, scan/color/home trajectories reported controller status `3`, and `home` returned to near-zero joints.

## D010 - Documentation Must Track Behavior

Status: confirmed

Decision:

Every future behavior change should update relevant docs, changelog, current status, and decisions log.

Reason:

This project depends on many compatibility details that are easy to forget between sessions.

## D011 - Use Main-Branch VX500-Style Wrist Camera Mount

Status: confirmed

Decision:

Use the merged main-branch Gazebo wrist camera transform from `Link6` to `wrist_rgbd_camera_link`:

```text
xyz="0 -0.055 0"
rpy="1.5708 -1.5708 0"
```

Keep `wrist_rgbd_camera_optical_frame` as the Gazebo plugin frame and retain the standard ROS optical-frame fixed rotation.

Reason:

This camera geometry was runtime verified after the 2026-05-11 merge: scan images contained all three colored boxes, RGB-D detections transformed to tabletop-height points, and the full color command sequence completed with fallbacks disabled.

## D012 - Keep Wrist Camera Down For Above-Box Moves

Status: confirmed

Decision:

Use `above_box_orientation_xyzw: [0.7071068, -0.7071068, 0.0, 0.0]` for color moves and keep `motion/center_camera_over_box: true`.

Reason:

With the merged VX500-style wrist camera mount, the previous above-box orientation could place `Link6` above the cube while rotating the camera toward the sky. The new orientation keeps `wrist_rgbd_camera_optical_frame` pointing downward, and the centering option compensates for the fixed camera offset from `Link6` so the camera frame stays over the detected box.

Runtime update:

On 2026-05-11, `scan` followed by `Move above red.` completed through the real trajectory controller with simulated fallbacks disabled. The post-move camera frame was near `world x=0.452, y=-0.239, z=0.285`, optical +Z in world was `[-0.033, 0.007, -0.999]`, and the RGB image still contained the red box.

## D013 - Add Real-Gripper Clearance For Above-Box Poses

Status: confirmed

Decision:

Keep the original `motion/safety_height: 0.25` and add `motion/above_box_extra_clearance: 0.25` for final above-box camera targets.

Reason:

The physical bringup robot has a gripper at the end effector. The demo should leave additional room between the end-effector assembly and the boxes, so the final camera target is intentionally higher than the earlier simulation-only pose.

Runtime update:

On 2026-05-11, the high-clearance `Move above red.` target completed through the real simulation trajectory controller. The post-move camera frame was near `world x=0.458, y=-0.240, z=0.535`, about `0.25 m` higher than the previous above-red camera pose, and the camera optical +Z axis still pointed down.

## D014 - Skip Redundant Scan Moves Before Color Detection

Status: confirmed

Decision:

When `observation_joints` are the active scan behavior, skip the scan trajectory if live `/joint_states` are already within `motion/scan_joint_tolerance` of the scan joints.

Reason:

After an explicit `scan`, the next color command was spending a full single-point trajectory duration on a no-op scan move before detection. Skipping the no-op keeps the physical command flow responsive while preserving the rule that detection starts from the observation pose.

Runtime update:

On 2026-05-11, after `scan`, `Move above red.` skipped the redundant scan trajectory with max joint error `0.0186 rad` against a `0.035 rad` tolerance. Detection started immediately and the above-red trajectory was sent about `0.5 s` after the command was received.
