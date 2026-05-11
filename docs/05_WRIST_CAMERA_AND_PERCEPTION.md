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
origin: xyz="0 -0.055 0" rpy="1.5708 -1.5708 0"
```

The merged camera geometry approximates a VX500-style wrist camera mounted at the CR5 end flange. The depth sensor is attached to `wrist_rgbd_camera_link`, while the Gazebo plugin publishes `frameName=wrist_rgbd_camera_optical_frame`. The optical frame uses the ROS camera convention: z forward, x right, y down.

The optical-frame fixed joint currently uses:

```text
wrist_rgbd_camera_link -> wrist_rgbd_camera_optical_frame
origin: xyz="0 0 0" rpy="-1.5708 0 -1.5708"
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

## Latest Verified Status

- Wrist topics publish after `run-cr5-gazebo`.
- From `scan`, the RGB image contains red, yellow, and green boxes.
- Latest image sample after scan: red `2418` broad-mask pixels, yellow `1806`, green `2463`.
- Depth from scan is plausible for the ground-plane boxes, with center depth around `0.706 m`.
- `detect_color_once.py` detects all three colors and transforms them to tabletop-height points in `dummy_link`.
- The launched command node logs transformed tabletop-height points in `world`.
- TF from `world`/`dummy_link` to `wrist_rgbd_camera_optical_frame` is available during runtime after robot state publication starts.
