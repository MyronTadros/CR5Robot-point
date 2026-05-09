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

Status: provisional; not accepted yet

Decision:

Use `hardware_interface/EffortJointInterface` and `effort_controllers/JointTrajectoryController` in the Gazebo-specific CR5 control path.

Reason:

The position-interface Gazebo path exposed a trajectory action but was not sufficient evidence that the robot could hold against gravity during manual MoveIt execution. Effort control with PID gains better matches the acceptance criterion: gravity ON, physics enabled, base fixed, and the arm visually holding before, during, and after MoveIt Execute.

Runtime update:

Effort control now loads and claims the joints in the clean Gazebo baseline. The clean URDF preserves the original CR5 chain, normal joint bounds, and CAD inertials while adding the Gazebo-only anchor, effort transmissions, Gazebo ROS control plugin, and wrist camera. Physical acceptance still fails: the initial hold trajectory aborted with finite but unstable joint feedback and saturated efforts. Continue Gazebo dynamics/controller tuning before returning to camera or color pointing work.

## D010 - Documentation Must Track Behavior

Status: confirmed

Decision:

Every future behavior change should update relevant docs, changelog, current status, and decisions log.

Reason:

This project depends on many compatibility details that are easy to forget between sessions.
