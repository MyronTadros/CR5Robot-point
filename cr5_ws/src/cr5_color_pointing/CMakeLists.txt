cmake_minimum_required(VERSION 3.0.2)
project(cr5_color_pointing)

find_package(catkin REQUIRED COMPONENTS
  rospy
  sensor_msgs
  geometry_msgs
  std_msgs
  cv_bridge
  image_geometry
  tf2_ros
  tf2_geometry_msgs
  moveit_commander
  gazebo_ros
  gazebo_msgs
)

catkin_python_setup()

catkin_package()

catkin_install_python(PROGRAMS
  scripts/color_pointing_node.py
  scripts/detect_color_once.py
  scripts/auto_enable_cr5.py
  scripts/execute_real_trajectory.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY
  launch
  config
  models
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
