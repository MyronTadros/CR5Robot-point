#!/usr/bin/env python
from __future__ import print_function

import argparse
import sys

import rospy

from cr5_color_pointing.perception import ColorDepthDetector, ColorDetectionError


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Detect one colored box with the CR5 wrist RGB-D camera.")
    parser.add_argument("color", nargs="?", default=None, help="red, yellow, or green")
    args, _ = parser.parse_known_args(argv)
    return args


def main():
    args = parse_args(rospy.myargv(argv=sys.argv)[1:])
    rospy.init_node("detect_color_once")

    color = args.color or rospy.get_param("~color", "red")
    detector = ColorDepthDetector()

    try:
        result = detector.detect(color)
    except (rospy.ROSException, ColorDetectionError) as exc:
        rospy.logerr("Detection failed: %s", exc)
        return 1

    camera_point = result["camera_point"]
    target_point = result["target_point"]
    print("Detected %s" % result["color"])
    print("  pixel: u=%d v=%d area=%.1f" % (result["u"], result["v"], result["area"]))
    print("  depth: %.4f m" % result["depth_m"])
    print(
        "  camera point [%s]: x=%.4f y=%.4f z=%.4f"
        % (
            camera_point.header.frame_id,
            camera_point.point.x,
            camera_point.point.y,
            camera_point.point.z,
        )
    )
    print(
        "  target point [%s]: x=%.4f y=%.4f z=%.4f"
        % (
            target_point.header.frame_id,
            target_point.point.x,
            target_point.point.y,
            target_point.point.z,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
