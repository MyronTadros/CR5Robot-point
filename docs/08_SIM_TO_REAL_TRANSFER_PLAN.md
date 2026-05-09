# Sim-To-Real Transfer Plan

## Transfer Goal

The demo should move from Gazebo to a real CR5 setup where:

- the robot base is mounted on the same physical surface as the boxes,
- colored cubes sit on that surface,
- the wrist camera observes the cubes,
- the arm moves above the selected cube without contact.

## Keep The Geometry Simple

Simulation convention:

| Item | Sim convention |
| --- | --- |
| Surface | Gazebo ground plane |
| Surface height | `z = 0` |
| Robot base | fixed at `z = 0` |
| Box bottom | `z = 0` |
| Box center | `cube_size / 2` |

Real-world convention should match this as closely as possible:

- define the robot base frame consistently,
- measure the table/surface plane relative to the base,
- place boxes at known approximate positions for early tests.

## Why Ground Plane As Tabletop

Using Gazebo ground plane avoids adding an artificial raised table model and keeps coordinate assumptions transparent.

This matches the intended real setup where the CR5 base and boxes are on the same physical surface.

## Perception Transfer

Keep perception simple:

- tune HSV thresholds with real lighting,
- use RGB-D depth for distance,
- use `CameraInfo` intrinsics,
- transform camera points into the robot base/planning frame,
- reject detections outside a plausible tabletop range.

Do not introduce ML until the classical pipeline is proven insufficient.

## Motion Transfer

Keep motion conservative:

- always move to an observation pose before detection,
- keep at least `0.25 m` clearance above the detected box initially,
- use low velocity/acceleration scaling,
- do not grip,
- do not descend to contact,
- add workspace bounds and collision objects before real robot motion.

## Simulation Items That Must Not Transfer Blindly

| Simulation item | Real hardware caution |
| --- | --- |
| Gazebo PID gains | Not real robot control gains |
| `SetModelConfiguration` fallback | Simulation-only, should not exist in real control path |
| Simulated box pose fallback | Debug/demo fallback only |
| Gazebo `world_fixed` anchor | Conceptual equivalent is physical mounting, not a robot command |
| HSV thresholds | Must be tuned for real camera lighting |

## Before Real Hardware

Needs verification before any real robot execution:

- correct CR5 driver/bringup path,
- emergency stop and safe workspace,
- measured camera extrinsics from `Link6` or tool frame,
- calibrated camera intrinsics if not provided by the driver,
- real TF tree from camera to robot base,
- collision scene includes table/surface and boxes,
- dry-run plans reviewed in RViz,
- low-speed first motion above empty surface.

## Future Real-Hardware Command Policy

The user-facing commands may remain:

```text
Move above red.
Move above yellow.
Move above green.
Return home.
```

But the execution backend must switch from simulation helpers to real robot control only after explicit approval.

