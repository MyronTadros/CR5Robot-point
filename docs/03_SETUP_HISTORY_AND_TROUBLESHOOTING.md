# Setup History And Troubleshooting

## Setup History

This section records the major setup problems and fixes that produced the current environment.

| Problem | Symptom | Fix |
| --- | --- | --- |
| ROS packages installed too early | Ubuntu 18.04 could not locate `python-catkin-tools` / `python-vcstool` before ROS apt repo was added | Removed those from the early Ubuntu install stage |
| Python ROS helper package conflicts | `dpkg` conflicts with `python-catkin-pkg-modules`, `python-rospkg-modules`, `python-rosdistro-modules` | Avoided installing Ubuntu-provided ROS Python helper packages early; let ROS Melodic packages provide the matching versions |
| Corrupted setup script | `syntax error: unexpected end of file` | Replaced the script with a clean version |
| TurboVNC download URL failed | SourceForge `.deb` URL returned 404 | Installed TurboVNC from the TurboVNC apt repository |
| ROS setup with strict shell mode | `ROS_DISTRO: unbound variable` when sourcing ROS setup under `set -u` | Catkin build shell uses `set -Eeo pipefail` before sourcing `/opt/ros/melodic/setup.bash` |
| TurboVNC startup failed | `Unrecognized option: no`; missing desktop session files | Container desktop script now uses `-SecurityTypes None`, `-xstartup`, Fluxbox, and xterm directly |
| Minimal GUI looked empty | Black Fluxbox desktop with xterm only | Documented as expected; robotics visuals appear only after RViz/MoveIt/Gazebo launch |

## Harmless Warnings

These are usually harmless if the desktop and tools appear:

```text
Failed to read: session...
Setting default value
xterm: cannot load font...
xmessage: not found
the rosdep view is empty: call 'sudo rosdep init' and 'rosdep update'
Kinematics solver doesn't support #attempts anymore
ALSA/no audio warnings
Ignition Fuel SSL warnings
```

Document new warnings when they block actual behavior.

## Read-Only First Checks

Start debugging with read-only commands:

```bash
pwd
ls -lah
docker ps
docker ps -a
which start-cr5-desktop
which run-cr5-rviz
which run-cr5-moveit
which run-cr5-gazebo
ls -lah /teamspace/studios/this_studio/cr5_ws/src
```

Check package visibility:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find dobot_description'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find cr5_moveit'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find cr5_color_pointing'
```

## Desktop Troubleshooting

Start:

```bash
start-cr5-desktop
```

Expected:

- TurboVNC listens on `5901`,
- websockify/noVNC listens on `6080`,
- Windows TurboVNC Viewer connects to `localhost::5901`,
- desktop is a black Fluxbox session with xterm.

Check display:

```bash
docker exec -it cr5ros bash -lc 'echo $DISPLAY'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && echo $DISPLAY'
```

Expected:

```text
:1
```

## Gazebo Controller Troubleshooting

After `run-cr5-gazebo`:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice list | grep controller_manager'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep follow_joint_trajectory'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic echo -n 1 /joint_states'
```

Expected controllers:

```text
joint_state_controller: running
cr5_joint_trajectory_controller: running
```

Expected action topic family:

```text
/cr5_joint_trajectory_controller/follow_joint_trajectory/goal
/cr5_joint_trajectory_controller/follow_joint_trajectory/result
/cr5_joint_trajectory_controller/follow_joint_trajectory/status
```

## Camera Troubleshooting

Gazebo must be running before camera topics exist.

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

Expected:

```text
/wrist_rgbd/rgb/image_raw
/wrist_rgbd/rgb/camera_info
/wrist_rgbd/depth/image_raw
/wrist_rgbd/depth/camera_info
/wrist_rgbd/depth/points
```

## Do Not Use These As Fixes

Do not fix physics problems by:

- turning gravity off,
- making the entire robot model static,
- repeatedly teleporting the model as the main behavior,
- deleting/recreating the Docker image/container without approval,
- running `docker system prune -a`.

