# Original CR5 Repo Architecture

## Source Location

Original upstream repository checkout:

```text
/teamspace/studios/this_studio/cr5_ws/src/CR5_ROS
```

The repository is catkin-based and contains multiple packages.

## Package Layout

Confirmed package manifests:

| Package | Role |
| --- | --- |
| `dobot_description` | URDF, meshes, RViz display launch files |
| `dobot_moveit` | Generic MoveIt demo launch/config path |
| `cr5_moveit` | CR5-specific MoveIt/Gazebo launch/config path |
| `cr3_moveit` | CR3 MoveIt configuration, not the active robot target |
| `dobot_bringup` | Bringup-related package from the upstream repo |
| `rviz_dobot_control` | RViz control-related package |
| `cr5robot` | CR5 robot package from upstream repo |

## Important CR5 Files

| File | Purpose |
| --- | --- |
| `dobot_description/urdf/cr5_robot.urdf` | Main CR5 URDF for normal display/description path |
| `dobot_description/urdf/cr5_robot_gazebo.urdf` | Gazebo-specific simulation URDF added for ROS control |
| `dobot_description/launch/display.launch` | RViz display launch |
| `dobot_moveit/launch/demo.launch` | MoveIt planning demo |
| `cr5_moveit/launch/demo_gazebo.launch` | Combined Gazebo + MoveIt launch |
| `cr5_moveit/launch/gazebo.launch` | Gazebo world/model/controller launch |
| `cr5_moveit/config/cr5_robot.srdf` | MoveIt semantic model |
| `cr5_moveit/config/ros_controllers.yaml` | Original controller-style config |
| `cr5_moveit/config/gazebo_controllers.yaml` | Gazebo controller-manager config added for simulation |
| `cr5_moveit/config/gazebo_moveit_controllers.yaml` | MoveIt-to-Gazebo controller mapping added for simulation |

## Robot Model Facts

Confirmed from the URDF/SRDF/config:

| Item | Value |
| --- | --- |
| MoveIt group | `cr5_arm` |
| Actuated joints | `joint1` through `joint6` |
| Home state | all six joints at `0` |
| End/wrist link | `Link6` |
| Base chain | `dummy_link -> base_link -> Link1 ... Link6` |
| SRDF virtual joint | fixed `world -> dummy_link` |

No `tool0`, `flange`, or named `end_effector` link was found in the inspected CR5 MoveIt path.

## Why RViz Worked

RViz displays the robot from URDF, TF, and joint states. It does not simulate gravity, collision, dynamics, or actuator controllers.

That means the CR5 could appear correct in RViz even while Gazebo failed physically.

## Why Gazebo Failed Originally

Gazebo is physics-based. The original simulation path lacked a complete powered simulation setup:

- several actuated joints used zero effort/velocity limits in the URDF,
- transmissions were missing from the CR5 URDF path used by Gazebo,
- `gazebo_ros_control` was missing or not wired into the active model,
- `controller_spawner` launched with empty args,
- MoveIt expected a `FollowJointTrajectory` action that did not exist,
- the base needed a simulation-safe fixed world anchor.

Gravity-off, static-model, or pose-reset hacks were rejected as the real fix because they do not represent a powered, bolted-down robot.

