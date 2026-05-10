#!/usr/bin/env python3
import rospy
from dobot_bringup.srv import EnableRobot, ClearError

def execute_hardware_enablement():
    """
    Autonomous node to transition the CR5A into an active state, bypassing GUI requirements.
    """
    rospy.init_node('cr5_autonomous_enabler', anonymous=True)
    
    # Phase 1: Purge residual hardware faults
    rospy.loginfo("Awaiting CC162 Controller ClearError dashboard service...")
    rospy.wait_for_service('/dobot_bringup/srv/ClearError')
    try:
        clear_hardware_err = rospy.ServiceProxy('/dobot_bringup/srv/ClearError', ClearError)
        clear_hardware_err()
        rospy.loginfo("Diagnostic purge complete. Hardware faults cleared.")
    except rospy.ServiceException as error_trace:
        rospy.logerr("ClearError Service invocation failure: %s", error_trace)

    # Phase 2: Actuate Servos and Release Brakes
    rospy.loginfo("Awaiting CC162 Controller EnableRobot dashboard service...")
    rospy.wait_for_service('/dobot_bringup/srv/EnableRobot')
    try:
        enable_servos = rospy.ServiceProxy('/dobot_bringup/srv/EnableRobot', EnableRobot)
        enable_servos()
        rospy.loginfo("CR5A System Enabled. Servos engaged. Ready for Port 30003 telemetry.")
    except rospy.ServiceException as error_trace:
        rospy.logerr("EnableRobot Service invocation failure: %s", error_trace)

if __name__ == "__main__":
    execute_hardware_enablement()
