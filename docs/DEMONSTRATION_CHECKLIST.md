# Project Demonstration Checklist

## Before the presentation

- [ ] Use Ubuntu 24.04 with ROS 2 Jazzy and Gazebo Harmonic installed.
- [ ] Confirm `~/Desktop/campus_ws` contains `src/`, `install/`, `results/`, and `graphs/`.
- [ ] Close any old Gazebo or ROS launch sessions before starting.
- [ ] Have a second terminal ready for topic inspection.

## Launch

```bash
cd ~/Desktop/campus_ws && source /opt/ros/jazzy/setup.bash && colcon build --symlink-install && source install/setup.bash && ros2 launch campus_robot_bringup campus_sim.launch.py
```

Keep this terminal open and note the printed `ROS_DOMAIN_ID`.

## Show the simulation

- Show the blue vehicle-style robot at the green start pad **(-3.8, 1.7)**.
- Show the red destination at **(3.8, 1.7)** and explain the 7.6 m endpoint spacing.
- Point out all three fixed blocks and follow the paved road with dashed center markings: below block 1, above block 2, below block 3.
- Show the `CENTURION UNIVERSITY` sign on the courtyard-facing wall.
- Explain that the active autonomy implementation is rule-based, not trained AI/ML.
- Let the route run until the display says **ROUTE FINISHED**.

## Verify topics in a second terminal

Replace `123` in the command below with the number printed in the launch terminal:

```bash
source /opt/ros/jazzy/setup.bash && source ~/Desktop/campus_ws/install/setup.bash && export ROS_DOMAIN_ID=123 && ros2 topic list
```

Inspect a single message at a time:

```bash
source /opt/ros/jazzy/setup.bash && source ~/Desktop/campus_ws/install/setup.bash && export ROS_DOMAIN_ID=123 && ros2 topic echo --once /campus_navigation/status
```

Other useful topics are `/scan`, `/odom`, `/cmd_vel`, `/campus_navigation/obstacle_detected`, and `/campus_navigation/succeeded`.

## Show results and shut down

- Open `results/campus_evaluation.csv` and explain each metric briefly.
- Show the five summary plots in `graphs/`: route performance, LiDAR ranges, sensor/controller activity, run time, and distance traveled. Explain that each chart represents individual CSV records, not averages.
- State that the latest saved successful run is a single run: 146.62 s, 13.056 m odometry path, 1,113 scans, and route success `True`.
- Explain that minimum raw LiDAR values may include self-echoes and do not certify collision clearance.
- Press Ctrl+C once in the launch terminal after the demonstration.

## Optional manual control

Start the teleoperation node in another terminal using the same ROS domain. W/I moves forward, S/K reverses, A/J turns left, D/L turns right, Space stops, and Q requests auto mode. Avoid using teleoperation during the autonomous result run.
