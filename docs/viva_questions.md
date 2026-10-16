# Campus Drive AI Viva Questions and Answers

## Project overview

### 1. What is Campus Drive AI?
It is a ROS 2 and Gazebo simulation of a small differential-drive campus robot. It follows a fixed S-shaped route around three blocks using wheel odometry and LiDAR.

### 2. Does the current project use machine learning?
No. The current controller uses hand-written waypoint-following and LiDAR clearance rules. There is no trained model, SLAM, or Nav2 integration.

### 3. What is the main project objective?
To demonstrate a complete simulated robotics loop: sensing, waypoint control, obstacle response, motion in Gazebo, visible route status, and performance recording.

### 4. What is the starting point and destination?
The robot starts at the green pad at world coordinate (-3.8, 1.7) m and aims for the red pad at (3.8, 1.7) m. They are 7.6 m apart. The S-shaped path travels around the three blocks in between.

### 5. How many route waypoints are used?
The controller uses nine target points. These shape the S-route: pass below block 1, above block 2, below block 3, then reach the destination.

## Software and communication

### 6. Which technologies are used?
Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic (Gazebo Sim 8), Python 3 with `rclpy`, SDF, `ros_gz_bridge`, and `colcon`.

### 7. What is ROS 2?
ROS 2 is a robotics software framework that lets independent nodes communicate through topics and other interfaces.

### 8. What is Gazebo used for?
Gazebo simulates the campus world, robot physics, and LiDAR sensor data.

### 9. What is a ROS topic?
A topic is a named stream of messages. For example, `/scan` carries LiDAR messages and `/cmd_vel` carries requested robot velocity.

### 10. What does `ros_gz_bridge` do?
It translates messages between Gazebo Transport and ROS 2 so the ROS controller can read simulated sensors and send commands to the Gazebo robot.

### 11. What are the important topics?
`/scan` (LiDAR), `/odom` (pose and velocity estimate), `/cmd_vel` (motion command), `/campus_navigation/status` (route progress), `/campus_navigation/obstacle_detected` (nearby-object flag), `/campus_navigation/succeeded` (route completion), and `/campus_navigation/mode` (automatic or manual control).

## Navigation and sensing

### 12. How does the robot follow the route?
The controller reads `/odom`, computes distance and heading to the next target, turns toward it, and drives forward. It advances to the next target within 0.12 m.

### 13. How does obstacle avoidance work?
The node checks the forward LiDAR sector. Below a 0.65 m forward threshold it compares left and right clearances and turns toward the clearer side; if neither side has enough clearance it stops. It ignores returns below 0.40 m to reduce robot-body echoes.

### 14. Does the robot calculate a new route around any obstacle?
No. The paved S-shaped road with dashed center markings is programmed for the three fixed blocks in this world. The LiDAR response is local and reactive; it does not provide global planning or a guarantee for arbitrary moving obstacles.

### 15. Why can a robot move backward in the simulator?
The autonomous controller publishes nonnegative forward speed, but the optional teleoperation node explicitly supports reverse with S/K. A backward movement can also be caused by differential-drive axis or frame configuration. For the demonstration, use one active launch, confirm the correct spawn pose and route, and avoid manual teleoperation during the autonomous segment.

### 16. What do the green and red markers mean?
Green marks the spawn/start location; red marks the separate destination. They are visual markers in the Gazebo world.

### 17. What does the in-world status sign show?
The display node spawns a “SIMULATION STARTED” sign when Gazebo is ready, then replaces it with “ROUTE FINISHED” after the route-success topic becomes true.

## Evaluation and limitations

### 18. What does the evaluator measure?
Elapsed time, odometry-based path length, minimum raw LiDAR return overall and in a ±30-degree forward sector, scan count, scans with raw range under 1 m, zero-velocity command samples, and route success.

### 19. What was the latest saved successful result?
The latest saved CSV reports success, 146.62 seconds, 13.056 m path length, 1,113 scans, 1,011 scans with a raw return under 1 m, and 10 zero-velocity command samples. The minimum raw ranges were 0.250 m overall and 0.537 m in the forward sector.

### 20. Does the 0.250 m reading prove the robot nearly collided?
Not by itself. The evaluator records raw LiDAR ranges and may include echoes from the robot's own body. These values are not verified collision-clearance measurements. Collision/contact instrumentation and controlled tests would be needed for a stronger claim.

### 21. Is this ready to control a real robot?
No. It is an educational simulation prototype. It has not been safety-validated on physical hardware and lacks mapping, localization, global planning, and repeated-run statistics.

### 22. What is a sensible next improvement?
Add collision/contact monitoring and run multiple repeatable trials. After establishing that baseline, add mapping/localization and a navigation planner such as Nav2 if the scope requires it.

## Demonstration quick sequence

1. Build and launch from `~/Desktop/campus_ws` using the README command.
2. Show the campus world, the three blocks, the paved S-shaped road with dashed center markings, green start, red destination, robot, and university sign.
3. In a second terminal, use the `ROS_DOMAIN_ID` printed at launch and inspect `/scan`, `/odom`, and `/campus_navigation/status`.
4. Let the autonomous route finish; show the in-world completion sign and `results/campus_evaluation.csv`.
