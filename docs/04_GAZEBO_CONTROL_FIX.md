# Gazebo Control Fix

## Problem

The CR5 displayed correctly in RViz but collapsed or behaved incorrectly in Gazebo.

Reason:

- RViz visualizes URDF/TF only.
- Gazebo simulates gravity, collision, joint dynamics, and controllers.
- The original Gazebo path did not provide a complete powered actuator/controller setup.

## Rejected Fixes

The following were rejected as primary fixes:

| Rejected option | Reason |
| --- | --- |
| Disable gravity | Breaks physical meaning and sim-to-real assumptions |
| Set the whole model static | Prevents real articulated simulation |
| Pose-reset hacks | Hide the controller problem |
| Damping-only fix | Does not provide MoveIt trajectory execution |

Gravity must remain ON.

## Files Changed

| File | Change |
| --- | --- |
| `dobot_description/urdf/cr5_robot.urdf` | Removed non-sim world anchor from normal URDF; preserved wrist camera |
| `dobot_description/urdf/cr5_robot_gazebo.urdf` | Gazebo-only simulation URDF; clean baseline preserves the original CR5 chain, CAD inertials, normal joint bounds, effort interfaces, stronger effort limits, Gazebo ROS control, and wrist camera |
| `cr5_moveit/config/gazebo_controllers.yaml` | Uses an effort trajectory controller with per-joint PID gains |
| `cr5_moveit/config/gazebo_moveit_controllers.yaml` | Added MoveIt controller mapping |
| `cr5_moveit/launch/gazebo_moveit_controller_manager.launch.xml` | Added MoveIt controller manager include |
| `cr5_moveit/launch/gazebo.launch` | Uses Gazebo URDF, paused launch, initial joints, controller launch, initial hold, auto-unpause |
| `cr5_moveit/launch/demo_gazebo.launch` | Uses Gazebo URDF and Gazebo MoveIt controller manager |
| `cr5_moveit/launch/move_group.launch` | Allows selecting the controller-manager config |
| `cr5_moveit/launch/ros_controllers.launch` | Loads Gazebo controllers and spawns named controllers |
| `cr5_moveit/scripts/unpause_after_controllers.py` | Waits for controllers, sends an initial hold trajectory, then unpauses physics |
| `cr5_moveit/package.xml` | Adds runtime dependencies for Gazebo control packages |

## Gazebo-Only URDF

The simulation-specific URDF is:

```text
/teamspace/studios/this_studio/cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot_gazebo.urdf
```

It keeps the wrist RGB-D camera and adds Gazebo-only control features.

## Base Anchoring

The clean Gazebo URDF includes a fixed world anchor:

```text
world -> dummy_link -> base_link
```

This represents the physical CR5 base being bolted to the table/surface while still allowing the arm joints to move.

The whole model is not made static.

`dummy_link` remains the existing parent frame for `base_link`; the clean baseline does not invert the original `dummy_link`/`base_link` semantics.

## Joint Limits And Dynamics

The Gazebo URDF sets nonzero simulation limits for actuated joints `joint1` through `joint6`.

Representative values:

| Joint | Effort | Velocity |
| --- | ---: | ---: |
| `joint1` | `200` | `1.5` |
| `joint2` | `350` | `1.5` |
| `joint3` | `300` | `1.5` |
| `joint4` | `120` | `1.2` |
| `joint5` | `100` | `1.2` |
| `joint6` | `60` | `1.2` |

These are simulation-control values, not a certified physical CR5 specification.

Current clean-baseline note:

- The clean URDF keeps the original lower/upper joint limits near `-3.14` and `3.14`; it does not use the earlier experimental `+/-4*pi` bounds.
- The clean URDF keeps the original CAD inertials; it does not use the earlier guessed simplified inertias.
- The clean URDF keeps the original kinematic chain and only adds simulation-specific anchor, transmissions, Gazebo ROS control, and wrist camera pieces.

## Transmissions

The Gazebo URDF adds `SimpleTransmission` entries for all six actuated joints.

Each uses:

```text
hardware_interface/EffortJointInterface
```

This matches the current controller strategy: effort trajectory control with PID gains so the simulated arm can apply torque against gravity.

## Gazebo ROS Control Plugin

The Gazebo URDF adds:

```xml
<gazebo>
  <plugin name="gazebo_ros_control" filename="libgazebo_ros_control.so">
    <robotNamespace>/</robotNamespace>
  </plugin>
</gazebo>
```

This creates the Gazebo-side ROS control hardware interface.

## Controller YAML

Controller config:

```text
cr5_moveit/config/gazebo_controllers.yaml
```

It defines:

- `joint_state_controller`,
- `cr5_joint_trajectory_controller`,
- per-joint PID gains under `cr5_joint_trajectory_controller/gains`.

The trajectory controller type is:

```text
effort_controllers/JointTrajectoryController
```

## MoveIt Controller Mapping

MoveIt mapping:

```text
cr5_moveit/config/gazebo_moveit_controllers.yaml
```

It maps MoveIt to:

```text
cr5_joint_trajectory_controller/follow_joint_trajectory
```

with joints:

```text
joint1
joint2
joint3
joint4
joint5
joint6
```

## Controller Spawner Fix

Original issue:

```text
controller_spawner
args=""
```

This caused the spawner to die with too few arguments.

Fixed behavior:

```text
joint_state_controller cr5_joint_trajectory_controller --stopped --timeout 60
```

Controllers are loaded stopped because switching them while Gazebo is paused can deadlock. The startup helper briefly unpauses physics to switch the controllers to `running`.

## Paused Startup And Auto-Unpause

Gazebo starts paused by default.

Reason:

- avoid a gravity drop before Gazebo ROS control is available,
- spawn in a non-colliding initial pose,
- let controllers start before normal runtime.

`unpause_after_controllers.py` waits for the controller manager and Gazebo unpause service, switches the stopped controllers to `running`, pauses again, sends a short initial hold goal through `cr5_joint_trajectory_controller/follow_joint_trajectory`, then unpauses physics.

The current clean-baseline launch sets:

```text
initial_joint1..initial_joint6 = 0.0
reset_initial_pose = false
```

This avoids the earlier direct `set_model_configuration` startup reset while still testing the real trajectory controller hold path.

Gravity remains ON after unpausing.

## Validation Results

Current session status:

| Check | Result |
| --- | --- |
| Static config inspection | effort controller path implemented |
| URDF XML and YAML syntax checks | passed |
| `check_urdf` tree check | passed; `world -> dummy_link -> base_link -> Link1 -> ... -> Link6 -> wrist_rgbd_camera_link -> wrist_rgbd_camera_optical_frame` |
| Docker image/container | restored and running |
| `catkin_make -DCMAKE_BUILD_TYPE=Release` | passed |
| Gazebo gravity/controller checks | gravity ON; effort controller running and claiming all six `EffortJointInterface` joints |
| Wrist camera topics | present after Gazebo launch |
| MoveIt action test | not attempted in the clean-baseline run because the pre-execute hold already failed |
| Physical Gazebo acceptance | failed; do not claim fixed |

Observed failed runtime modes:

- The clean baseline loads the correct URDF, controller YAML, and MoveIt action mapping.
- `cr5_joint_trajectory_controller` runs as `effort_controllers/JointTrajectoryController` and claims `joint1` through `joint6`.
- The initial hold trajectory aborted with action state `4`.
- `/joint_states` stayed finite, but velocities were unstable/high and several efforts saturated, especially wrist and elbow-related joints.

Conclusion:

The previous position-controller fix and the current clean effort-controller startup fixes are not sufficient acceptance evidence. The remaining blocker is Gazebo physics/controller dynamics under gravity, not XML parsing, controller loading, resource claiming, camera topics, or MoveIt action namespace mapping.

## Validation Commands

Rebuild after control-related edits:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && cd /root/cr5_ws && catkin_make -DCMAKE_BUILD_TYPE=Release'
```

Start:

```bash
run-cr5-gazebo
```

Check controllers:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
```

Check controller type:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosparam get /cr5_joint_trajectory_controller/type'
```

Check action topics:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep follow_joint_trajectory'
```

Check gravity:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /gazebo/get_physics_properties'
```

Check joint stability:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic echo -n 5 /joint_states'
```

## Still Needs Manual Verification

- In TurboVNC, visually confirm the CR5 stands and holds in Gazebo.
- In RViz, plan and execute a small `cr5_arm` motion.
- In Gazebo, confirm the robot follows that trajectory without collapsing.
