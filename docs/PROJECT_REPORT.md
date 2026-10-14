# Campus Drive AI — Project Report

**Project type:** ROS 2 mobile robotics simulation  
**Platform:** Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic / Gazebo Sim 8  
**Student:** [Add your name]  
**Department / college:** [Add your department and college]  
**Date:** [Add submission date]

## Abstract

Campus Drive AI is a simulated differential-drive robot that navigates a small campus courtyard. The robot receives 2D LiDAR scans and wheel odometry, follows a sequence of campus waypoints, and uses a reactive obstacle-avoidance rule to change its motion when an obstacle is detected ahead. A separate evaluation node records route duration, odometry-based path length, LiDAR clearance, scan counts, stop commands, and route completion in a CSV file.

The project demonstrates the main ROS 2 robotics workflow: simulation, sensor data, velocity commands, navigation logic, and measurable evaluation. The current controller is a beginner-level waypoint and reactive-avoidance implementation. It is not a learned AI model or the full Nav2 stack.

## Problem statement

A mobile robot in a campus-like environment must move between destinations while using its sensors to respond to nearby obstacles. The project provides a repeatable simulation in which the robot's sensor topics, movement commands, route progress, and evaluation metrics can be inspected.

## Objectives

1. Create a campus courtyard world in Gazebo.
2. Simulate a differential-drive robot with a 360-degree LiDAR and odometry.
3. Connect Gazebo sensor and control messages to ROS 2 topics.
4. Navigate a set of campus waypoints with a simple reactive obstacle-avoidance layer.
5. Record route performance in a CSV report.

## System architecture

```mermaid
flowchart LR
    W[Campus world in Gazebo] --> R[Diff-drive robot]
    R --> L[LiDAR /scan]
    R --> O[Odometry /odom]
    L --> A[Waypoint and obstacle controller]
    O --> A
    A --> C[/cmd_vel]
    C --> R
    L --> E[Evaluation recorder]
    O --> E
    C --> E
    A --> S[/campus_navigation/status and succeeded]
    E --> F[results/campus_evaluation.csv]
```

### Main software components

- **`campus_robot_description`**: robot description package.
- **`campus_robot_bringup`**: Gazebo world, robot model, launch file, navigation node, and evaluator.
- **Gazebo Sim**: physics and sensor simulation.
- **ROS-Gazebo bridge**: connects `/scan`, `/odom`, and `/cmd_vel` between Gazebo and ROS 2.

## Robot and environment

The purple east-side campus building is labeled **CENTURION UNIVERSITY** on its courtyard-facing front wall.

The simulated robot is a two-wheel differential-drive base. Its model includes a planar LiDAR and a Gazebo DiffDrive system. The campus world contains paved pedestrian paths, lawn verges, four buildings with facade details, four trees, and two courtyard planters. The trees sit outside the seven-waypoint path. The current waypoint list is defined in `src/campus_robot_bringup/scripts/campus_autonomy.py` and routes through the upper courtyard. The robot starts at world coordinates **(0, 0)** and returns to **(0, 0)** after waypoint 7. The Gazebo world places a green start marker and red finish marker on either side of this shared point; they are visual-only and named in the Entity Tree.

## Navigation method

The controller stores a sequence of seven 2D waypoint coordinates. At each control step it:

1. Reads the robot position from `/odom` and LiDAR ranges from `/scan`.
2. Computes the distance and heading error to the current waypoint.
3. Rotates toward the waypoint before moving forward.
4. Checks the forward LiDAR sector. If an obstacle is close, it chooses a turn direction based on side-sector clearance and slows or stops forward motion.
5. Marks a waypoint reached when the robot is within the configured distance threshold, then proceeds to the next goal.
6. Publishes route progress on `/campus_navigation/status` and publishes success on `/campus_navigation/succeeded` when all goals are reached.

This is a small reactive controller intended for learning and demonstration. It does not build a map, localize using SLAM, or use Nav2's global and local planners.

## Interactive controls
The robot uses a blue vehicle-style body shell. A large visual sign in the Gazebo courtyard changes from **STARTED** to **FINISHED** when the route success signal arrives. The ROS-Gazebo bridge provides the create and remove services used to change the sign.


The launch opens Gazebo with its graphical client. The user can pause or resume the simulation and manipulate the camera or select entities. Autonomous waypoint following starts by default. For keyboard teleoperation, run `ros2 run campus_robot_bringup campus_teleop.py` in a second sourced terminal. W/S move forward/reverse, A/D turn, Space stops, and Q requests autonomous mode again. The autonomy node listens to `/campus_navigation/mode` so both controllers do not command the robot at the same time.

## ROS topics

| Topic | Message type | Use |
| --- | --- | --- |
| `/scan` | `sensor_msgs/msg/LaserScan` | LiDAR ranges for obstacle detection |
| `/odom` | `nav_msgs/msg/Odometry` | Robot pose and velocity estimate |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Linear and angular velocity commands |
| `/campus_navigation/status` | `std_msgs/msg/String` | Current waypoint and remaining distance |
| `/campus_navigation/succeeded` | `std_msgs/msg/Bool` | Route completion signal |
| `/campus_navigation/mode` | `std_msgs/msg/String` | Select `auto` or `manual` control |

## Evaluation method

The evaluation node subscribes to odometry, LiDAR, velocity commands, and route success. It writes `results/campus_evaluation.csv` with elapsed time, accumulated odometry path length, minimum LiDAR return overall and in the forward 60-degree field, scan count, near-obstacle scan count, stop-command count, and route success.

### Verified simulation run

The latest completed seven-waypoint run recorded:

| Metric | Result |
| --- | ---: |
| Route completion | Success (7/7 waypoints) |
| Elapsed time | 277.30 s |
| Odometry path length | 18.883 m |
| Minimum LiDAR return | 0.736 m |
| Minimum forward LiDAR return | 0.736 m |
| LiDAR scans | 2,772 |
| Stop commands | 10 |

These values describe one simulation run. Results can vary with changes to the controller, world, or simulation performance. The verified run is preserved as `results/campus_evaluation_verified.csv`. The standard `results/campus_evaluation.csv` is overwritten on each run and may reflect a later interrupted attempt.

## How to run

From a terminal:

```bash
cd ~/Desktop/campus_ws && source /opt/ros/jazzy/setup.bash && source install/setup.bash && ros2 launch campus_robot_bringup campus_sim.launch.py
```

The launch runs the simulation server headlessly. Wait for `Campus route complete` to appear. Press Ctrl+C once to stop it. The CSV is written to `results/campus_evaluation.csv`.

To check route progress from a second terminal:

```bash
source /opt/ros/jazzy/setup.bash && source ~/Desktop/campus_ws/install/setup.bash && ros2 topic echo --once /campus_navigation/status
```

## Limitations and future work

- This implementation uses hand-coded waypoint and reactive-avoidance rules, not machine learning.
- It is a simulation demonstration, not a safety-certified system for a physical robot.
- Evaluation is based on simulated odometry and LiDAR; it does not include repeated statistical trials or ground-truth tracking.
- A logical next upgrade is Nav2 with a mapped environment, localization, a global planner, and a local obstacle-avoidance planner.
- Further work could add an IMU or camera, more varied obstacle layouts, repeated trials, plots of the CSV metrics, and automated collision or clearance checks.

## Reproducibility notes

Source files are in `src/`. After changing them, rebuild with:

```bash
cd ~/Desktop/campus_ws && source /opt/ros/jazzy/setup.bash && colcon build --symlink-install && source install/setup.bash
```

The project README contains the shorter quick-start guide. The evaluation CSV is regenerated on each run, so copy it elsewhere before a new run if you need to keep a previous trial.


## Updated map evaluation note

The saved verified CSV, and graphs derived from it, describe the earlier simpler world. Those previous measurements predate the new map scenery and tree obstacles. Re-run the updated world before reporting performance metrics as results for this map.
