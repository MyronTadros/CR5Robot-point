#!/usr/bin/env python
from __future__ import print_function

import threading

import rospy
from gazebo_msgs.srv import SetModelConfiguration
from sensor_msgs.msg import JointState


class GazeboJointStateMirror(object):
    def __init__(self):
        rospy.init_node("gazebo_joint_state_mirror")

        self.model_name = rospy.get_param("~model_name", "hardware_robot")
        self.urdf_param_name = rospy.get_param("~urdf_param_name", "robot_description")
        self.joint_state_topic = rospy.get_param("~joint_state_topic", "/joint_states")
        self.joint_names = rospy.get_param("~joint_names", ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"])
        self.rate_hz = float(rospy.get_param("~rate", 10.0))

        self._lock = threading.Lock()
        self._latest = None

        rospy.loginfo("Waiting for /gazebo/set_model_configuration.")
        rospy.wait_for_service("/gazebo/set_model_configuration")
        self._set_model_configuration = rospy.ServiceProxy(
            "/gazebo/set_model_configuration",
            SetModelConfiguration,
        )

        rospy.Subscriber(self.joint_state_topic, JointState, self._joint_state_cb, queue_size=1)

    def _joint_state_cb(self, msg):
        positions_by_name = dict(zip(msg.name, msg.position))
        try:
            positions = [positions_by_name[name] for name in self.joint_names]
        except KeyError:
            return

        with self._lock:
            self._latest = positions

    def spin(self):
        rate = rospy.Rate(self.rate_hz)
        warned = False
        while not rospy.is_shutdown():
            with self._lock:
                positions = list(self._latest) if self._latest is not None else None

            if positions is None:
                if not warned:
                    rospy.logwarn("Waiting for joint states on %s.", self.joint_state_topic)
                    warned = True
                rate.sleep()
                continue

            try:
                response = self._set_model_configuration(
                    self.model_name,
                    self.urdf_param_name,
                    self.joint_names,
                    positions,
                )
                if not response.success:
                    rospy.logwarn_throttle(5.0, "Gazebo mirror update failed: %s", response.status_message)
            except rospy.ServiceException as exc:
                rospy.logwarn_throttle(5.0, "Gazebo mirror service error: %s", exc)

            rate.sleep()


if __name__ == "__main__":
    GazeboJointStateMirror().spin()
