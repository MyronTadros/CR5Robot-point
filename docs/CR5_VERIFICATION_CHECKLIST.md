# CR5 Verification Checklist

Use this checklist after setup changes, Lightning restarts, Docker rebuilds, or camera debugging.

## 1. Host Sanity Check

Run on the Lightning host:

```bash
pwd
ls -lah
which start-cr5-desktop
which run-cr5-rviz
which run-cr5-moveit
which run-cr5-gazebo
which run-cr5-camera-web
```

Expected:

- current workspace is `/teamspace/studios/this_studio`
- helper commands resolve under `~/.local/bin`
- `cr5_ws/src/CR5_ROS` exists

## 2. Docker Sanity Check

Run on the Lightning host:

```bash
docker ps
docker ps -a
docker images | grep cr5
```

Expected:

- image `cr5-ros-melodic-turbovnc:local` exists
- container `cr5ros` exists or can be created by `cr5-ensure-container`

Start or ensure the container:

```bash
cr5-ensure-container
docker ps
```

## 3. Desktop Check

Run:

```bash
start-cr5-desktop
```

Expected log signs:

- TurboVNC listens on `5901`
- websockify/noVNC listens on `6080`
- no fatal X server error appears

From Windows, forward port `5901` and connect:

```text
localhost::5901
```

Expected visual result:

- black Fluxbox desktop
- xterm window

Harmless warnings include missing Fluxbox session keys, font warnings, and missing `xmessage`.

## 4. RViz Display Check

With the desktop running:

```bash
run-cr5-rviz
```

Expected:

- RViz appears in TurboVNC
- CR5 model loads
- no package-not-found errors for `dobot_description`

Read-only package check:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find dobot_description'
```

## 5. MoveIt Check

With the desktop running:

```bash
run-cr5-moveit
```

Expected:

- RViz appears
- MoveIt MotionPlanning panel loads
- CR5 planning scene loads
- no package-not-found errors for `dobot_moveit`

Read-only package check:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find dobot_moveit'
```

## 6. Gazebo Check

With the desktop running:

```bash
run-cr5-gazebo
```

Expected:

- Gazebo Classic opens
- RViz may open as part of the launch
- robot model loads in simulation
- no package-not-found errors for `cr5_moveit`

Read-only package check:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find cr5_moveit'
```

## 7. Camera Topic Check

After Gazebo is running and fully loaded:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

Expected topics:

```text
/wrist_rgbd/rgb/image_raw
/wrist_rgbd/rgb/camera_info
/wrist_rgbd/depth/image_raw
/wrist_rgbd/depth/camera_info
/wrist_rgbd/depth/points
```

If the list is empty, check the URDF camera block:

```bash
grep -n "wrist_rgbd" /teamspace/studios/this_studio/cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot.urdf
```

## 8. Camera Viewing Check

For GUI image viewing:

```bash
run-cr5-camera-rqt
```

For browser streaming:

```bash
run-cr5-camera-web
```

Then forward port `8080` and open:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw
```

Depth stream:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/depth/image_raw
```

## 9. Recording Results

For project demos, capture evidence in this order:

1. TurboVNC desktop connected through `localhost::5901`
2. RViz with CR5 model
3. MoveIt planning panel with a planned trajectory
4. Gazebo Classic with CR5 loaded
5. `rostopic list | grep wrist_rgbd`
6. RGB camera stream in browser or `rqt_image_view`
