# Campus Drive AI Robotics Simulation

A ROS 2 campus robot simulation for Ubuntu 24.04, ROS 2 Jazzy, and Gazebo Harmonic (Gazebo Sim 8). A blue, car-style differential-drive robot follows a programmed S-shaped route through a campus courtyard, reads 2D LiDAR and wheel odometry, and reacts to nearby obstacles with a rule-based controller.

This project currently uses hand-written waypoint and LiDAR rules. It does **not** use a trained AI/ML model, SLAM, or Nav2. “AI” is retained in the project title; the implementation is a robotics simulation prototype.

## Current project features

- A campus courtyard with four building models, a Centurion University sign on the front-facing building, paths, lawn areas, trees, and planters.
- Three fixed obstacle blocks arranged across the route.
- A blue car-style differential-drive robot with a planar LiDAR and wheel odometry.
- A green start pad at **(-3.8, 1.7)** and a red destination pad at **(3.8, 1.7)** in Gazebo world coordinates (7.6 m apart).
- A nine-target S-shaped waypoint route that passes below the first block, above the middle block, and below the third block before reaching the red destination.
- Reactive obstacle handling based on forward LiDAR distance and side clearance.
- An in-world `SIMULATION STARTED` sign that changes to `ROUTE FINISHED` after the controller reports success.
- Optional keyboard teleoperation, ROS topic inspection, and CSV evaluation output summarized by five charts.

## Software

| Component | Role |
| --- | --- |
| Ubuntu 24.04 | Operating system |
| ROS 2 Jazzy | ROS nodes and topic communication |
| Gazebo Harmonic / Gazebo Sim 8 | Physics-based world, robot, and LiDAR simulation |
| Python 3 / `rclpy` | Waypoint control, obstacle response, status display, evaluation, and teleoperation |
| SDF | Gazebo world and robot model description |
| `ros_gz_bridge` | Connects Gazebo messages and ROS 2 topics/services |
| `colcon`, `ament_cmake` | Builds the ROS 2 workspace |

## Workspace layout

```text
campus_ws/
├── src/
│   ├── campus_robot_bringup/
│   │   ├── launch/campus_sim.launch.py
│   │   ├── models/campus_robot/model.sdf
│   │   ├── scripts/campus_autonomy.py
│   │   ├── scripts/campus_evaluation.py
│   │   ├── scripts/campus_status_display.py
│   │   ├── scripts/campus_teleop.py
│   │   └── worlds/campus.world
│   └── campus_robot_description/
├── docs/                 # Project report and viva guide
├── graphs/               # Five summary charts, including two simple bar charts
├── tools/                # Summary chart generator
└── results/               # Evaluation CSV files
```

## Build and launch

Open one terminal and run:

```bash
cd ~/Desktop/campus_ws && source /opt/ros/jazzy/setup.bash && colcon build --symlink-install && source install/setup.bash && ros2 launch campus_robot_bringup campus_sim.launch.py
```

Keep that terminal open while Gazebo runs. The launch starts one isolated Gazebo partition and ROS domain, bridges the sensor/control topics, spawns the robot at the green pad, and starts navigation, status display, and evaluation. The robot starts autonomously when odometry and LiDAR messages are available. When finished, press **Ctrl+C once** in the launch terminal.

If `ros2` is not found in another terminal, source ROS and the workspace in that terminal too:

```bash
source /opt/ros/jazzy/setup.bash && source ~/Desktop/campus_ws/install/setup.bash
```

## Route and controller

The route starts at world pose **(-3.8, 1.7)**, first lines up at **(-3.2, 1.7)**, passes around three blocks centered at **(-2.5, 1.7)**, **(0, 1.7)**, and **(2.5, 1.7)**, and finishes at **(3.8, 1.7)**. Waypoint targets in `campus_autonomy.py` are:

1. (-3.2, 1.70)
2. (-3.2, 0.65)
3. (-1.35, 0.65)
4. (-1.35, 2.75)
5. (1.35, 2.75)
6. (1.35, 0.65)
7. (3.2, 0.65)
8. (3.2, 1.70)
9. (3.8, 1.70)

The node captures the spawn odometry as its origin, converts the world targets into that local odometry frame, and advances within a 0.12 m waypoint tolerance. It turns toward the active target and then drives forward. When the forward LiDAR sector is under the configured 0.65 m avoidance threshold, it compares left/right sectors and turns toward the side with more measured clearance. LiDAR returns shorter than 0.40 m are ignored by the controller to reduce robot-body self-echoes. A 180-second watchdog stops a run that does not complete.

The paved S-shaped road with dashed center markings follows the fixed roadmap for this world. Local LiDAR handling supplements it; it does not calculate a new global path or guarantee avoidance for arbitrary moving obstacles.

## ROS topics

| Topic | Message | Purpose |
| --- | --- | --- |
| `/scan` | `sensor_msgs/msg/LaserScan` | 360-degree simulated LiDAR ranges |
| `/odom` | `nav_msgs/msg/Odometry` | Robot pose and velocity estimate |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Requested linear and angular speeds |
| `/campus_navigation/status` | `std_msgs/msg/String` | Active waypoint and distance, or completion state |
| `/campus_navigation/obstacle_detected` | `std_msgs/msg/Bool` | Latches true after a valid nearby LiDAR return under 1.8 m |
| `/campus_navigation/succeeded` | `std_msgs/msg/Bool` | Route-completion signal used by the display and evaluator |
| `/campus_navigation/mode` | `std_msgs/msg/String` | `auto` or `manual` control selection |

To inspect topics while the simulation is running, use the `ROS_DOMAIN_ID` printed by the launch terminal in a second terminal:

```bash
source /opt/ros/jazzy/setup.bash && source ~/Desktop/campus_ws/install/setup.bash && export ROS_DOMAIN_ID=123 && ros2 topic list
```

Print one status message:

```bash
source /opt/ros/jazzy/setup.bash && source ~/Desktop/campus_ws/install/setup.bash && export ROS_DOMAIN_ID=123 && ros2 topic echo --once /campus_navigation/status
```

Before running, replace `123` with the numeric ROS_DOMAIN_ID printed by the launch terminal. `--once` prints one message and returns to the prompt.

## Interactive controls

Use Gazebo's pause and play controls and mouse camera controls to present the simulation. For keyboard control, open a second terminal, source the same ROS domain and workspace, then run:

```bash
source /opt/ros/jazzy/setup.bash && source ~/Desktop/campus_ws/install/setup.bash && export ROS_DOMAIN_ID=123 && ros2 run campus_robot_bringup campus_teleop.py
```

Hold **W**/**I** to drive forward, **S**/**K** to reverse, **A**/**J** to turn left, **D**/**L** to turn right; release a key or press **Space** to stop. Press **Q** to request autonomous mode again. Teleoperation is optional; it can interrupt an autonomous demonstration if used during the route.

## Evaluation and current recorded run

`campus_evaluation.py` writes `results/campus_evaluation.csv` on route completion and when the node shuts down. An incomplete run is recorded with `route_succeeded=False`. It records elapsed time, odometry-based path length, minimum raw LiDAR return overall and in a ±30-degree forward sector, scan count, scans with a raw return under 1 m, zero-velocity command samples, and the route-success flag. These are measurements from one simulation run, not averages.

The latest saved successful run in the workspace records:

| Measure | Recorded value |
| --- | ---: |
| Route result | Succeeded (`True`) |
| Elapsed time | 146.62 s |
| Odometry path length | 13.056 m |
| Minimum raw LiDAR return, all directions | 0.250 m |
| Minimum raw forward return, ±30 degrees | 0.537 m |
| LiDAR scans | 1,113 |
| Scans with a raw return under 1 m | 1,011 |
| Zero-velocity command samples | 10 |

The five charts in `graphs/` summarize every available record from `results/campus_evaluation.csv` and `results/campus_evaluation_verified.csv`: route performance, raw LiDAR ranges, sensor/controller activity, elapsed time by run, and odometry-estimated distance by run. The two bar charts display each recorded run separately, with units and completion status; they are not averages. To regenerate them in an environment with Matplotlib, run `python3 tools/generate_summary_graphs.py` from the workspace root. The raw minimum LiDAR values can include returns from the robot's own body. These raw-distance metrics are not verified collision-clearance measurements, and “near-obstacle scans” are scan counts rather than distinct obstacle encounters. Two successful records do not establish repeatability or physical-robot safety.

## Documentation

- [`docs/PROJECT_REPORT.md`](docs/PROJECT_REPORT.md) — project design, implementation, latest recorded run, limitations, and future work.
- [`docs/viva_questions.md`](docs/viva_questions.md) — short explanations of the system and likely demonstration questions.
- [`Campus_Drive_AI_Project_Demonstration.docx`](Campus_Drive_AI_Project_Demonstration.docx) — detailed nine-page project demonstration report and procedure.

## Limitations and next steps

This is a simulation prototype. It uses known fixed waypoint coordinates and a local clearance rule; it does not include SLAM, a global planner, Nav2, learned perception, dynamic obstacle tracking, or real-robot validation. The next useful engineering steps are repeated runs, collision/contact instrumentation, and then map-based localization and navigation if the project is extended.

## Rebuild after source changes

```bash
cd ~/Desktop/campus_ws && source /opt/ros/jazzy/setup.bash && colcon build --symlink-install && source install/setup.bash
```
