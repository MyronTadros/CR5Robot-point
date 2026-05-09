# Operation Guide

## Open The Workspace

Use VS Code Remote-SSH from Windows and open:

```text
/teamspace/studios/this_studio
```

If helper commands are missing:

```bash
source ~/.bashrc
```

## Start Desktop

Terminal 1:

```bash
start-cr5-desktop
```

Forward port `5901` and connect Windows TurboVNC Viewer to:

```text
localhost::5901
```

Expected desktop:

```text
black Fluxbox desktop with xterm
```

## RViz Robot Display

Terminal 2:

```bash
run-cr5-rviz
```

Expected:

- RViz opens in TurboVNC,
- CR5 model appears.

## MoveIt Planning Demo

Terminal 2:

```bash
run-cr5-moveit
```

Expected:

- RViz opens,
- MotionPlanning panel loads,
- `cr5_arm` planning is available.

## Gazebo + MoveIt Simulation

Terminal 2:

```bash
run-cr5-gazebo
```

Expected:

- Gazebo Classic opens,
- RViz opens or becomes available from launch,
- robot spawns in a non-colliding pose,
- controllers start,
- physics unpauses with gravity ON.

Controller checks:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep follow_joint_trajectory'
```

## Spawn Colored Boxes

After Gazebo is running:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing spawn_colored_boxes.launch'
```

Default box positions:

| Color | x | y | z |
| --- | ---: | ---: | ---: |
| red | `0.45` | `-0.25` | `0.025` |
| yellow | `0.55` | `0.0` | `0.025` |
| green | `0.45` | `0.25` | `0.025` |

## Camera Checks

List wrist topics:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

Open rqt image viewer:

```bash
run-cr5-camera-rqt
```

Open browser stream:

```bash
run-cr5-camera-web
```

Then browse:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw
```

## Color Pointing

Run detector:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun cr5_color_pointing detect_color_once.py red'
```

Run pointing node:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_color_pointing color_pointing.launch'
```

At `cr5>`:

```text
red
yellow
green
home
quit
```

or:

```text
Move above red.
Move above yellow.
Move above green.
Return home.
```

## Rebuild

After ROS package, launch, config, URDF, or script changes:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && cd /root/cr5_ws && catkin_make -DCMAKE_BUILD_TYPE=Release'
```

Documentation-only changes do not require rebuild.

