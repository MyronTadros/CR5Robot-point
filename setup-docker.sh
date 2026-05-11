#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE_NAME="cr5-ros-melodic-turbovnc:local"
CONTAINER_NAME="cr5ros"
STUDIO_DIR="/home/mo-sameh1/Documents/GitHub/CR5Robot-point"
WS_DIR="${STUDIO_DIR}/cr5_ws"
BUILD_DIR="${STUDIO_DIR}/cr5_docker_build"
BIN_DIR="${HOME}/.local/bin"

FORCE_REBUILD=0
IMAGE_REBUILT=0
if [ "${1:-}" = "--rebuild" ]; then
  FORCE_REBUILD=1
elif [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<EOF
Usage: ./setup-docker.sh [--rebuild]

Restore only the Docker runtime for the CR5 project using the existing files.
This script does not clone repositories, reset source files, or patch URDF/code.
EOF
  exit 0
elif [ -n "${1:-}" ]; then
  echo "[CR5 docker setup ERROR] Unknown argument: $1" >&2
  exit 2
fi

log() {
  echo
  echo "[CR5 docker setup] $*"
}

die() {
  echo
  echo "[CR5 docker setup ERROR] $*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"
}

image_exists() {
  docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1
}

container_exists() {
  docker ps -a --format "{{.Names}}" | grep -qx "${CONTAINER_NAME}"
}

container_running() {
  docker ps --format "{{.Names}}" | grep -qx "${CONTAINER_NAME}"
}

log "Checking Docker and existing project files"
need_cmd docker
docker info >/dev/null 2>&1 || die "Docker is installed but not running or not accessible from this user."

[ -d "${WS_DIR}/src/CR5_ROS" ] || die "Missing existing CR5_ROS checkout: ${WS_DIR}/src/CR5_ROS"
[ -f "${BUILD_DIR}/Dockerfile" ] || die "Missing Dockerfile: ${BUILD_DIR}/Dockerfile"
mkdir -p "${BIN_DIR}"

if [ "${FORCE_REBUILD}" -eq 1 ] || ! image_exists; then
  log "Building Docker image ${IMAGE_NAME} from existing ${BUILD_DIR}/Dockerfile"
  docker build -t "${IMAGE_NAME}" "${BUILD_DIR}"
  IMAGE_REBUILT=1
else
  log "Docker image ${IMAGE_NAME} already exists; skipping image build"
fi

log "Building current mounted catkin workspace"
docker run --rm \
  --shm-size=2g \
  -v "${WS_DIR}:/root/cr5_ws" \
  "${IMAGE_NAME}" \
  bash -lc '
    set -Eeo pipefail
    source /opt/ros/melodic/setup.bash
    cd /root/cr5_ws
    export DOBOT_TYPE=cr5
    catkin_make -DCMAKE_BUILD_TYPE=Release
  '

log "Writing helper commands"

cat > "${BIN_DIR}/cr5-ensure-container" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE_NAME="${IMAGE_NAME}"
CONTAINER_NAME="${CONTAINER_NAME}"
WS_DIR="${WS_DIR}"

if ! docker ps --format "{{.Names}}" | grep -qx "\${CONTAINER_NAME}"; then
  if docker ps -a --format "{{.Names}}" | grep -qx "\${CONTAINER_NAME}"; then
    docker rm -f "\${CONTAINER_NAME}" >/dev/null 2>&1 || true
  fi

  docker run -d \\
    --name "\${CONTAINER_NAME}" \\
    --shm-size=2g \\
    -p 5901:5901 \\
    -p 6080:6080 \\
    -p 8080:8080 \\
    -v "\${WS_DIR}:/root/cr5_ws" \\
    -e DOBOT_TYPE=cr5 \\
    -e DISPLAY=:1 \\
    -e LIBGL_ALWAYS_SOFTWARE=1 \\
    -e QT_X11_NO_MITSHM=1 \\
    "\${IMAGE_NAME}" \\
    tail -f /dev/null >/dev/null
fi
EOF

cat > "${BIN_DIR}/start-cr5-desktop" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
cr5-ensure-container
docker exec -it cr5ros bash -lc 'container-start-cr5-desktop'
EOF

cat > "${BIN_DIR}/cr5-shell" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
cr5-ensure-container
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && cd /root/cr5_ws && bash'
EOF

cat > "${BIN_DIR}/run-cr5-rviz" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
cr5-ensure-container
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch dobot_description display.launch'
EOF

cat > "${BIN_DIR}/run-cr5-moveit" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
cr5-ensure-container
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch dobot_moveit demo.launch'
EOF

cat > "${BIN_DIR}/run-cr5-gazebo" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
cr5-ensure-container
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && roslaunch cr5_moveit demo_gazebo.launch'
EOF

cat > "${BIN_DIR}/run-cr5-camera-web" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
cr5-ensure-container
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rosrun web_video_server web_video_server'
EOF

cat > "${BIN_DIR}/run-cr5-camera-rqt" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
cr5-ensure-container
docker exec -it cr5ros bash -lc 'source /usr/local/bin/cr5-env && rqt_image_view /wrist_rgbd/rgb/image_raw'
EOF

chmod +x \
  "${BIN_DIR}/cr5-ensure-container" \
  "${BIN_DIR}/start-cr5-desktop" \
  "${BIN_DIR}/cr5-shell" \
  "${BIN_DIR}/run-cr5-rviz" \
  "${BIN_DIR}/run-cr5-moveit" \
  "${BIN_DIR}/run-cr5-gazebo" \
  "${BIN_DIR}/run-cr5-camera-web" \
  "${BIN_DIR}/run-cr5-camera-rqt"

if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "${HOME}/.bashrc" 2>/dev/null; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${HOME}/.bashrc"
fi

export PATH="${HOME}/.local/bin:${PATH}"

log "Ensuring ${CONTAINER_NAME} is running"
if [ "${IMAGE_REBUILT}" -eq 1 ] && container_exists; then
  log "Recreating ${CONTAINER_NAME} so it uses the rebuilt image"
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi
cr5-ensure-container

log "Verifying container ROS workspace"
docker exec "${CONTAINER_NAME}" bash -lc '
  set -Eeo pipefail
  source /usr/local/bin/cr5-env
  rospack find dobot_description >/dev/null
  rospack find cr5_moveit >/dev/null
  rospack find cr5_color_pointing >/dev/null
  rospack find effort_controllers >/dev/null
  rosrun controller_manager spawner --help >/dev/null
'

log "Docker runtime is ready"
docker ps --filter "name=${CONTAINER_NAME}"
docker images "${IMAGE_NAME}"

echo
echo "Now run:"
echo
echo "  source ~/.bashrc"
echo "  start-cr5-desktop"
echo
