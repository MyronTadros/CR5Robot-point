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
      xfonts-base \
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
wm_pid=$!
xterm &
wait "${wm_pid}"
EOS

chmod +x /root/.vnc/xstartup

/opt/TurboVNC/bin/vncserver -kill :1 >/dev/null 2>&1 || true
pkill -f websockify >/dev/null 2>&1 || true

setsid /opt/TurboVNC/bin/vncserver :1 \
  -geometry 1920x1080 \
  -depth 24 \
  -SecurityTypes None \
  -interface 0.0.0.0 \
  -noautokill \
  -xstartup /root/.vnc/xstartup

setsid websockify --web=/usr/share/novnc/ 6080 localhost:5901 >/tmp/novnc.log 2>&1 &

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
