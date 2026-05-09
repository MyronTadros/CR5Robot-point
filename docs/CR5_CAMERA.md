# CR5 Wrist RGB-D Camera

The simulated wrist camera is attached to the CR5 URDF:

```text
/teamspace/studios/this_studio/cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot.urdf
```

Camera identifiers:

```text
wrist_rgbd_camera_link
wrist_rgbd_camera_joint
wrist_rgbd_camera
wrist_rgbd_camera_controller
```

The Gazebo plugin is:

```text
libgazebo_ros_openni_kinect.so
```

## Expected Topics

After `run-cr5-gazebo` is running and Gazebo has fully loaded, these topics should exist:

```text
/wrist_rgbd/rgb/image_raw
/wrist_rgbd/rgb/camera_info
/wrist_rgbd/depth/image_raw
/wrist_rgbd/depth/camera_info
/wrist_rgbd/depth/points
```

Check with:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

## View RGB Image

With Gazebo running:

```bash
run-cr5-camera-rqt
```

or inside the container:

```bash
rqt_image_view /wrist_rgbd/rgb/image_raw
```

## View Depth Image

Inside a CR5 shell:

```bash
rqt_image_view /wrist_rgbd/depth/image_raw
```

Depth images may look mostly dark or flat if the camera is looking at empty space or all visible geometry is outside a useful depth range.

## View Browser Stream

With Gazebo running, start:

```bash
run-cr5-camera-web
```

Forward port `8080`, then open:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw
```

Depth stream:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/depth/image_raw
```

## Point Cloud

The expected point cloud topic is:

```text
/wrist_rgbd/depth/points
```

Check that it publishes:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic hz /wrist_rgbd/depth/points'
```

To view the point cloud in RViz:

- add a `PointCloud2` display
- set the topic to `/wrist_rgbd/depth/points`
- set the fixed frame to a valid robot/world frame from the simulation

## If Topics Do Not Appear

First confirm Gazebo is still running. The camera plugin only publishes after the model is spawned in Gazebo.

Check for the camera block:

```bash
grep -n "wrist_rgbd" /teamspace/studios/this_studio/cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot.urdf
```

Check ROS package visibility:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find dobot_description'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find cr5_moveit'
```

Check all topics:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list'
```

If the camera topics still do not exist, inspect Gazebo launch output for plugin load errors involving:

```text
libgazebo_ros_openni_kinect.so
wrist_rgbd_camera_controller
```
