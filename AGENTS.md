# AGENTS.md

Guidance for coding agents working in this workspace.

## Project Identity

This is a Dobot CR5 student robotics project on Lightning AI, accessed through VS Code Remote-SSH from Windows.

The working environment is Docker-based:

- host workspace: `/teamspace/studios/this_studio`
- ROS workspace: `/teamspace/studios/this_studio/cr5_ws`
- CR5 repo: `/teamspace/studios/this_studio/cr5_ws/src/CR5_ROS`
- Docker image: `cr5-ros-melodic-turbovnc:local`
- Docker container: `cr5ros`
- GUI display: TurboVNC on `DISPLAY=:1`
- ROS stack inside container: Ubuntu 18.04, ROS Melodic, Gazebo Classic 9, MoveIt 1, RViz
- robot type: `DOBOT_TYPE=cr5`

Keep this compatibility stack unless the user explicitly asks for a migration.

Do not migrate to ROS 2, Ubuntu 22.04 native ROS, ROS Noetic, Ignition/Gazebo Sim, or a newer Gazebo by default.

## Current Project Goal

Implement a wrist-camera-based "point at colored boxes" demo.

The intended user commands are:

- `Move above red.`
- `Move above yellow.`
- `Move above green.`
- `Return home.`

The robot should:

1. move to an observation pose,
2. use its wrist RGB-D camera to detect red, yellow, or green boxes,
3. estimate the requested box position in 3D,
4. transform the point into the robot base frame with TF,
5. use MoveIt to move safely above the requested box,
6. avoid touching or gripping the box.

## Simulation And Geometry Assumptions

Use the Gazebo ground plane as the tabletop surface. This matches the real plan where the CR5 base and colored boxes are on the same physical table/surface.

Do not add a high table initially unless the user explicitly requests it.

Coordinate convention:

- table/surface plane is `z = 0`
- CR5 base is mounted at `z = 0`
- colored cubes sit on `z = 0`
- cube center `z = cube_size / 2`

Initial safety target:

- move the tool/camera at least `0.25 m` above the detected box
- do not descend to touch the box
- do not implement gripping

## Perception Constraints

Do not use:

- ML models
- YOLO
- neural-network classifiers
- GPU perception

Use:

- lightweight OpenCV HSV color thresholding
- RGB-D depth images
- `CameraInfo` intrinsics
- TF transforms from camera frame to robot base frame
- MoveIt for robot motion

Always move to an observation pose before detection because the camera is wrist-mounted.

Known camera topic family:

```text
/wrist_rgbd/rgb/image_raw
/wrist_rgbd/rgb/camera_info
/wrist_rgbd/depth/image_raw
/wrist_rgbd/depth/camera_info
/wrist_rgbd/depth/points
```

Known camera frame/plugin identifiers in the CR5 URDF include:

```text
wrist_rgbd_camera_link
wrist_rgbd_camera_joint
wrist_rgbd_camera
wrist_rgbd_camera_controller
```

## Code Organization Preference

Do not modify the existing `CR5_ROS` repository unless necessary.

Prefer creating a new ROS package:

```text
/teamspace/studios/this_studio/cr5_ws/src/cr5_color_pointing
```

Use this package for the colored-box demo nodes, launch files, config, and documentation.

If a change to `CR5_ROS` is necessary, explain the reason before editing and keep the change small and reversible.

## Required Inspection Before Changes

Start with read-only inspection. Prefer commands like:

```bash
pwd
ls -lah
docker ps
docker ps -a
ls -lah /teamspace/studios/this_studio/cr5_ws/src
grep -R -n "wrist_rgbd" /teamspace/studios/this_studio/cr5_ws/src/CR5_ROS/dobot_description/urdf
find /teamspace/studios/this_studio/cr5_ws/src/CR5_ROS -path '*/launch/*' -type f
```

Inspect relevant launch files before modifying or depending on them.

Useful container command pattern:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && COMMAND_HERE'
```

Examples:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find dobot_description'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rospack find cr5_moveit'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list'
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

## Useful Host Commands

These helpers are expected in `~/.local/bin`:

```bash
start-cr5-desktop
run-cr5-rviz
run-cr5-moveit
run-cr5-gazebo
cr5-shell
run-cr5-camera-web
run-cr5-camera-rqt
cr5-ensure-container
```

Normal GUI flow:

1. run `start-cr5-desktop`
2. forward port `5901`
3. connect TurboVNC Viewer from Windows to `localhost::5901`
4. launch RViz, MoveIt, or Gazebo from another terminal

Useful ports:

- `5901`: TurboVNC native viewer
- `6080`: noVNC browser fallback
- `8080`: `web_video_server` camera stream

Do not expose VNC publicly.

## Testing And Build Expectations

After ROS code or package changes, rebuild with:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && cd /root/cr5_ws && catkin_make -DCMAKE_BUILD_TYPE=Release'
```

For runtime checks, use the existing Docker/container environment rather than installing unrelated host packages.

Verify camera topics only after Gazebo is running and fully loaded:

```bash
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rostopic list | grep wrist_rgbd'
```

## Safety Rules

Do not:

- delete Docker images, containers, or workspaces
- run `docker system prune -a`
- run destructive commands such as `rm -rf` on major directories
- edit `.lightning_studio/`
- expose VNC publicly
- commit secrets
- touch OpenAI/Codex auth files
- install unrelated packages with `sudo`

Ask before major architecture changes.

Prefer small, reversible changes. Explain the file path and reason before editing.

## Documentation Pointers

Workspace docs:

- `README.md`
- `docs/README.md`
- `docs/00_PROJECT_OVERVIEW.md`
- `docs/01_LIGHTNING_DOCKER_ENVIRONMENT.md`
- `docs/02_ORIGINAL_CR5_REPO_ARCHITECTURE.md`
- `docs/03_SETUP_HISTORY_AND_TROUBLESHOOTING.md`
- `docs/04_GAZEBO_CONTROL_FIX.md`
- `docs/05_WRIST_CAMERA_AND_PERCEPTION.md`
- `docs/06_COLOR_POINTING_PACKAGE.md`
- `docs/07_OPERATION_GUIDE.md`
- `docs/08_SIM_TO_REAL_TRANSFER_PLAN.md`
- `docs/09_FUTURE_WORK_AND_ROADMAP.md`
- `docs/10_DECISIONS_LOG.md`
- `docs/11_CHANGELOG.md`
- `docs/12_CURRENT_STATUS.md`
- `docs/13_DOCUMENTATION_MAINTENANCE.md`
- `docs/CR5_LIGHTNING_WORKFLOW.md`
- `docs/CR5_VERIFICATION_CHECKLIST.md`
- `docs/CR5_CAMERA.md`
- `docs/CR5_TROUBLESHOOTING.md`
- `docs/CR5_MAINTENANCE.md`

Use these before rediscovering workflow details.

## Documentation Maintenance Rule

For every future Codex session:

1. Update relevant docs when code/config/launch/URDF/script behavior changes.
2. Update `docs/11_CHANGELOG.md` for meaningful changes.
3. Update `docs/12_CURRENT_STATUS.md` after tests.
4. Update `docs/10_DECISIONS_LOG.md` when a design decision changes.
5. If a new topic appears, create a new `docs/*.md` file and add it to `docs/README.md`.
6. Separate confirmed facts from assumptions and future plans.
7. Do not document unverified claims as facts.
8. Mark outdated legacy behavior clearly.
