#!/usr/bin/env python
from __future__ import print_function

import cv2
import numpy as np
import rospy
from cv_bridge import CvBridge
from geometry_msgs.msg import PointStamped
from image_geometry import PinholeCameraModel
from sensor_msgs.msg import CameraInfo, Image
import tf2_geometry_msgs  # noqa: F401 - registers geometry conversions
import tf2_ros


DEFAULT_THRESHOLDS = {
    "red": [
        {"lower": [0, 100, 80], "upper": [10, 255, 255]},
        {"lower": [170, 100, 80], "upper": [180, 255, 255]},
    ],
    "yellow": [
        {"lower": [20, 100, 80], "upper": [35, 255, 255]},
    ],
    "green": [
        {"lower": [40, 80, 60], "upper": [85, 255, 255]},
    ],
}


class ColorDetectionError(Exception):
    """Raised when a requested color cannot be detected safely."""


class ColorDepthDetector(object):
    def __init__(self, tf_buffer=None):
        self.rgb_topic = rospy.get_param("~topics/rgb_image", "/wrist_rgbd/rgb/image_raw")
        self.depth_topic = rospy.get_param("~topics/depth_image", "/wrist_rgbd/depth/image_raw")
        self.camera_info_topic = rospy.get_param("~topics/camera_info", "/wrist_rgbd/rgb/camera_info")
        self.camera_frame = rospy.get_param("~frames/camera_frame", "wrist_rgbd_camera_link")
        self.target_frame = rospy.get_param("~frames/planning_frame", "dummy_link")
        self.image_timeout = float(rospy.get_param("~detection/image_timeout", 5.0))
        self.tf_timeout = float(rospy.get_param("~detection/tf_timeout", 2.0))
        self.min_area = float(rospy.get_param("~detection/min_area", 200.0))
        self.depth_window = int(rospy.get_param("~detection/depth_window", 5))
        self.morph_kernel = int(rospy.get_param("~detection/morph_kernel", 5))
        self.thresholds = rospy.get_param("~colors", DEFAULT_THRESHOLDS)

        self.bridge = CvBridge()
        self.camera_model = PinholeCameraModel()
        self.tf_buffer = tf_buffer or tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

    def detect(self, color_name):
        color = self._normalize_color(color_name)
        rgb_msg = rospy.wait_for_message(self.rgb_topic, Image, timeout=self.image_timeout)
        depth_msg = rospy.wait_for_message(self.depth_topic, Image, timeout=self.image_timeout)
        info_msg = rospy.wait_for_message(self.camera_info_topic, CameraInfo, timeout=self.image_timeout)

        bgr = self.bridge.imgmsg_to_cv2(rgb_msg, desired_encoding="bgr8")
        depth = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding="passthrough")
        self.camera_model.fromCameraInfo(info_msg)

        mask = self._make_mask(bgr, color)
        contour = self._largest_contour(mask, color)
        u, v, area = self._contour_centroid(contour)
        depth_m = self._median_depth(depth, u, v)
        camera_point = self._project_to_camera(info_msg, u, v, depth_m)
        target_point = self._transform_point(camera_point)

        return {
            "color": color,
            "u": u,
            "v": v,
            "area": area,
            "depth_m": depth_m,
            "camera_point": camera_point,
            "target_point": target_point,
        }

    def _normalize_color(self, color_name):
        color = color_name.strip().lower()
        if color not in self.thresholds:
            raise ColorDetectionError("Unsupported color '%s'. Use red, yellow, or green." % color_name)
        return color

    def _make_mask(self, bgr, color):
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        combined = None
        for hsv_range in self.thresholds[color]:
            lower = np.array(hsv_range["lower"], dtype=np.uint8)
            upper = np.array(hsv_range["upper"], dtype=np.uint8)
            mask = cv2.inRange(hsv, lower, upper)
            combined = mask if combined is None else cv2.bitwise_or(combined, mask)

        if self.morph_kernel > 1:
            kernel = np.ones((self.morph_kernel, self.morph_kernel), np.uint8)
            combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
            combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
        return combined

    def _largest_contour(self, mask, color):
        result = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = result[-2]
        if not contours:
            raise ColorDetectionError("No %s blob found in RGB image." % color)
        contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(contour)
        if area < self.min_area:
            raise ColorDetectionError(
                "Largest %s blob area %.1f is below min_area %.1f." % (color, area, self.min_area)
            )
        return contour

    def _contour_centroid(self, contour):
        area = cv2.contourArea(contour)
        moments = cv2.moments(contour)
        if abs(moments["m00"]) > 1e-6:
            u = int(moments["m10"] / moments["m00"])
            v = int(moments["m01"] / moments["m00"])
        else:
            x, y, w, h = cv2.boundingRect(contour)
            u = int(x + w / 2)
            v = int(y + h / 2)
        return u, v, area

    def _median_depth(self, depth_image, u, v):
        depth = np.asarray(depth_image)
        radius = max(1, int(self.depth_window))
        height, width = depth.shape[:2]
        x0 = max(0, u - radius)
        x1 = min(width, u + radius + 1)
        y0 = max(0, v - radius)
        y1 = min(height, v + radius + 1)
        patch = depth[y0:y1, x0:x1].astype(np.float32)

        if depth.dtype == np.uint16:
            patch = patch / 1000.0

        valid = patch[np.isfinite(patch)]
        valid = valid[valid > 0.0]
        if valid.size == 0:
            raise ColorDetectionError("No valid depth near detected pixel (%d, %d)." % (u, v))

        depth_m = float(np.median(valid))
        if not np.isfinite(depth_m) or depth_m <= 0.0:
            raise ColorDetectionError("Invalid median depth %.4f m." % depth_m)
        return depth_m

    def _project_to_camera(self, info_msg, u, v, depth_m):
        ray = self.camera_model.projectPixelTo3dRay((u, v))
        if abs(ray[2]) < 1e-9:
            raise ColorDetectionError("Camera projection ray has near-zero z component.")
        scale = depth_m / ray[2]

        point = PointStamped()
        point.header.stamp = rospy.Time(0)
        point.header.frame_id = info_msg.header.frame_id or self.camera_frame
        point.point.x = ray[0] * scale
        point.point.y = ray[1] * scale
        point.point.z = ray[2] * scale
        return point

    def _transform_point(self, camera_point):
        try:
            return self.tf_buffer.transform(
                camera_point,
                self.target_frame,
                rospy.Duration(self.tf_timeout),
            )
        except Exception as exc:
            raise ColorDetectionError(
                "Could not transform %s to %s: %s"
                % (camera_point.header.frame_id, self.target_frame, exc)
            )
