# Campus Drive AI — ROS 2 Campus Robot Simulation

A beginner-friendly campus robotics project for Ubuntu 24.04, ROS 2 Jazzy, and Gazebo Harmonic (Gazebo Sim 8). A differential-drive robot traverses a small campus courtyard using wheel odometry and a 2D LiDAR. A waypoint controller steers around obstacles, and an evaluation node saves run metrics to CSV.

## Project contents

- `src/campus_robot_bringup/worlds/campus.world` — courtyard paths, lawns, four campus buildings with windows, trees, and planters.
- `src/campus_robot_bringup/models/campus_robot/model.sdf` — differential-drive robot with LiDAR and odometry.
- `src/campus_robot_bringup/launch/campus_sim.launch.py` — starts Gazebo, ROS-Gazebo bridges, robot spawning, navigation, and evaluation.
- `src/campus_robot_bringup/scripts/campus_autonomy.py` — waypoint following and reactive LiDAR obstacle avoidance.
- `src/campus_robot_bringup/scripts/campus_evaluation.py` — records route duration, traveled distance, LiDAR clearance, scans, and stop commands.
- `src/campus_robot_description` — robot description package.
- `results/campus_evaluation.csv` — most recent attempt; each run overwrites this file.
- `results/campus_evaluation_verified.csv` — preserved metrics from the completed 7-waypoint route.

## Build and run

Run this one-line command from a terminal:

```bash
cd ~/Desktop/campus_ws && source /opt/ros/jazzy/setup.bash && colcon build --symlink-install && source install/setup.bash && ros2 launch campus_robot_bringup campus_sim.launch.py
```

The launch opens the Gazebo GUI and starts the simulation with autonomous waypoint driving. Keep the terminal open while the robot navigates. Press Ctrl+C once to stop the simulation. The evaluator writes its CSV when the route completes or when the launch is stopped.

## Watch progress and inspect topics

Open a second terminal and run:

```bash
source /opt/ros/jazzy/setup.bash && source ~/Desktop/campus_ws/install/setup.bash && ros2 topic echo --once /campus_navigation/status
```

For a live stream, remove `--once`. A completed route prints `Campus route complete` in the launch terminal and publishes `true` on `/campus_navigation/succeeded`.

| Topic | ROS message | Purpose |
| --- | --- | --- |
| `/scan` | `sensor_msgs/msg/LaserScan` | 360-degree LiDAR ranges |
| `/odom` | `nav_msgs/msg/Odometry` | Robot position and velocity estimate |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Velocity commands to the simulated robot |
| `/campus_navigation/status` | `std_msgs/msg/String` | Current waypoint and distance |
| `/campus_navigation/succeeded` | `std_msgs/msg/Bool` | Route completion signal |

## Route start and finish
The robot has a blue car-style shell with a raised cabin, windshield, headlights, and bumpers; its LiDAR and drive base remain functional. A large in-world board displays **STARTED** at launch and changes to **FINISHED** when all seven waypoints are reached.


The robot spawns at the world origin **(x=0, y=0)**, drives the seven waypoint route, and returns to **(x=0, y=0)** to finish. The world shows a green `start_marker` and a red `finish_marker` flanking this shared point; they are visual-only markers. Select them in Gazebo's Entity Tree to identify them.

## Interactive manual driving

The normal launch starts autonomous waypoint driving. To take manual control, open a second terminal while the simulation is running and use:

```bash
source /opt/ros/jazzy/setup.bash && source ~/Desktop/campus_ws/install/setup.bash && ros2 run campus_robot_bringup campus_teleop.py
```

In that terminal, hold **W** to move forward, **S** to reverse, **A**/**D** to turn, and **Space** to stop. Releasing a key stops motion. Press **Q** to return control to the autonomous waypoint controller. In the Gazebo window, use the pause/play buttons and mouse to orbit, pan, and zoom the view; select objects in the Entity Tree.

## Campus map

The purple east-side campus building displays a prominent **CENTURION UNIVERSITY** sign on its courtyard-facing front wall.


The Gazebo world now has a paved T-shaped pedestrian route, green verges, four campus buildings with windows and entrances, four trees, and the two courtyard planters. The seven-waypoint route remains on the open central path and returns to its starting position. The tree trunks are added as LiDAR-visible obstacles outside the programmed route.

The saved successful evaluation and graph files came from the earlier, simpler world. Run the updated map before reporting new performance figures; each new run overwrites `results/campus_evaluation.csv`.

## Navigation and obstacle avoidance

The current source defines **7 campus waypoints**. The controller first turns toward a goal, then uses the forward LiDAR sector to select an avoidance turn. It stops forward motion when the forward clearance is below 0.60 m and creeps while turning at larger distances. This is a small educational reactive controller, not the Nav2 navigation stack or a safety-certified system.

## Evaluation output

The file `results/campus_evaluation.csv` contains:

- `elapsed_seconds` — duration of the evaluation run.
- `path_length_m` — distance accumulated from odometry.
- `minimum_obstacle_m` — closest valid LiDAR return in any direction.
- `minimum_front_obstacle_m` — closest valid LiDAR return within 30 degrees of the forward direction.
- `scan_count`, `near_obstacle_scans`, and `stop_commands` — sensor and controller counts.
- `route_succeeded` — whether the route completion signal was received.

A previous version of the world completed **7/7** waypoints successfully (18.883 m in 277.30 seconds, minimum forward LiDAR return 0.736 m). Those measurements predate the newly added trees and map details and should not be treated as verification of the updated environment. Re-run the simulation to collect current metrics.

## Rebuild after editing source files

```bash
cd ~/Desktop/campus_ws && source /opt/ros/jazzy/setup.bash && colcon build --symlink-install && source install/setup.bash
```

## Limitations

This is a Gazebo simulation using a simple waypoint controller. The current obstacle response needs further tuning and route verification before any real-robot use. The graphical Gazebo client opens with the simulation.
