# CR5 Troubleshooting

Use read-only checks first. Preserve the working Docker image, container, and workspace unless a rebuild is deliberately needed.

## Helper Command Not Found

Run:

```bash
source ~/.bashrc
echo "$PATH"
ls -lah ~/.local/bin
```

Expected:

```text
~/.local/bin
```

appears near the front of `PATH`.

## Container Is Not Running

Run:

```bash
docker ps
docker ps -a
cr5-ensure-container
docker ps
```

Expected:

```text
cr5ros
```

appears in the running container list.

## Desktop Does Not Appear

Start the desktop:

```bash
start-cr5-desktop
```

Check ports and processes:

```bash
docker logs cr5ros --tail 100
docker exec -it cr5ros bash -lc 'ps aux | grep Xvnc'
docker exec -it cr5ros bash -lc 'netstat -tulpn | grep 5901'
```

Expected:

- `Xvnc` is running for display `:1`
- port `5901` is listening
- port `6080` is listening for noVNC/websockify

Connect from Windows through forwarded port `5901`:

```text
localhost::5901
```

## Harmless VNC Warnings

These are usually harmless if the desktop appears:

```text
Failed to read: session...
Setting default value
xterm: cannot load font...
xmessage: not found
```

The desktop is intentionally minimal. A black Fluxbox desktop with an xterm is normal.

## RViz Or Gazebo Does Not Open

Confirm the desktop is running first. Then check the display environment:

```bash
docker exec -it cr5ros bash -lc 'echo $DISPLAY'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && echo $DISPLAY'
```

Expected:

```text
:1
```

Check OpenGL software rendering:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && glxinfo | head'
```

Expected:

- command runs without failing
- rendering is compatible with the VNC display

## ROS Package Not Found

Check that the workspace setup file exists:

```bash
docker exec -it cr5ros bash -lc 'ls -lah /root/cr5_ws/devel/setup.bash'
```

Check package paths:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find dobot_description'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find dobot_moveit'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find cr5_moveit'
```

If packages are missing, rebuild the catkin workspace only after confirming the source tree is present:

```bash
docker exec -it cr5ros bash -lc 'source /opt/ros/melodic/setup.bash && cd /root/cr5_ws && catkin_make -DCMAKE_BUILD_TYPE=Release'
```

## Camera Topics Missing

Gazebo must be running before camera topics exist.

Check:

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

If absent, inspect the URDF camera block:

```bash
grep -n "wrist_rgbd" /teamspace/studios/this_studio/cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot.urdf
```

Then inspect Gazebo output for plugin errors involving:

```text
libgazebo_ros_openni_kinect.so
```

## Camera Web Stream Does Not Load

Confirm the server is running:

```bash
run-cr5-camera-web
```

Forward port `8080`, then open:

```text
http://localhost:8080/stream?topic=/wrist_rgbd/rgb/image_raw
```

If the browser says the topic is unavailable, confirm Gazebo is running and the topic exists:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

## Keep Changes Small

Preferred debugging sequence:

1. read logs
2. inspect helper scripts
3. inspect launch files and URDF
4. run direct ROS commands inside the container
5. rebuild catkin only if source/config changes require it
6. rebuild Docker only if system dependencies or container scripts must change

Avoid deleting the Docker image, container, or workspace unless that is explicitly approved.
