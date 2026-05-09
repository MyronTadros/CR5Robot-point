# CR5 Maintenance And Safety Notes

This environment is already working. Prefer small, reversible changes and preserve the compatibility stack.

## Do Not Touch Without Explicit Approval

Avoid editing or deleting:

```text
/teamspace/studios/this_studio/.lightning_studio
Docker image cr5-ros-melodic-turbovnc:local
Docker container cr5ros
/teamspace/studios/this_studio/cr5_ws
OpenAI/Codex auth files
```

Avoid destructive commands such as:

```bash
rm -rf
docker system prune -a
git reset --hard
```

unless the action is explicitly approved.

## Preferred Change Policy

For this project:

- keep Ubuntu 18.04 + ROS Melodic + Gazebo Classic 9
- keep Docker as the reproducible boundary
- keep using `catkin_make`
- keep `DOBOT_TYPE=cr5`
- prefer helper-script polish over architecture changes
- document any manual workaround that makes the environment work

Before editing a file, state:

- the file path
- why it needs to change
- whether the change affects setup, runtime helpers, ROS config, or documentation only

## Rebuild Levels

Use the smallest rebuild that matches the change.

Documentation-only change:

```text
No rebuild needed.
```

URDF, launch, or ROS package config change:

```bash
docker exec -it cr5ros bash -lc 'source /opt/ros/melodic/setup.bash && cd /root/cr5_ws && catkin_make -DCMAKE_BUILD_TYPE=Release'
```

Dockerfile or system dependency change:

```bash
/teamspace/studios/this_studio/setup_cr5_lightning.sh
```

Only rebuild Docker when necessary. The working image is valuable project infrastructure.

## Stable Demo Routine

For a project demo or recording:

1. Start the Lightning machine and connect with VS Code Remote-SSH.
2. Open `/teamspace/studios/this_studio`.
3. Start the desktop with `start-cr5-desktop`.
4. Connect TurboVNC Viewer to `localhost::5901`.
5. Launch RViz with `run-cr5-rviz`.
6. Launch MoveIt with `run-cr5-moveit`.
7. Launch Gazebo with `run-cr5-gazebo`.
8. Start camera streaming with `run-cr5-camera-web`.
9. Show the RGB stream at `/stream?topic=/wrist_rgbd/rgb/image_raw`.

For the cleanest recording, close one major GUI demo before starting the next unless the demo specifically needs multiple tools running.

## Known Setup Fixes

The current setup script already includes fixes for:

- installing ROS Python helper packages after adding the ROS Melodic apt repository
- avoiding Ubuntu/ROS Python package conflicts
- replacing a corrupted shell script with a clean setup script
- installing TurboVNC from the TurboVNC apt repository
- avoiding `set -u` while sourcing ROS setup files
- starting TurboVNC with `-SecurityTypes None` and a direct Fluxbox/xterm startup file

These details matter if the setup script is refactored later.
