# Wrist Camera And Perception

## Camera Status

A simulated wrist RGB-D camera is present in the CR5 URDF path.

Known identifiers:

```text
wrist_rgbd_camera_link
wrist_rgbd_camera_joint
wrist_rgbd_camera
wrist_rgbd_camera_controller
```

Gazebo plugin:

```text
libgazebo_ros_openni_kinect.so
```

The camera is fixed to:

```text
parent: Link6
child:  wrist_rgbd_camera_link
```

## Expected Topics

After Gazebo has fully loaded, expected topics are:

```text
/wrist_rgbd/rgb/image_raw
/wrist_rgbd/rgb/camera_info
/wrist_rgbd/depth/image_raw
/wrist_rgbd/depth/camera_info
/wrist_rgbd/depth/points
```

Check:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

## View RGB And Depth

RGB through rqt:

```bash
run-cr5-camera-rqt
```

Browser stream:

```bash
run-cr5-camera-web
```

Then open:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw
```

Depth stream:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/depth/image_raw
```

## Perception Strategy

Use lightweight classical computer vision:

- OpenCV HSV color thresholding,
- largest contour selection,
- median depth around detected centroid,
- `CameraInfo` projection through `image_geometry`,
- TF transform to the planning/base frame.

Do not use:

- YOLO,
- neural-network classifiers,
- ML model training,
- GPU perception.

## Why HSV Instead Of ML

HSV thresholding is appropriate because the demo objects are simple red/yellow/green cubes in a controlled simulation/teaching setup.

Benefits:

- easy to inspect and tune,
- no dataset collection,
- no training,
- runs on CPU,
- simpler to transfer to first real-hardware experiments.

## Current Color Thresholds

Defined in:

```text
cr5_ws/src/cr5_color_pointing/config/color_thresholds.yaml
```

Default ranges:

| Color | HSV lower | HSV upper |
| --- | --- | --- |
| red range 1 | `[0, 100, 80]` | `[10, 255, 255]` |
| red range 2 | `[170, 100, 80]` | `[180, 255, 255]` |
| yellow | `[20, 100, 80]` | `[35, 255, 255]` |
| green | `[40, 80, 60]` | `[85, 255, 255]` |

Detection params:

| Param | Value |
| --- | --- |
| `min_area` | `200` |
| `morph_kernel` | `5` |
| `depth_window` | `5` |
| `image_timeout` | `5.0` |
| `tf_timeout` | `2.0` |

## Needs Verification

- Confirm wrist topics publish after a clean `run-cr5-gazebo`.
- Confirm RGB image shows the colored boxes after spawning.
- Confirm the observation pose sees all three boxes.
- Confirm the camera optical orientation produces sensible projected 3D points.
- Confirm TF can transform from the camera frame to `dummy_link`.

