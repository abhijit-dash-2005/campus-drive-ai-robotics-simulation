cmake_minimum_required(VERSION 3.8)
project(campus_robot_bringup)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(std_msgs REQUIRED)

install(
  DIRECTORY models worlds launch
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
    scripts/lidar_avoid.py
    scripts/campus_autonomy.py
    scripts/campus_evaluation.py
    scripts/campus_teleop.py
    scripts/campus_status_display.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
