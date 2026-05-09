#!/usr/bin/env python
from __future__ import print_function

import time

import actionlib
import rospy
from actionlib_msgs.msg import GoalStatus
from control_msgs.msg import FollowJointTrajectoryAction, FollowJointTrajectoryGoal
from controller_manager_msgs.srv import ListControllers, SwitchController
from gazebo_msgs.srv import SetModelConfiguration
from std_srvs.srv import Empty
from trajectory_msgs.msg import JointTrajectoryPoint


STRICT = 2


def get_controller_states():
    list_controllers = rospy.ServiceProxy(
        "/controller_manager/list_controllers", ListControllers
    )
    return {
        controller.name: controller.state
        for controller in list_controllers().controller
    }


def wait_for_controllers(required, allowed_states, timeout, poll_period):
    rospy.loginfo(
        "Waiting for controllers %s to be in states %s", required, allowed_states
    )
    rospy.wait_for_service("/controller_manager/list_controllers", timeout)
    deadline = time.time() + timeout

    while not rospy.is_shutdown():
        states = get_controller_states()
        missing = [name for name in required if states.get(name) not in allowed_states]
        if not missing:
            rospy.loginfo("Required Gazebo controllers reached requested states.")
            return
        if time.time() > deadline:
            raise rospy.ROSException(
                "Timed out waiting for controllers %s. Current states: %s"
                % (missing, states)
            )
        time.sleep(poll_period)


def start_controllers(required, timeout, poll_period):
    wait_for_controllers(
        required, ["running", "stopped", "initialized"], timeout, poll_period
    )
    states = get_controller_states()
    stopped = [name for name in required if states.get(name) != "running"]
    if not stopped:
        rospy.loginfo("Required Gazebo controllers are already running.")
        return

    rospy.loginfo(
        "Unpausing Gazebo briefly so ros_control can switch controllers: %s", stopped
    )
    unpause = rospy.ServiceProxy("/gazebo/unpause_physics", Empty)
    unpause()

    rospy.wait_for_service("/controller_manager/switch_controller", timeout)
    switch_controller = rospy.ServiceProxy(
        "/controller_manager/switch_controller", SwitchController
    )
    response = switch_controller(stopped, [], STRICT, True, timeout)
    if not response.ok:
        raise rospy.ROSException(
            "Failed to start Gazebo controllers through switch_controller: %s"
            % stopped
        )

    wait_for_controllers(required, ["running"], timeout, poll_period)


def get_initial_hold_pose():
    joint_names = rospy.get_param("~hold_joints", [])
    positions = [float(position) for position in rospy.get_param("~hold_positions", [])]
    if len(joint_names) != len(positions) or not joint_names:
        raise rospy.ROSException(
            "Initial hold requires matching non-empty hold_joints and hold_positions."
        )
    return joint_names, positions


def reset_model_configuration(joint_names, positions, timeout):
    if not rospy.get_param("~reset_initial_pose", True):
        return

    model_name = rospy.get_param("~model_name", "robot")
    urdf_param_name = rospy.get_param("~urdf_param_name", "robot_description")
    rospy.loginfo(
        "Resetting Gazebo model %s to the initial hold configuration.", model_name
    )
    rospy.wait_for_service("/gazebo/set_model_configuration", timeout)
    set_model_configuration = rospy.ServiceProxy(
        "/gazebo/set_model_configuration", SetModelConfiguration
    )
    response = set_model_configuration(
        model_name, urdf_param_name, joint_names, positions
    )
    if not response.success:
        raise rospy.ROSException(
            "Failed to reset Gazebo model configuration: %s" % response.status_message
        )


def send_initial_hold_goal(joint_names, positions, timeout):
    action_name = rospy.get_param(
        "~trajectory_action",
        "/cr5_joint_trajectory_controller/follow_joint_trajectory",
    )
    rospy.loginfo("Sending initial hold trajectory to %s.", action_name)
    client = actionlib.SimpleActionClient(action_name, FollowJointTrajectoryAction)
    if not client.wait_for_server(rospy.Duration(timeout)):
        raise rospy.ROSException(
            "Timed out waiting for trajectory action server: %s" % action_name
        )

    point = JointTrajectoryPoint()
    point.positions = positions
    point.velocities = [0.0] * len(joint_names)
    point.time_from_start = rospy.Duration(
        float(rospy.get_param("~hold_duration", 1.0))
    )

    goal = FollowJointTrajectoryGoal()
    goal.trajectory.joint_names = joint_names
    goal.trajectory.points = [point]
    goal.trajectory.header.stamp = rospy.Time(0)
    client.send_goal(goal)
    return client


def main():
    rospy.init_node("unpause_after_controllers")

    required = rospy.get_param(
        "~controllers",
        ["joint_state_controller", "cr5_joint_trajectory_controller"],
    )
    timeout = float(rospy.get_param("~timeout", 60.0))
    poll_period = float(rospy.get_param("~poll_period", 0.2))

    rospy.loginfo("Waiting for Gazebo controller manager and unpause service.")
    rospy.wait_for_service("/controller_manager/switch_controller", timeout)
    rospy.wait_for_service("/gazebo/unpause_physics", timeout)
    rospy.wait_for_service("/gazebo/pause_physics", timeout)

    start_controllers(required, timeout, poll_period)

    pause = rospy.ServiceProxy("/gazebo/pause_physics", Empty)
    pause()

    hold_client = None
    if rospy.get_param("~hold_initial_pose", False):
        joint_names, positions = get_initial_hold_pose()
        reset_model_configuration(joint_names, positions, timeout)
        hold_client = send_initial_hold_goal(joint_names, positions, timeout)

    unpause = rospy.ServiceProxy("/gazebo/unpause_physics", Empty)
    unpause()

    if hold_client:
        result_timeout = float(rospy.get_param("~hold_result_timeout", timeout))
        if not hold_client.wait_for_result(rospy.Duration(result_timeout)):
            raise rospy.ROSException("Timed out waiting for initial hold result.")
        result = hold_client.get_result()
        state = hold_client.get_state()
        if state != GoalStatus.SUCCEEDED:
            raise rospy.ROSException(
                "Initial hold trajectory failed with action state %s: %s"
                % (state, getattr(result, "error_string", ""))
            )

    rospy.loginfo("Gazebo physics unpaused after controllers were running.")


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
