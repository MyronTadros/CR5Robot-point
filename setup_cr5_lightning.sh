#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE_NAME="cr5-ros-melodic-turbovnc:local"
CONTAINER_NAME="cr5ros"
STUDIO_DIR="/teamspace/studios/this_studio"
WS_DIR="${STUDIO_DIR}/cr5_ws"
BUILD_DIR="${STUDIO_DIR}/cr5_docker_build"
BIN_DIR="${HOME}/.local/bin"

log() {
  echo
  echo "[CR5 setup] $*"
}

die() {
  echo
  echo "[CR5 setup ERROR] $*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"
}

log "Checking Docker"
need_cmd docker
docker info >/dev/null 2>&1 || die "Docker is installed but not running or not accessible from this user."

log "Preparing folders"
mkdir -p "${WS_DIR}/src"
mkdir -p "${BUILD_DIR}"
mkdir -p "${BIN_DIR}"

log "Cloning CR5_ROS repository"
if [ ! -d "${WS_DIR}/src/CR5_ROS/.git" ]; then
  git clone https://github.com/WELLBEINGLWB/CR5_ROS.git "${WS_DIR}/src/CR5_ROS"
else
  echo "Repo already exists at ${WS_DIR}/src/CR5_ROS"
fi

log "Adding simulated wrist RGB-D camera to CR5 URDF if not already present"
python3 - <<'PY'
from pathlib import Path

urdf = Path("/teamspace/studios/this_studio/cr5_ws/src/CR5_ROS/dobot_description/urdf/cr5_robot.urdf")
if not urdf.exists():
    raise SystemExit(f"URDF not found: {urdf}")

s = urdf.read_text()

if "wrist_rgbd_camera_link" in s:
    print("Camera already exists in URDF.")
    raise SystemExit(0)

camera = r'''
  <!-- Wrist-mounted RGB-D camera for Gazebo/ROS viewing -->
  <link name="wrist_rgbd_camera_link">
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="0.04 0.04 0.03"/>
      </geometry>
      <material name="camera_gray">
        <color rgba="0.05 0.05 0.05 1"/>
      </material>
    </visual>

    <collision>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="0.04 0.04 0.03"/>
      </geometry>
    </collision>

    <inertial>
      <mass value="0.05"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="1e-5" ixy="0" ixz="0" iyy="1e-5" iyz="0" izz="1e-5"/>
    </inial>
  </link>

  <joint name="wrist_rgbd_camera_joint" type="fixed">
    <parent link="Link6"/>
    <child link="wrist_rgbd_camera_link"/>
    <origin xyz="0 0 0.08" rpy="0 1.5708 0"/>
  </joint>

  <gazebo reference="wrist_rgbd_camera_link">
    <material>Gazebo/Black</material>

    <sensor type="depth" name="wrist_rgbd_camera">
      <always_on>true</always_on>
      <update_rate>30.0</update_rate>

      <camera name="camera">
        <horizontal_fov>1.047</horizontal_fov>
        <image>
          <width>1280</width>
          <height>720</height>
          <format>R8G8B8</format>
        </image>
        <clip>
          <near>0.05</near>
          <far>5.0</far>
        </clip>
      </camera>

      <plugin name="wrist_rgbd_camera_controller" filename="libgazebo_ros_openni_kinect.so">
        <alwaysOn>true</alwaysOn>
        <updateRate>30.0</updateRate>

        <cameraName>wrist_rgbd</cameraName>
        <frameName>wrist_rgbd_camera_link</frameName>

        <imageTopicName>rgb/image_raw</imageTopicName>
        <cameraInfoTopicName>rgb/camera_info</cameraInfoTopicName>

        <depthImageTopicName>depth/image_raw</depthImageTopicName>
        <depthImageCameraInfoTopicName>depth/camera_info</depthImageCameraInfoTopicName>
        <pointCloudTopicName>depth/points</pointCloudTopicName>

        <pointCloudCutoff>0.05</pointCloudCutoff>
        <pointCloudCutoffMax>5.0</pointCloudCutoffMax>

        <hackBaseline>0.0</hackBaseline>
        <distortionK1>0.0</distortionK1>
        <distortionK2>0.0</distortionK2>
        <distortionK3>0.0</distortionK3>
        <distortionT1>0.0</distortionT1>
        <distortionT2>0.0</distortionT2>
      </plugin>
    </sensor>
  </gazebo>
'''

# Fix typo before writing.
camera = camera.replace("</inial>", "</inertial>")

if "</robot>" not in s:
    raise SystemExit("Could not find closing </robot> tag in URDF.")

s = s.replace("</robot>", camera + "\n</robot>")
urdf.write_text(s)
print("Added camera to URDF.")
PY

log "Writing Dockerfile"
cat > "${BUILD_DIR}/Dockerfile" <<'DOCKERFILE'
FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DOBOT_TYPE=cr5
ENV DISPLAY=:1
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV QT_X11_NO_MITSHM=1

SHELL ["/bin/bash", "-c"]

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      gnupg2 \
      lsb-release \
      git \
      build-essential \
      cmake \
      nano \
      wget \
      sudo \
      software-properties-common \
      fluxbox \
      xterm \
      dbus-x11 \
      mesa-utils \
      libgl1-mesa-glx \
      libgl1-mesa-dri \
      net-tools \
      procps \
      psmisc \
      novnc \
      websockify && \
    add-apt-repository -y universe && \
    add-apt-repository -y multiverse && \
    rm -rf /var/lib/apt/lists/*

RUN echo "deb http://packages.ros.org/ros/ubuntu bionic main" > /etc/apt/sources.list.d/ros-latest.list && \
    curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add -

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ros-melodic-desktop-full \
      ros-melodic-moveit \
      ros-melodic-gazebo-ros-pkgs \
      ros-melodic-gazebo-ros-control \
      ros-melodic-gazebo-plugins \
      ros-melodic-ros-control \
      ros-melodic-ros-controllers \
      ros-melodic-joint-state-controller \
      ros-melodic-joint-trajectory-controller \
      ros-melodic-position-controllers \
      ros-melodic-robot-state-publisher \
      ros-melodic-joint-state-publisher \
      ros-melodic-joint-state-publisher-gui \
      ros-melodic-rviz \
      ros-melodic-xacro \
      ros-melodic-tf \
      ros-melodic-image-transport \
      ros-melodic-camera-info-manager \
      ros-melodic-cv-bridge \
      ros-melodic-image-view \
      ros-melodic-rqt-image-view \
      ros-melodic-rqt-graph \
      ros-melodic-web-video-server && \
    rm -rf /var/lib/apt/lists/*

RUN wget -q -O- https://packagecloud.io/dcommander/turbovnc/gpgkey | \
      gpg --dearmor > /etc/apt/trusted.gpg.d/TurboVNC.gpg && \
    wget -O /etc/apt/sources.list.d/TurboVNC.list \
      https://raw.githubusercontent.com/TurboVNC/repo/main/TurboVNC.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends turbovnc && \
    rm -rf /var/lib/apt/lists/*

RUN cat > /usr/local/bin/cr5-env <<'EOF'
#!/usr/bin/env bash
source /opt/ros/melodic/setup.bash
if [ -f /root/cr5_ws/devel/setup.bash ]; then
  source /root/cr5_ws/devel/setup.bash
fi
export DOBOT_TYPE=cr5
export DISPLAY=:1
export LIBGL_ALWAYS_SOFTWARE=1
export QT_X11_NO_MITSHM=1
EOF

RUN chmod +x /usr/local/bin/cr5-env

RUN cat > /usr/local/bin/container-start-cr5-desktop <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

export USER=root
export HOME=/root
export DISPLAY=:1
export DOBOT_TYPE=cr5
export LIBGL_ALWAYS_SOFTWARE=1
export QT_X11_NO_MITSHM=1

mkdir -p /root/.vnc

cat > /root/.vnc/xstartup <<'EOS'
#!/usr/bin/env bash
export DISPLAY=:1
export DOBOT_TYPE=cr5
export LIBGL_ALWAYS_SOFTWARE=1
export QT_X11_NO_MITSHM=1
xrdb $HOME/.Xresources 2>/dev/null || true
fluxbox &
xterm &
EOS

chmod +x /root/.vnc/xstartup

/opt/TurboVNC/bin/vncserver -kill :1 >/dev/null 2>&1 || true
pkill -f websockify >/dev/null 2>&1 || true

/opt/TurboVNC/bin/vncserver :1 \
  -geometry 1920x1080 \
  -depth 24 \
  -SecurityTypes None \
  -localhost no

websockify --web=/usr/share/novnc/ 6080 localhost:5901 >/tmp/novnc.log 2>&1 &

echo
echo "CR5 desktop is running."
echo "TurboVNC port: 5901"
echo "Browser noVNC port: 6080"
echo
echo "Keep this terminal running."
echo

tail -F /root/.vnc/*.log /tmp/novnc.log
EOF

RUN chmod +x /usr/local/bin/container-start-cr5-desktop

RUN echo "source /opt/ros/melodic/setup.bash" >> /root/.bashrc && \
    echo "source /root/cr5_ws/devel/setup.bash 2>/dev/null || true" >> /root/.bashrc && \
    echo "export DOBOT_TYPE=cr5" >> /root/.bashrc && \
    echo "export DISPLAY=:1" >> /root/.bashrc && \
    echo "export LIBGL_ALWAYS_SOFTWARE=1" >> /root/.bashrc && \
    echo "export QT_X11_NO_MITSHM=1" >> /root/.bashrc

WORKDIR /root/cr5_ws
CMD ["bash"]
DOCKERFILE

log "Building Docker image. This is the long step."
docker build -t "${IMAGE_NAME}" "${BUILD_DIR}"

log "Building CR5 catkin workspace inside container"
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

chmod +x "${BIN_DIR}/cr5-ensure-container"
chmod +x "${BIN_DIR}/start-cr5-desktop"
chmod +x "${BIN_DIR}/cr5-shell"
chmod +x "${BIN_DIR}/run-cr5-rviz"
chmod +x "${BIN_DIR}/run-cr5-moveit"
chmod +x "${BIN_DIR}/run-cr5-gazebo"
chmod +x "${BIN_DIR}/run-cr5-camera-web"
chmod +x "${BIN_DIR}/run-cr5-camera-rqt"

if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "${HOME}/.bashrc" 2>/dev/null; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${HOME}/.bashrc"
fi

export PATH="${HOME}/.local/bin:${PATH}"

log "Setup complete."

echo
echo "Now run:"
echo
echo "  source ~/.bashrc"
echo "  start-cr5-desktop"
echo
echo "Then open another VS Code terminal and run:"
echo
echo "  run-cr5-rviz"
echo "  run-cr5-moveit"
echo "  run-cr5-gazebo"
echo
echo "Lightning ports to open:"
echo
echo "  5901  TurboVNC"
echo "  6080  browser noVNC"
echo "  8080  camera web stream"
echo