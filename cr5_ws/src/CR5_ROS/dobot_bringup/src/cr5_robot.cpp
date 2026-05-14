/**
 ***********************************************************************************************************************
 *
 * @author ZhangRan
 * @date   2021/08/07
 *
 * <h2><center>&copy; COPYRIGHT 2021 DOBOT CORPORATION</center></h2>
 *
 ***********************************************************************************************************************
 */

#include <ros/ros.h>
#include <ros/param.h>
#include <dobot_bringup/cr5_robot.h>
#include <algorithm>
#include <cmath>

CR5Robot::CR5Robot(ros::NodeHandle& nh, std::string name)
    : ActionServer<FollowJointTrajectoryAction>(nh, std::move(name), false), goal_{}, control_nh_(nh)
{
    index_ = 0;
    memset(goal_, 0, sizeof(goal_));
}

CR5Robot::~CR5Robot()
{
    ROS_INFO("~CR5Robot");
}

void CR5Robot::init()
{
    std::string ip = control_nh_.param<std::string>("robot_ip_address", "192.168.5.1");
    int real_time_port = control_nh_.param("real_time_port", 30004);
    int dashboard_port = control_nh_.param("dashboard_port", 29999);
    int motion_port = control_nh_.param("motion_port", 30003);

    trajectory_duration_ = control_nh_.param("trajectory_duration", 0.3);
    servo_period_ = control_nh_.param("servo_period", 0.05);
    goal_tolerance_ = control_nh_.param("goal_tolerance", 0.01);
    if (servo_period_ <= 0.0)
        servo_period_ = 0.05;
    ROS_INFO("robot_ip_address : %s", ip.c_str());
    ROS_INFO("real_time_port : %d", real_time_port);
    ROS_INFO("dashboard_port : %d", dashboard_port);
    ROS_INFO("motion_port : %d", motion_port);
    ROS_INFO("trajectory_duration : %0.2f", trajectory_duration_);
    ROS_INFO("servo_period : %0.3f", servo_period_);
    ROS_INFO("goal_tolerance : %0.4f", goal_tolerance_);

    commander_ = std::make_shared<CR5Commander>(
        ip,
        static_cast<uint16_t>(real_time_port),
        static_cast<uint16_t>(dashboard_port),
        static_cast<uint16_t>(motion_port)
    );
    commander_->init();

    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/MovJ", &CR5Robot::movJ, this));
    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/MoveJog", &CR5Robot::moveJog, this));
    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/MovL", &CR5Robot::movL, this));
    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/RelMovJ", &CR5Robot::relMovJ, this));
    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/RelMovL", &CR5Robot::relMovL, this));
    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/ServoJ", &CR5Robot::servoJ, this));
    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/ServoP", &CR5Robot::servoP, this));
    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/JointMovJ", &CR5Robot::jointMovJ, this));

    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/ClearError", &CR5Robot::clearError, this));
    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/ResetRobot", &CR5Robot::resetRobot, this));
    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/DisableRobot", &CR5Robot::disableRobot, this));
    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/EnableRobot", &CR5Robot::enableRobot, this));
    server_tbl_.push_back(control_nh_.advertiseService("/dobot_bringup/srv/SpeedFactor", &CR5Robot::speedFactor, this));

    registerGoalCallback(boost::bind(&CR5Robot::goalHandle, this, _1));
    registerCancelCallback(boost::bind(&CR5Robot::cancelHandle, this, _1));
    start();
}

void CR5Robot::feedbackHandle(const ros::TimerEvent& tm,
                              ActionServer<control_msgs::FollowJointTrajectoryAction>::GoalHandle handle)
{
    control_msgs::FollowJointTrajectoryFeedback feedback;

    double current_joints[6];
    getJointState(current_joints);

    for (uint32_t i = 0; i < 6; i++)
    {
        feedback.joint_names.push_back(std::string("joint") + std::to_string(i + 1));
        feedback.actual.positions.push_back(current_joints[i]);
        feedback.desired.positions.push_back(goal_[i]);
    }

    handle.publishFeedback(feedback);
}

void CR5Robot::moveHandle(const ros::TimerEvent& tm,
                          ActionServer<control_msgs::FollowJointTrajectoryAction>::GoalHandle handle)
{
    control_msgs::FollowJointTrajectoryGoalConstPtr trajectory = handle.getGoal();
    const auto& points = trajectory->trajectory.points;

    if (points.empty())
    {
        timer_.stop();
        movj_timer_.stop();
        control_msgs::FollowJointTrajectoryResult result;
        result.error_code = control_msgs::FollowJointTrajectoryResult::INVALID_GOAL;
        result.error_string = "trajectory has no points";
        handle.setAborted(result);
        return;
    }

    const double elapsed = std::max(0.0, (ros::Time::now() - trajectory_start_time_).toSec());
    const double final_time = points.back().time_from_start.toSec();
    std::vector<double> command(6, 0.0);

    if (final_time > 0.0 && elapsed < final_time)
    {
        while (index_ + 1 < points.size() && points[index_ + 1].time_from_start.toSec() <= elapsed)
            index_++;

        const size_t next_index = std::min<size_t>(index_ + 1, points.size() - 1);
        const auto& p0 = points[index_];
        const auto& p1 = points[next_index];
        const double t0 = p0.time_from_start.toSec();
        const double t1 = p1.time_from_start.toSec();
        double ratio = 0.0;
        if (next_index != index_ && t1 > t0)
            ratio = std::max(0.0, std::min(1.0, (elapsed - t0) / (t1 - t0)));

        if (p0.positions.size() < 6 || p1.positions.size() < 6)
        {
            timer_.stop();
            movj_timer_.stop();
            control_msgs::FollowJointTrajectoryResult result;
            result.error_code = control_msgs::FollowJointTrajectoryResult::INVALID_GOAL;
            result.error_string = "trajectory point has fewer than 6 positions";
            handle.setAborted(result);
            return;
        }

        for (uint32_t i = 0; i < 6; i++)
            command[i] = p0.positions[i] + (p1.positions[i] - p0.positions[i]) * ratio;
    }
    else
    {
        if (points.back().positions.size() < 6)
        {
            timer_.stop();
            movj_timer_.stop();
            control_msgs::FollowJointTrajectoryResult result;
            result.error_code = control_msgs::FollowJointTrajectoryResult::INVALID_GOAL;
            result.error_string = "final trajectory point has fewer than 6 positions";
            handle.setAborted(result);
            return;
        }
        for (uint32_t i = 0; i < 6; i++)
            command[i] = points.back().positions[i];
    }

    double tmp[6];
    for (uint32_t i = 0; i < 6; i++)
        tmp[i] = command[i] * 180.0 / 3.1415926;

    try
    {
        commander_->servoJ(tmp[0], tmp[1], tmp[2], tmp[3], tmp[4], tmp[5]);
    }
    catch (const TcpClientException& err)
    {
        ROS_ERROR("%s", err.what());
        timer_.stop();
        movj_timer_.stop();
        control_msgs::FollowJointTrajectoryResult result;
        result.error_code = control_msgs::FollowJointTrajectoryResult::INVALID_GOAL;
        result.error_string = err.what();
        handle.setAborted(result);
        return;
    }

    if (final_time <= 0.0 || elapsed >= final_time)
    {
        double current_joints[6];
        getJointState(current_joints);
        bool reached = true;
        for (uint32_t i = 0; i < 6; i++)
            reached = reached && std::fabs(current_joints[i] - goal_[i]) <= goal_tolerance_;
        if (reached)
        {
            timer_.stop();
            movj_timer_.stop();
            handle.setSucceeded();
        }
    }
}

void CR5Robot::goalHandle(ActionServer<control_msgs::FollowJointTrajectoryAction>::GoalHandle handle)
{
    index_ = 0;
    auto goal = handle.getGoal();
    if (goal->trajectory.points.empty())
    {
        control_msgs::FollowJointTrajectoryResult result;
        result.error_code = control_msgs::FollowJointTrajectoryResult::INVALID_GOAL;
        result.error_string = "trajectory has no points";
        handle.setRejected(result);
        return;
    }
    if (goal->trajectory.points.back().positions.size() < 6)
    {
        control_msgs::FollowJointTrajectoryResult result;
        result.error_code = control_msgs::FollowJointTrajectoryResult::INVALID_GOAL;
        result.error_string = "final trajectory point has fewer than 6 positions";
        handle.setRejected(result);
        return;
    }

    for (uint32_t i = 0; i < 6; i++)
    {
        goal_[i] = goal->trajectory.points.back().positions[i];
    }
    trajectory_start_time_ = ros::Time::now();
    timer_ = control_nh_.createTimer(ros::Duration(1.0), boost::bind(&CR5Robot::feedbackHandle, this, _1, handle));
    movj_timer_ = control_nh_.createTimer(ros::Duration(servo_period_), boost::bind(&CR5Robot::moveHandle, this, _1, handle));
    timer_.start();
    movj_timer_.start();
    handle.setAccepted();
}

void CR5Robot::cancelHandle(ActionServer<control_msgs::FollowJointTrajectoryAction>::GoalHandle handle)
{
    timer_.stop();
    movj_timer_.stop();
    handle.setCanceled();
}

void CR5Robot::getJointState(double* point)
{
    commander_->getCurrentJointStatus(point);
}

bool CR5Robot::clearError(dobot_bringup::ClearError::Request& request, dobot_bringup::ClearError::Response& response)
{
    try
    {
        response.res = commander_->clearError() ? 0 : -1;
        return true;
    }
    catch (const std::exception& err)
    {
        response.res = -1;
        return true;
    }
}

bool CR5Robot::enableRobot(dobot_bringup::EnableRobot::Request& request, dobot_bringup::EnableRobot::Response& response)
{
    try
    {
        response.res = commander_->enableRobot() ? 0 : -1;
        return true;
    }
    catch (const std::exception& err)
    {
        response.res = -1;
        return true;
    }
}

bool CR5Robot::disableRobot(dobot_bringup::DisableRobot::Request& request, dobot_bringup::DisableRobot::Response& response)
{
    try
    {
        response.res = commander_->disableRobot() ? 0 : -1;
        return true;
    }
    catch (const std::exception& err)
    {
        response.res = -1;
        return true;
    }
}

bool CR5Robot::isEnable() const
{
    return commander_->isEnable();
}

bool CR5Robot::isConnected() const
{
    return commander_->isConnected();
}

void CR5Robot::getToolVectorActual(double* val)
{
    commander_->getToolVectorActual(val);
}

bool CR5Robot::movJ(dobot_bringup::MovJ::Request& request, dobot_bringup::MovJ::Response& response)
{
    try
    {
        commander_->movJ(request.x, request.y, request.z, request.z, request.b, request.c);
        return true;
    }
    catch (const TcpClientException& err)
    {
        ROS_ERROR("%s", err.what());
        return false;
    }
}

bool CR5Robot::movL(dobot_bringup::MovL::Request& request, dobot_bringup::MovL::Response& response)
{
    try
    {
        commander_->movL(request.x, request.y, request.z, request.z, request.b, request.c);
        return true;
    }
    catch (const TcpClientException& err)
    {
        ROS_ERROR("%s", err.what());
        return false;
    }
}

bool CR5Robot::servoJ(dobot_bringup::ServoJ::Request& request, dobot_bringup::ServoJ::Response& response)
{
    try
    {
        commander_->servoJ(request.j1, request.j2, request.j3, request.j4, request.j5, request.j6);
        return true;
    }
    catch (const TcpClientException& err)
    {
        ROS_ERROR("%s", err.what());
        return false;
    }
}

bool CR5Robot::servoP(dobot_bringup::ServoP::Request& request, dobot_bringup::ServoP::Response& response)
{
    try
    {
        commander_->servoP(request.x, request.y, request.z, request.a, request.b, request.c);
        return true;
    }
    catch (const TcpClientException& err)
    {
        ROS_ERROR("%s", err.what());
        return false;
    }
}

bool CR5Robot::relMovJ(dobot_bringup::RelMovJ::Request& request, dobot_bringup::RelMovJ::Response& response)
{
    try
    {
        commander_->relMovJ(request.offset1, request.offset2, request.offset3, request.offset4, request.offset5,
                            request.offset6);
        return true;
    }
    catch (const TcpClientException& err)
    {
        ROS_ERROR("%s", err.what());
        return false;
    }
}

bool CR5Robot::relMovL(dobot_bringup::RelMovL::Request& request, dobot_bringup::RelMovL::Response& response)
{
    try
    {
        commander_->relMovL(request.x, request.y, request.z);
        return true;
    }
    catch (const TcpClientException& err)
    {
        ROS_ERROR("%s", err.what());
        return false;
    }
}

bool CR5Robot::jointMovJ(dobot_bringup::JointMovJ::Request& request, dobot_bringup::JointMovJ::Response& response)
{
    try
    {
        commander_->jointMovJ(request.j1, request.j2, request.j3, request.j4, request.j5, request.j6);
        return true;
    }
    catch (const TcpClientException& err)
    {
        ROS_ERROR("%s", err.what());
        return false;
    }
}

bool CR5Robot::moveJog(dobot_bringup::MoveJog::Request& request, dobot_bringup::MoveJog::Response& response)
{
    try
    {
        commander_->moveJog(request.axisID);
        return true;
    }
    catch (const TcpClientException& err)
    {
        ROS_ERROR("%s", err.what());
        response.res = 0;
        return false;
    }
}

bool CR5Robot::resetRobot(dobot_bringup::ResetRobot::Request& request, dobot_bringup::ResetRobot::Response& response)
{
    try
    {
        response.res = commander_->resetRobot() ? 0 : -1;
        return true;
    }
    catch (const TcpClientException& err)
    {
        ROS_ERROR("%s", err.what());
        response.res = -1;
        return false;
    }
}

bool CR5Robot::speedFactor(dobot_bringup::SpeedFactor::Request& request, dobot_bringup::SpeedFactor::Response& response)
{
    try
    {
        response.res = commander_->speedFactor(request.ratio) ? 0 : -1;
        return true;
    }
    catch (const TcpClientException& err)
    {
        ROS_ERROR("%s", err.what());
        response.res = -1;
        return false;
    }
}
