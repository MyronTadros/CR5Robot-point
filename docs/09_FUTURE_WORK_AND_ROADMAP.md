# Future Work And Roadmap

## Immediate Next Steps

1. Manually verify Gazebo control visually in TurboVNC.
2. Confirm MoveIt Execute moves the Gazebo robot through `cr5_joint_trajectory_controller`.
3. Rebuild and re-test the `cr5_color_pointing` package after the controller fix.
4. Verify wrist camera topics and image streams.
5. Verify `detect_color_once.py` for red, yellow, and green boxes.

## Color Pointing Hardening

Future package work:

- tune observation pose so all boxes are visible,
- verify camera frame orientation,
- validate depth units and point projection,
- disable or restrict simulation fallbacks once real perception is working,
- add better safety checks for target poses,
- publish debug images/masks for HSV tuning,
- add RViz markers for detected object and target above-object pose.

## Gazebo Simulation Improvements

Potential follow-up work:

- tune PID gains if the arm visibly sags or oscillates,
- add collision objects for boxes to MoveIt planning scene,
- add launch args for initial pose and controller config,
- add a single demo launch that starts Gazebo, boxes, camera stream, and pointing node in a controlled order.

## Documentation Improvements

Future sessions should:

- update status after every validation run,
- include exact command outputs for pass/fail checks,
- mark stale legacy notes clearly,
- add screenshots or short recordings outside git if needed.

## Real Hardware Preparation

Before moving to real hardware:

- decide on the official real robot bringup package/path,
- verify driver command semantics,
- calibrate camera mount,
- add workspace safety limits,
- test planning with no motion execution,
- test slow motion above empty space,
- then test above colored boxes without contact.

## AI Perception Experiments Later

AI/ML perception is intentionally out of scope for the initial demo.

If added later, it should be a separate milestone after:

- HSV pipeline works,
- RGB-D geometry works,
- TF transforms are validated,
- MoveIt execution is stable,
- safety behavior is documented.

