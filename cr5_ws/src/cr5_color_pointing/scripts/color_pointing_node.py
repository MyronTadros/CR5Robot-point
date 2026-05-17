#!/usr/bin/env python
from __future__ import print_function

import re
import select
import sys
import threading
import time
import json

import actionlib
from actionlib_msgs.msg import GoalStatus
from control_msgs.msg import FollowJointTrajectoryAction, FollowJointTrajectoryGoal
from gazebo_msgs.srv import GetModelState, SetModelConfiguration
import moveit_commander
import rospy
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from trajectory_msgs.msg import JointTrajectoryPoint
import tf2_ros

try:
    from urllib2 import Request, urlopen
except ImportError:
    from urllib.request import Request, urlopen


from cr5_color_pointing.perception import ColorDepthDetector, ColorDetectionError, PointTopicDetector

try:
    from dobot_bringup.msg import RobotStatus
    from dobot_bringup.srv import ClearError, EnableRobot, SpeedFactor
except ImportError:
    RobotStatus = None
    ClearError = None
    EnableRobot = None
    SpeedFactor = None


class ColorPointingNode(object):
    def __init__(self):
        moveit_commander.roscpp_initialize(sys.argv)
        rospy.init_node("cr5_color_pointing")

        self.group_name = rospy.get_param("~moveit/planning_group", "cr5_arm")
        self.end_effector_link = rospy.get_param("~moveit/end_effector_link", "Link6")
        self.configured_frame = rospy.get_param("~frames/planning_frame", "world")
        self.camera_frame = rospy.get_param("~frames/camera_frame", "wrist_rgbd_camera_optical_frame")
        self.safety_height = float(rospy.get_param("~motion/safety_height", 0.25))
        self.above_box_extra_clearance = float(rospy.get_param("~motion/above_box_extra_clearance", 0.25))
        if self.above_box_extra_clearance < 0.0:
            rospy.logwarn("Negative above_box_extra_clearance requested; using 0.0 instead.")
            self.above_box_extra_clearance = 0.0
        self.ground_plane_z = float(rospy.get_param("~scene/ground_plane_z", 0.0))
        self.cube_size = float(rospy.get_param("~scene/cube_size", 0.05))
        self.max_tabletop_detection_z = float(rospy.get_param("~scene/max_tabletop_detection_z", 0.20))
        self.use_simulated_box_pose_fallback = bool(rospy.get_param("~scene/use_simulated_box_pose_fallback", True))
        self.allow_simulated_detection_fallback = bool(
            rospy.get_param("~scene/allow_simulated_detection_fallback", True)
        )
        self.configured_boxes = rospy.get_param("~scene/boxes", {})
        self.scan_target_link = rospy.get_param("~motion/scan_target_link", "Link6")
        self.scan_position = rospy.get_param("~motion/scan_position", None)
        self.scan_orientation = rospy.get_param("~motion/scan_orientation_xyzw", None)
        self.above_box_orientation = rospy.get_param(
            "~motion/above_box_orientation_xyzw",
            self.scan_orientation or [0.7071068, -0.7071068, 0.0, 0.0],
        )
        self.center_camera_over_box = bool(rospy.get_param("~motion/center_camera_over_box", True))
        self.scan_link6_position = rospy.get_param("~motion/scan_link6_position", None)
        self.scan_link6_orientation = rospy.get_param("~motion/scan_link6_orientation_xyzw", None)
        self.observation_joints = rospy.get_param("~motion/observation_joints", [0.0, -0.8, 1.2, 0.0, 1.1, 0.0])
        self.scan_joint_tolerance = float(rospy.get_param("~motion/scan_joint_tolerance", 0.035))
        self.home_state = rospy.get_param("~motion/home_state", "home")
        self.home_joints = rospy.get_param("~motion/home_joints", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.execution_mode = rospy.get_param("~motion/execution_mode", "auto").lower()
        self.gazebo_model_name = rospy.get_param("~motion/gazebo_model_name", "robot")
        self.gazebo_urdf_param = rospy.get_param("~motion/gazebo_urdf_param", "robot_description")
        self.velocity_scale = float(rospy.get_param("~motion/max_velocity_scaling", 0.2))
        self.accel_scale = float(rospy.get_param("~motion/max_acceleration_scaling", 0.2))
        self.controller_action = rospy.get_param(
            "~motion/controller_action",
            "/cr5_joint_trajectory_controller/follow_joint_trajectory",
        )
        self.controller_wait_margin = float(rospy.get_param("~motion/controller_wait_margin", 4.0))
        self.joint_state_timeout = float(rospy.get_param("~motion/joint_state_timeout", 5.0))
        self.joint_state_max_age = float(rospy.get_param("~motion/joint_state_max_age", 1.0))
        self.use_single_point_trajectories = bool(rospy.get_param("~motion/use_single_point_trajectories", True))
        self.single_point_duration = float(rospy.get_param("~motion/single_point_duration", 8.0))
        self.command_topic = rospy.get_param("~command_topic", "/cr5_color_pointing/command")
        self.perception_mode = rospy.get_param("~perception/mode", "rgbd").strip().lower()
        self.motion_only = bool(rospy.get_param("~hardware/motion_only", False))
        self.require_camera_topics = bool(rospy.get_param("~hardware/require_camera_topics", False))
        self.hardware_status_required = bool(rospy.get_param("~hardware/require_robot_status", False))
        self.require_robot_enabled = bool(rospy.get_param("~hardware/require_robot_enabled", False))
        self.auto_enable_robot = bool(rospy.get_param("~hardware/auto_enable_robot", False))
        self.clear_error_before_enable = bool(rospy.get_param("~hardware/clear_error_before_enable", False))
        self.robot_status_topic = rospy.get_param("~hardware/robot_status_topic", "/dobot_bringup/msg/RobotStatus")
        self.enable_service_name = rospy.get_param("~hardware/enable_service", "/dobot_bringup/srv/EnableRobot")
        self.clear_error_service_name = rospy.get_param("~hardware/clear_error_service", "/dobot_bringup/srv/ClearError")
        self.speed_factor_service_name = rospy.get_param("~hardware/speed_factor_service", "/dobot_bringup/srv/SpeedFactor")
        self.hardware_preflight_timeout = float(rospy.get_param("~hardware/preflight_timeout", 8.0))
        self.hardware_speed_factor = int(rospy.get_param("~hardware/speed_factor", 0))
        self.speed_factor_applied = False
        self.robot_status = None
        self.robot_status_lock = threading.Lock()
        self.joint_names = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
        self.last_commanded_joints = [0.0] * 6
        self.current_joint_positions = None
        self.current_joint_stamp = rospy.Time(0)
        self.gazebo_joint_fallback_enabled = self.execution_mode in ("auto", "gazebo")

        self.robot = moveit_commander.RobotCommander()
        self.scene = moveit_commander.PlanningSceneInterface()
        self.group = moveit_commander.MoveGroupCommander(self.group_name)
        self.group.set_max_velocity_scaling_factor(self.velocity_scale)
        self.group.set_max_acceleration_scaling_factor(self.accel_scale)

        self.planning_frame = self.group.get_planning_frame() or self.configured_frame
        if self.configured_frame and self.configured_frame != self.planning_frame:
            rospy.logwarn(
                "Configured frame '%s' differs from MoveIt planning frame '%s'. Using MoveIt planning frame '%s'.",
                self.configured_frame,
                self.planning_frame,
                self.planning_frame,
            )
        self.target_frame = self.planning_frame or self.configured_frame
        rospy.set_param("~frames/planning_frame", self.target_frame)

        try:
            self.group.set_pose_reference_frame(self.target_frame)
        except Exception:
            rospy.logwarn("MoveIt group did not accept pose reference frame '%s'.", self.target_frame)

        self.tf_buffer = tf2_ros.Buffer()
        self.detector = self._make_detector()
        self.command_lock = threading.Lock()
        self.joint_state_lock = threading.Lock()
        self.joint_state_sub = rospy.Subscriber("/joint_states", JointState, self._joint_state_cb, queue_size=1)
        self.command_sub = rospy.Subscriber(self.command_topic, String, self._command_topic_cb, queue_size=1)
        self.robot_status_sub = None
        if self.hardware_status_required or self.require_robot_enabled or self.auto_enable_robot:
            if RobotStatus is None:
                rospy.logerr("dobot_bringup messages are unavailable; hardware robot-status checks cannot run.")
            else:
                self.robot_status_sub = rospy.Subscriber(
                    self.robot_status_topic,
                    RobotStatus,
                    self._robot_status_cb,
                    queue_size=1,
                )
        self.trajectory_client = actionlib.SimpleActionClient(
            self.controller_action,
            FollowJointTrajectoryAction,
        )
        self.joint_state_pub = None
        self.joint_state_timer = None
        self.set_model_config = None
        self.get_model_state = None
        if self.gazebo_joint_fallback_enabled:
            self.joint_state_pub = rospy.Publisher("/joint_states", JointState, queue_size=10)
            self.joint_state_timer = rospy.Timer(rospy.Duration(0.05), self._publish_commanded_joint_state)
            self.set_model_config = rospy.ServiceProxy("/gazebo/set_model_configuration", SetModelConfiguration)
        if self.use_simulated_box_pose_fallback:
            self.get_model_state = rospy.ServiceProxy("/gazebo/get_model_state", GetModelState)

        rospy.loginfo("CR5 color pointing ready. Commands: scan, red, yellow, green, home, quit.")
        rospy.loginfo("Also listening for std_msgs/String commands on %s", self.command_topic)
        rospy.loginfo("Execution mode is '%s'.", self.execution_mode)
        rospy.loginfo("Perception mode is '%s'.", self.perception_mode)
        if self.motion_only:
            rospy.loginfo("Hardware motion-only mode is enabled; red/yellow/green use fixed scan-relative offsets.")
        rospy.loginfo("Using trajectory controller action %s.", self.controller_action)
        if not self.gazebo_joint_fallback_enabled:
            rospy.loginfo("Gazebo joint teleport fallback is disabled; using MoveIt/controller execution only.")
        if not self.allow_simulated_detection_fallback and not self.use_simulated_box_pose_fallback:
            rospy.loginfo("Simulated detection/box pose fallbacks are disabled; using %s perception.", self.perception_mode)
        if self.hardware_status_required:
            rospy.loginfo("Hardware robot-status preflight is enabled on %s.", self.robot_status_topic)

    def _make_detector(self):
        if self.perception_mode in ("rgbd", "rgb_depth", "color_depth"):
            return ColorDepthDetector(tf_buffer=self.tf_buffer)
        if self.perception_mode in ("point_topic", "external_point", "external"):
            return PointTopicDetector(tf_buffer=self.tf_buffer)
        rospy.logwarn("Unknown perception/mode '%s'; using rgbd.", self.perception_mode)
        self.perception_mode = "rgbd"
        return ColorDepthDetector(tf_buffer=self.tf_buffer)

    def spin(self):
        if sys.stdin.isatty():
            self._stdin_loop()
        else:
            rospy.logwarn("No interactive stdin is attached. Send commands on %s.", self.command_topic)
            rospy.spin()

    def _stdin_loop(self):
        prompt_pending = True
        while not rospy.is_shutdown():
            if prompt_pending:
                sys.stdout.write("cr5> ")
                sys.stdout.flush()
                prompt_pending = False
            ready, _, _ = select.select([sys.stdin], [], [], 0.5)
            if not ready:
                continue
            line = sys.stdin.readline()
            if not line:
                rospy.logwarn("stdin closed. Switching to command topic mode.")
                rospy.spin()
                return
            keep_running = self.handle_command(line)
            if not keep_running:
                return
            prompt_pending = True

    def _command_topic_cb(self, msg):
        with self.command_lock:
            self.handle_command(msg.data)

    def _joint_state_cb(self, msg):
        if not msg.name or not msg.position:
            return

        by_name = {}
        for index, name in enumerate(msg.name):
            if index < len(msg.position):
                by_name[name] = float(msg.position[index])

        if any(name not in by_name for name in self.joint_names):
            return

        with self.joint_state_lock:
            self.current_joint_positions = [by_name[name] for name in self.joint_names]
            self.current_joint_stamp = msg.header.stamp

    def _robot_status_cb(self, msg):
        with self.robot_status_lock:
            self.robot_status = msg

    def handle_command(self, text):
        action = self._parse_command(text)
        if action == "quit":
            rospy.signal_shutdown("quit requested")
            return False
        if action == "home":
            if self._preflight_command(action):
                self.return_home()
            return True
        if action == "scan":
            if self._preflight_command(action):
                self.move_to_scan_pose()
            return True
        if action in ("red", "yellow", "green"):
            if self.motion_only:
                if self._preflight_command(action):
                    self.move_motion_only_offset(action)
                return True
            if self._preflight_command(action):
                self.point_at_color(action)
            return True

        rospy.logwarn("Unknown command '%s'. Use scan, red, yellow, green, home, or quit.", text.strip())
        return True

    def _parse_command(self, text):
        normalized = re.sub(r"[^a-z]+", " ", text.lower()).strip()
        if normalized in ("quit", "exit"):
            return "quit"
        if normalized in ("home", "return home"):
            return "home"
        if normalized in (
            "scan",
            "observe",
            "observation",
            "move scan",
            "move to scan",
            "go scan",
            "go to scan",
            "return scan",
            "return to scan",
        ):
            return "scan"
        for color in ("red", "yellow", "green"):
            if normalized == color or normalized == "move above " + color:
                return color
        return None

    def _preflight_command(self, action):
        if self.hardware_status_required or self.require_robot_enabled or self.auto_enable_robot:
            if not self._ensure_robot_ready():
                return False
        if self.require_camera_topics and (not self.motion_only) and action in ("red", "yellow", "green"):
            if not self._ensure_detection_source(action):
                return False
        if not self._apply_speed_factor_once():
            return False
        return True

    def _ensure_robot_ready(self):
        if RobotStatus is None:
            rospy.logerr("Cannot check real CR5 status because dobot_bringup messages are not importable.")
            return False

        deadline = time.time() + max(0.5, self.hardware_preflight_timeout)
        status = None
        while not rospy.is_shutdown() and time.time() < deadline:
            with self.robot_status_lock:
                status = self.robot_status
            if status is not None:
                break
            time.sleep(0.05)

        if status is None:
            rospy.logerr("Timed out waiting for robot status on %s.", self.robot_status_topic)
            return False
        if not status.is_connected:
            rospy.logerr("Real CR5 driver is running but not connected to the robot controller.")
            return False
        if status.is_enable:
            return True
        if not self.require_robot_enabled:
            return True
        if not self.auto_enable_robot:
            rospy.logerr(
                "Real CR5 is connected but not enabled. Enable it from the Dobot RViz plugin "
                "or call %s, then resend the command.",
                self.enable_service_name,
            )
            return False

        if self.clear_error_before_enable and not self._call_clear_error():
            return False
        if not self._call_enable_robot():
            return False
        return self._wait_until_enabled()

    def _call_clear_error(self):
        if ClearError is None:
            rospy.logerr("Cannot clear robot errors because dobot_bringup services are not importable.")
            return False
        try:
            rospy.wait_for_service(self.clear_error_service_name, timeout=self.hardware_preflight_timeout)
            response = rospy.ServiceProxy(self.clear_error_service_name, ClearError)()
        except Exception as exc:
            rospy.logerr("Could not call %s: %s", self.clear_error_service_name, exc)
            return False
        if getattr(response, "res", 0) != 0:
            rospy.logerr("%s returned res=%s.", self.clear_error_service_name, response.res)
            return False
        return True

    def _call_enable_robot(self):
        if EnableRobot is None:
            rospy.logerr("Cannot enable robot because dobot_bringup services are not importable.")
            return False
        try:
            rospy.wait_for_service(self.enable_service_name, timeout=self.hardware_preflight_timeout)
            response = rospy.ServiceProxy(self.enable_service_name, EnableRobot)()
        except Exception as exc:
            rospy.logerr("Could not call %s: %s", self.enable_service_name, exc)
            return False
        if getattr(response, "res", 0) != 0:
            rospy.logerr("%s returned res=%s.", self.enable_service_name, response.res)
            return False
        return True

    def _wait_until_enabled(self):
        deadline = time.time() + max(0.5, self.hardware_preflight_timeout)
        while not rospy.is_shutdown() and time.time() < deadline:
            with self.robot_status_lock:
                status = self.robot_status
            if status is not None and status.is_connected and status.is_enable:
                return True
            time.sleep(0.05)
        rospy.logerr("Robot did not report enabled after calling %s.", self.enable_service_name)
        return False

    def _apply_speed_factor_once(self):
        if self.hardware_speed_factor <= 0 or self.speed_factor_applied:
            return True
        if SpeedFactor is None:
            rospy.logerr("Cannot set speed factor because dobot_bringup services are not importable.")
            return False
        try:
            rospy.wait_for_service(self.speed_factor_service_name, timeout=self.hardware_preflight_timeout)
            response = rospy.ServiceProxy(self.speed_factor_service_name, SpeedFactor)(self.hardware_speed_factor)
        except Exception as exc:
            rospy.logerr("Could not call %s: %s", self.speed_factor_service_name, exc)
            return False
        if getattr(response, "res", 0) != 0:
            rospy.logerr("%s returned res=%s.", self.speed_factor_service_name, response.res)
            return False
        self.speed_factor_applied = True
        rospy.loginfo("Set Dobot speed factor to %d.", self.hardware_speed_factor)
        return True

    def _ensure_detection_source(self, color):
        topics = self._detection_topics_for(color)
        published = dict(rospy.get_published_topics())
        missing = [topic for topic, _type_name in topics if topic not in published]
        if not missing:
            return True
        rospy.logerr(
            "Detection source is missing required ROS topics: %s. "
            "Start the camera/bridge before commanding a color move.",
            ", ".join(missing),
        )
        return False

    def _detection_topics_for(self, color):
        if self.perception_mode in ("point_topic", "external_point", "external"):
            template = rospy.get_param("~topics/detected_point_template", "/cr5_color_pointing/detections/{color}")
            return [(template.format(color=color), "geometry_msgs/PointStamped")]
        return [
            (rospy.get_param("~topics/rgb_image", "/wrist_rgbd/rgb/image_raw"), "sensor_msgs/Image"),
            (rospy.get_param("~topics/depth_image", "/wrist_rgbd/depth/image_raw"), "sensor_msgs/Image"),
            (rospy.get_param("~topics/camera_info", "/wrist_rgbd/rgb/camera_info"), "sensor_msgs/CameraInfo"),
        ]

    def _motion_only_offset_key_for_color(self, color):
        """Resolve a typed color to the fixed motion slot using the HTTP locate API.

        API examples:
          /locate/red -> {"color":"red","location":"mid"}

        Mapping:
          left  -> yellow offset
          mid   -> red offset
          right -> green offset
        """
        if not bool(rospy.get_param("~motion/locate_api/enabled", False)):
            return color

        base_url = rospy.get_param("~motion/locate_api/base_url", "")
        timeout = float(rospy.get_param("~motion/locate_api/timeout", 2.0))
        mapping = rospy.get_param(
            "~motion/locate_api/location_to_command",
            {"left": "yellow", "mid": "red", "right": "green"},
        )

        if not base_url:
            rospy.logerr("motion/locate_api/base_url is empty.")
            return None

        url = base_url.rstrip("/") + "/" + color
        try:
            req = Request(url)
            response = urlopen(req, timeout=timeout)
            raw = response.read()
            if not isinstance(raw, str):
                raw = raw.decode("utf-8")
            data = json.loads(raw)
        except Exception as exc:
            rospy.logerr("Could not query locate API %s: %s", url, exc)
            return None

        reported_color = str(data.get("color", "")).strip().lower()
        location = str(data.get("location", "")).strip().lower()

        if reported_color and reported_color != color:
            rospy.logwarn(
                "Locate API color mismatch: requested '%s' but response color is '%s'.",
                color,
                reported_color,
            )

        offset_key = mapping.get(location)
        if offset_key is None:
            rospy.logerr(
                "Locate API returned unsupported location '%s'. Expected one of: %s.",
                location,
                sorted(mapping.keys()),
            )
            return None

        rospy.loginfo(
            "Locate API: requested color '%s' is at location '%s'; using '%s' motion slot.",
            color,
            location,
            offset_key,
        )
        return offset_key

    def move_motion_only_offset(self, color):
        rospy.loginfo("Motion-only %s command: moving to scan pose first.", color)
        if not self.move_to_scan_pose():
            rospy.logerr("Could not move to scan pose before motion-only %s command.", color)
            return False

        rospy.sleep(0.5)

        offset_key = self._motion_only_offset_key_for_color(color)
        if offset_key is None:
            return False

        offsets = rospy.get_param("~motion/motion_only_offsets", {})
        commands = offsets.get("commands", {})
        command = commands.get(offset_key)
        if command is None:
            rospy.logerr(
                "No motion_only_offsets command configured for requested color '%s' resolved to motion slot '%s'.",
                color,
                offset_key,
            )
            return False

        right_axis = offsets.get("right_axis_xyz", [0.0, -1.0, 0.0])
        if len(right_axis) != 3:
            rospy.logerr("motion_only_offsets/right_axis_xyz must have 3 values.")
            return False

        down_m = float(command.get("down_m", 0.0))
        right_m = float(command.get("right_m", 0.0))
        min_z = float(rospy.get_param("~motion/motion_only_min_z", 0.10))

        try:
            current = self.group.get_current_pose(self.end_effector_link)
        except Exception as exc:
            rospy.logerr("Could not read current pose for motion-only offset: %s", exc)
            return False

        target = PoseStamped()
        target.header.stamp = rospy.Time.now()
        target.header.frame_id = self.target_frame
        target.pose = current.pose

        # Down = negative Z in planning frame.
        target.pose.position.z -= down_m

        # Right = configurable planning-frame axis.
        target.pose.position.x += float(right_axis[0]) * right_m
        target.pose.position.y += float(right_axis[1]) * right_m
        target.pose.position.z += float(right_axis[2]) * right_m

        rospy.loginfo(
            "Motion-only %s target: down=%.3f m, right=%.3f m, axis=[%.1f, %.1f, %.1f], target %s x=%.3f y=%.3f z=%.3f.",
            color,
            down_m,
            right_m,
            float(right_axis[0]),
            float(right_axis[1]),
            float(right_axis[2]),
            target.header.frame_id,
            target.pose.position.x,
            target.pose.position.y,
            target.pose.position.z,
        )

        if target.pose.position.z < min_z:
            rospy.logerr(
                "Refusing %s target: z=%.3f is below motion_only_min_z=%.3f.",
                color,
                target.pose.position.z,
                min_z,
            )
            return False

        return self.move_to_motion_only_pose(target, "%s motion-only offset" % color)

    def move_to_motion_only_pose(self, pose, label):
        if not self._prepare_for_planning(label):
            return False
        try:
            self.group.set_pose_target(pose, self.end_effector_link)
        except Exception as exc:
            rospy.logerr("%s target is invalid: %s", label, exc)
            return False
        return self._plan_and_send_to_controller(label)

    def point_at_color(self, color):
        rospy.loginfo("Moving to scan pose before detecting %s.", color)
        if not self.move_to_scan_pose():
            rospy.logerr("Could not move to scan pose. Skipping detection.")
            return False

        try:
            result = self.detector.detect(color)
        except (rospy.ROSException, ColorDetectionError) as exc:
            if not self.allow_simulated_detection_fallback:
                rospy.logerr("Detection failed for %s: %s", color, exc)
                return False
            rospy.logwarn(
                "Detection failed for %s: %s. Using simulated box pose fallback.",
                color,
                exc,
            )
            target_point = self._simulated_box_point(color)
            if target_point is None:
                rospy.logerr("No simulated fallback pose is available for %s.", color)
                return False
            target_pose = self._make_above_box_pose(target_point)
            return self.move_to_pose(target_pose)

        target_point = self._resolve_tabletop_target(color, result["target_point"])
        if target_point is None:
            return False
        target_pose = self._make_above_box_pose(target_point)
        rospy.loginfo(
            "Detected %s at %s x=%.3f y=%.3f z=%.3f; moving above to z=%.3f.",
            color,
            target_point.header.frame_id,
            target_point.point.x,
            target_point.point.y,
            target_point.point.z,
            target_pose.pose.position.z,
        )
        return self.move_to_pose(target_pose)

    def move_to_scan_pose(self):
        if self.scan_position and self.scan_orientation:
            return self.move_to_scan_pose_target(
                self.scan_position,
                self.scan_orientation,
                self.scan_target_link,
            )
        if self.scan_link6_position and self.scan_link6_orientation:
            return self.move_to_scan_pose_target(
                self.scan_link6_position,
                self.scan_link6_orientation,
                self.end_effector_link,
            )
        rospy.loginfo("Moving to observation_joints for wrist-camera scan.")
        return self.move_to_observation_pose()

    def move_to_scan_pose_target(self, position, orientation, target_link):
        if len(position) != 3 or len(orientation) != 4:
            rospy.logerr("Scan pose requires 3 position values and 4 orientation values.")
            return False

        pose = PoseStamped()
        pose.header.stamp = rospy.Time.now()
        pose.header.frame_id = self.target_frame
        pose.pose.position.x = float(position[0])
        pose.pose.position.y = float(position[1])
        pose.pose.position.z = float(position[2])
        pose.pose.orientation.x = float(orientation[0])
        pose.pose.orientation.y = float(orientation[1])
        pose.pose.orientation.z = float(orientation[2])
        pose.pose.orientation.w = float(orientation[3])

        rospy.loginfo(
            "Moving to scan pose: %s x=%.3f y=%.3f z=%.3f in %s.",
            target_link,
            pose.pose.position.x,
            pose.pose.position.y,
            pose.pose.position.z,
            pose.header.frame_id,
        )
        if not self._prepare_for_planning("scan pose"):
            return False
        try:
            self.group.set_pose_target(pose, target_link)
        except Exception as exc:
            rospy.logerr("Scan pose target is invalid: %s", exc)
            return False

        return self._plan_and_send_to_controller("scan pose")

    def move_to_observation_pose(self):
        if len(self.observation_joints) != 6:
            rospy.logerr("Observation joint list must contain 6 values.")
            return False
        joints = [float(v) for v in self.observation_joints]
        if not self._wait_for_current_joint_state("observation pose"):
            return False
        current_joints, _stamp = self._latest_joint_state()
        if self._joints_close(current_joints, joints, self.scan_joint_tolerance):
            max_error = max(self._joint_abs_errors(current_joints, joints))
            self.last_commanded_joints = current_joints
            rospy.loginfo(
                "Already within %.3f rad of observation_joints; skipping redundant scan move "
                "(max joint error %.4f rad).",
                self.scan_joint_tolerance,
                max_error,
            )
            return True
        if not self._prepare_for_planning("observation pose", wait_for_joint_state=False):
            return False
        try:
            self.group.set_joint_value_target(joints)
        except Exception as exc:
            rospy.logerr("Scan joint target is invalid or outside MoveIt limits: %s", exc)
            return False
        return self._plan_and_send_to_controller("observation pose", fallback_joints=joints)

    def return_home(self):
        if len(self.home_joints) != 6:
            rospy.logerr("Home joint list must contain 6 values.")
            return False

        rospy.loginfo("Returning to configured launch/home joints.")
        if not self._prepare_for_planning("home"):
            return False
        joints = [float(v) for v in self.home_joints]
        try:
            self.group.set_joint_value_target(joints)
        except Exception as exc:
            rospy.logerr("Home joint target is invalid or outside MoveIt limits: %s", exc)
            return False
        return self._plan_and_send_to_controller("home", fallback_joints=joints)

    def _make_above_box_pose(self, target_point):
        min_clearance_z = self._minimum_above_box_camera_z()
        orientation = self.above_box_orientation
        if len(orientation) != 4:
            rospy.logwarn("Invalid above-box orientation; using downward wrist-camera orientation.")
            orientation = [0.7071068, -0.7071068, 0.0, 0.0]
        orientation = self._normalize_quaternion(orientation)

        desired_camera_position = [
            target_point.point.x,
            target_point.point.y,
            min_clearance_z,
        ]
        link6_position = list(desired_camera_position)
        if self.center_camera_over_box:
            camera_offset = self._camera_offset_in_end_effector()
            world_offset = self._rotate_vector_by_quaternion(camera_offset, orientation)
            link6_position = [
                desired_camera_position[0] - world_offset[0],
                desired_camera_position[1] - world_offset[1],
                desired_camera_position[2] - world_offset[2],
            ]
            rospy.loginfo(
                "Centering %s above box: camera target x=%.3f y=%.3f z=%.3f, "
                "%s target x=%.3f y=%.3f z=%.3f.",
                self.camera_frame,
                desired_camera_position[0],
                desired_camera_position[1],
                desired_camera_position[2],
                self.end_effector_link,
                link6_position[0],
                link6_position[1],
                link6_position[2],
            )

        pose = PoseStamped()
        pose.header.stamp = rospy.Time.now()
        pose.header.frame_id = target_point.header.frame_id or self.target_frame
        pose.pose.position.x = link6_position[0]
        pose.pose.position.y = link6_position[1]
        pose.pose.position.z = link6_position[2]
        pose.pose.orientation.x = float(orientation[0])
        pose.pose.orientation.y = float(orientation[1])
        pose.pose.orientation.z = float(orientation[2])
        pose.pose.orientation.w = float(orientation[3])
        return pose

    def _normalize_quaternion(self, orientation):
        values = [float(v) for v in orientation]
        norm = sum(v * v for v in values) ** 0.5
        if norm < 1e-9:
            rospy.logwarn("Above-box orientation has near-zero norm; using downward wrist-camera orientation.")
            return [0.7071068, -0.7071068, 0.0, 0.0]
        return [v / norm for v in values]

    def _camera_offset_in_end_effector(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                self.end_effector_link,
                self.camera_frame,
                rospy.Time(0),
                rospy.Duration(1.0),
            )
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException) as exc:
            rospy.logwarn(
                "Could not lookup %s -> %s camera offset; using zero offset: %s",
                self.end_effector_link,
                self.camera_frame,
                exc,
            )
            return [0.0, 0.0, 0.0]

        return [
            transform.transform.translation.x,
            transform.transform.translation.y,
            transform.transform.translation.z,
        ]

    def _rotate_vector_by_quaternion(self, vector, orientation):
        qx, qy, qz, qw = orientation
        vx, vy, vz = [float(v) for v in vector]
        tx = 2.0 * (qy * vz - qz * vy)
        ty = 2.0 * (qz * vx - qx * vz)
        tz = 2.0 * (qx * vy - qy * vx)
        return [
            vx + qw * tx + (qy * tz - qz * ty),
            vy + qw * ty + (qz * tx - qx * tz),
            vz + qw * tz + (qx * ty - qy * tx),
        ]

    def move_to_pose(self, pose):
        if pose.pose.position.z < self._minimum_above_box_camera_z():
            rospy.logerr("Refusing unsafe target z=%.3f.", pose.pose.position.z)
            return False

        if not self._prepare_for_planning("pose target"):
            return False
        try:
            self.group.set_pose_target(pose, self.end_effector_link)
        except Exception as exc:
            rospy.logerr("Pose target is invalid: %s", exc)
            return False
        return self._plan_and_send_to_controller("pose target")

    def _minimum_above_box_camera_z(self):
        return self.ground_plane_z + self.cube_size + self.safety_height + self.above_box_extra_clearance

    def _prepare_for_planning(self, label, wait_for_joint_state=True):
        self.group.clear_pose_targets()
        if wait_for_joint_state and not self._wait_for_current_joint_state(label):
            return False
        try:
            self.group.set_start_state_to_current_state()
        except Exception as exc:
            rospy.logerr("Could not set MoveIt start state for %s: %s", label, exc)
            return False
        return True

    def _joint_abs_errors(self, current, target):
        if current is None or len(current) != len(target):
            return [float("inf")]
        return [abs(float(a) - float(b)) for a, b in zip(current, target)]

    def _joints_close(self, current, target, tolerance):
        if tolerance < 0.0:
            return False
        return max(self._joint_abs_errors(current, target)) <= tolerance

    def _plan_and_send_to_controller(self, label, fallback_joints=None):
        try:
            plan_result = self.group.plan()
        except Exception as exc:
            rospy.logerr("MoveIt planning failed for %s: %s", label, exc)
            self.group.clear_pose_targets()
            return self._gazebo_joint_fallback(fallback_joints or [], label)

        plan = plan_result
        success = True
        if isinstance(plan_result, tuple):
            success = bool(plan_result[0])
            plan = plan_result[1] if len(plan_result) >= 2 else None

        points = []
        if plan is not None:
            points = getattr(plan.joint_trajectory, "points", [])
        if not success or not points:
            rospy.logerr("MoveIt did not produce a usable plan for %s.", label)
            self.group.clear_pose_targets()
            return self._gazebo_joint_fallback(fallback_joints or [], label)

        ok = self._send_trajectory_to_controller(plan, label)
        self.group.stop()
        self.group.clear_pose_targets()
        if ok:
            if self._record_current_joint_state(label):
                return True
            rospy.logerr("Could not confirm fresh joint state after %s.", label)

        return self._gazebo_joint_fallback(fallback_joints or [], label)

    def _send_trajectory_to_controller(self, plan, label):
        if not self.trajectory_client.wait_for_server(rospy.Duration(5.0)):
            rospy.logerr("Trajectory controller action %s is unavailable.", self.controller_action)
            return False

        goal = FollowJointTrajectoryGoal()
        if self.use_single_point_trajectories:
            goal.trajectory = self._single_point_trajectory(plan)
        else:
            goal.trajectory = plan.joint_trajectory
        goal.trajectory.header.stamp = rospy.Time.now() + rospy.Duration(0.2)
        duration = goal.trajectory.points[-1].time_from_start.to_sec()
        wait_time = max(1.0, duration + self.controller_wait_margin)

        rospy.loginfo(
            "Sending %s trajectory with %d points to %s; waiting %.1f s.",
            label,
            len(goal.trajectory.points),
            self.controller_action,
            wait_time,
        )
        self.trajectory_client.send_goal(goal)
        finished = self.trajectory_client.wait_for_result(rospy.Duration(wait_time))
        state = self.trajectory_client.get_state()
        if not finished:
            rospy.logerr("%s trajectory did not finish before timeout; cancelling goal.", label)
            self.trajectory_client.cancel_goal()
            return False
        if state == GoalStatus.SUCCEEDED:
            return True

        rospy.logerr(
            "%s trajectory ended with action state %s.",
            label,
            state,
        )
        return False

    def _latest_joint_state(self):
        with self.joint_state_lock:
            if self.current_joint_positions is None:
                return None, rospy.Time(0)
            return list(self.current_joint_positions), self.current_joint_stamp

    def _is_fresh_joint_state(self, stamp):
        if self.joint_state_max_age <= 0.0:
            return True
        if stamp == rospy.Time(0):
            return True

        now = rospy.Time.now()
        if now == rospy.Time(0):
            return True

        age = (now - stamp).to_sec()
        return age <= self.joint_state_max_age

    def _wait_for_current_joint_state(self, label):
        deadline = time.time() + max(0.1, self.joint_state_timeout)
        while not rospy.is_shutdown() and time.time() < deadline:
            positions, stamp = self._latest_joint_state()
            if positions is not None and self._is_fresh_joint_state(stamp):
                return True
            time.sleep(0.05)

        rospy.logerr(
            "Timed out waiting for fresh /joint_states before %s. "
            "Check joint_state_controller and Gazebo physics.",
            label,
        )
        return False

    def _record_current_joint_state(self, label):
        if not self._wait_for_current_joint_state("%s completion" % label):
            return False
        positions, _stamp = self._latest_joint_state()
        if positions is None:
            return False
        self.last_commanded_joints = positions
        return True

    def _single_point_trajectory(self, plan):
        trajectory = plan.joint_trajectory
        final_point = trajectory.points[-1]
        point = JointTrajectoryPoint()
        point.positions = list(final_point.positions)
        point.velocities = [0.0] * len(point.positions)
        point.accelerations = [0.0] * len(point.positions)
        point.time_from_start = rospy.Duration(max(self.single_point_duration, final_point.time_from_start.to_sec()))

        simple = type(trajectory)()
        simple.header = trajectory.header
        simple.joint_names = list(trajectory.joint_names)
        simple.points = [point]
        return simple

    def _plan_current_target_final_joints(self):
        try:
            plan_result = self.group.plan()
        except Exception as exc:
            rospy.logerr("Planning failed during fallback: %s", exc)
            return None

        plan = plan_result
        if isinstance(plan_result, tuple):
            if len(plan_result) >= 2:
                plan = plan_result[1]
            else:
                return None

        points = getattr(plan.joint_trajectory, "points", [])
        if not points:
            return None
        return [float(v) for v in points[-1].positions]

    def _gazebo_joint_fallback(self, joints, label):
        if not self.gazebo_joint_fallback_enabled:
            rospy.logerr("MoveIt execution failed for %s and Gazebo fallback is disabled.", label)
            return False
        if len(joints) != 6:
            rospy.logerr("Expected 6 joint values for %s fallback, got %d.", label, len(joints))
            return False
        try:
            rospy.wait_for_service("/gazebo/set_model_configuration", timeout=2.0)
            response = self.set_model_config(
                self.gazebo_model_name,
                self.gazebo_urdf_param,
                self.joint_names,
                [float(v) for v in joints],
            )
        except Exception as exc:
            rospy.logerr("Gazebo fallback failed for %s: %s", label, exc)
            return False

        if not response.success:
            rospy.logerr("Gazebo rejected %s fallback: %s", label, response.status_message)
            return False

        self.last_commanded_joints = [float(v) for v in joints]
        self._publish_commanded_joint_state(None)
        rospy.logwarn("Used Gazebo joint-state fallback for %s: %s", label, response.status_message)
        return True

    def _resolve_tabletop_target(self, color, detected_point):
        max_z = self.ground_plane_z + self.max_tabletop_detection_z
        min_z = self.ground_plane_z - 0.05
        if min_z <= detected_point.point.z <= max_z:
            return detected_point

        rospy.logwarn(
            "Detected %s point z=%.3f is not near tabletop z=%.3f. Using simulated box pose fallback.",
            color,
            detected_point.point.z,
            self.ground_plane_z,
        )
        fallback = self._simulated_box_point(color)
        if fallback is not None:
            return fallback
        rospy.logerr(
            "Detected %s point is not near the tabletop and simulated box pose fallback is disabled.",
            color,
        )
        return None

    def _simulated_box_point(self, color):
        if not self.use_simulated_box_pose_fallback:
            return None

        point = PoseStamped()
        point.header.stamp = rospy.Time.now()
        point.header.frame_id = self.target_frame

        try:
            rospy.wait_for_service("/gazebo/get_model_state", timeout=1.0)
            state = self.get_model_state("%s_box" % color, "world")
            if state.success:
                point.pose.position.x = state.pose.position.x
                point.pose.position.y = state.pose.position.y
                point.pose.position.z = state.pose.position.z
                return self._pose_to_point_stamped(point)
            rospy.logwarn("Gazebo did not return %s_box pose: %s", color, state.status_message)
        except Exception as exc:
            rospy.logwarn("Could not read Gazebo %s_box pose: %s", color, exc)

        if color in self.configured_boxes and len(self.configured_boxes[color]) >= 3:
            box = self.configured_boxes[color]
            point.pose.position.x = float(box[0])
            point.pose.position.y = float(box[1])
            point.pose.position.z = float(box[2])
            return self._pose_to_point_stamped(point)

        return None

    def _pose_to_point_stamped(self, pose):
        from geometry_msgs.msg import PointStamped

        point = PointStamped()
        point.header = pose.header
        point.point.x = pose.pose.position.x
        point.point.y = pose.pose.position.y
        point.point.z = pose.pose.position.z
        return point

    def _publish_commanded_joint_state(self, _event):
        if self.joint_state_pub is None:
            return
        msg = JointState()
        msg.header.stamp = rospy.Time.now()
        msg.name = list(self.joint_names)
        msg.position = list(self.last_commanded_joints)
        self.joint_state_pub.publish(msg)


def main():
    node = ColorPointingNode()
    try:
        node.spin()
    finally:
        moveit_commander.roscpp_shutdown()


if __name__ == "__main__":
    main()
