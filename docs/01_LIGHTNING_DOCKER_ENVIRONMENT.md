# Lightning Docker Environment

## Why Lightning AI

Lightning AI is used as the cloud compute/dev machine so the project can run a Linux ROS/Gazebo stack without depending on the Windows host for native ROS support.

Benefits:

- persistent project workspace under `/teamspace/studios/this_studio`
- enough CPU resources for student-scale Gazebo/RViz demos
- VS Code Remote-SSH access from Windows
- ability to keep Docker, ROS Melodic, Gazebo, MoveIt, and VNC tools together

## Why VS Code Remote-SSH

VS Code Remote-SSH gives a normal editor and terminal experience against the Lightning machine while keeping the Windows laptop as the client.

It also supports port forwarding for:

| Port | Purpose |
| --- | --- |
| `5901` | TurboVNC native viewer |
| `6080` | browser noVNC fallback |
| `8080` | `web_video_server` camera stream |

## Windows SSH And GUI Access

Confirmed workflow:

1. connect to Lightning through VS Code Remote-SSH,
2. open `/teamspace/studios/this_studio`,
3. forward required ports in VS Code,
4. connect TurboVNC Viewer from Windows to `localhost::5901`.

Reported project history:

- Direct GUI access from a cloud machine was not practical.
- The solution was to run a minimal VNC desktop in the Docker container and reach it through SSH/VS Code port forwarding.
- VNC must not be exposed publicly.

Needs more detail:

- Exact Windows SSH setup errors are not captured in workspace files. Future docs should record exact Windows-side errors if they happen again.

## Why Docker Ubuntu 18.04

The original CR5 repository is ROS 1/catkin and was treated as a Melodic-era project.

Docker is used to preserve:

- Ubuntu 18.04 package availability,
- ROS Melodic package names,
- Gazebo Classic 9 behavior,
- MoveIt 1 configuration compatibility,
- repeatable helper commands and GUI setup.

Do not install unrelated ROS packages on the Lightning host unless explicitly approved.

## Setup Script

Main setup script:

```text
/teamspace/studios/this_studio/setup_cr5_lightning.sh
```

Docker-only recovery helper:

```text
/teamspace/studios/this_studio/setup-docker.sh
```

Use `setup-docker.sh` when the source workspace still exists but Docker local state was wiped or the `cr5ros` container/image is missing. It rebuilds the Docker image from the existing Dockerfile, rebuilds the mounted catkin workspace, rewrites helper commands, and recreates `cr5ros` if needed. It does not reclone the CR5 repository or reset source files.

It creates or uses:

| Resource | Path/name |
| --- | --- |
| Persistent workspace | `/teamspace/studios/this_studio/cr5_ws` |
| Docker build folder | `/teamspace/studios/this_studio/cr5_docker_build` |
| Helper command folder | `~/.local/bin` |
| CR5 source checkout | `/teamspace/studios/this_studio/cr5_ws/src/CR5_ROS` |
| Docker image | `cr5-ros-melodic-turbovnc:local` |
| Docker container | `cr5ros` |

## Helper Commands

The setup script writes these host commands:

| Command | Purpose |
| --- | --- |
| `cr5-ensure-container` | Create/start the `cr5ros` Docker container if needed |
| `start-cr5-desktop` | Start TurboVNC/noVNC desktop in the container |
| `cr5-shell` | Open a ROS-ready shell inside the container |
| `run-cr5-rviz` | Launch `dobot_description display.launch` |
| `run-cr5-moveit` | Launch `dobot_moveit demo.launch` |
| `run-cr5-gazebo` | Launch `cr5_moveit demo_gazebo.launch` |
| `run-cr5-camera-web` | Start `web_video_server` |
| `run-cr5-camera-rqt` | Start `rqt_image_view` on the wrist RGB topic |

If commands are not found:

```bash
source ~/.bashrc
```

## Container Command Pattern

Use this pattern for ROS commands inside Docker:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && COMMAND_HERE'
```

Examples:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find cr5_moveit'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosservice call /controller_manager/list_controllers'
```

## GUI Environment Variables

| Variable | Value | Reason |
| --- | --- | --- |
| `DOBOT_TYPE` | `cr5` | Selects CR5 in generic launch/config wrappers |
| `DISPLAY` | `:1` | Sends GUI windows to TurboVNC |
| `LIBGL_ALWAYS_SOFTWARE` | `1` | Predictable OpenGL in cloud/container sessions |
| `QT_X11_NO_MITSHM` | `1` | Avoids Qt shared-memory issues with remote X |

## Current Live Docker Note

During the 2026-05-09 repair session, Docker local state was initially empty even though the project source workspace was intact. `setup-docker.sh` restored the image/container, and `start-cr5-desktop` was verified with TurboVNC on `5901` and noVNC on `6080`.

If Docker local state disappears again, run:

```bash
./setup-docker.sh
```

For a normal already-restored session, run:

```bash
source ~/.bashrc
start-cr5-desktop
```
