# Campus Drive AI Viva Questions and Simple Answers

## Q1. What is ROS 2?

ROS 2 is a robotics framework used to build robot software. It helps different modules communicate using topics, services, actions, and nodes.

## Q2. What is Gazebo Sim?

Gazebo Sim is a simulator used to test robots in a virtual environment before running them on real hardware.

## Q3. Why did the project fail before the fix?

The launch file had a malformed ROS-Gazebo bridge syntax, and the simulation was started in a mode that caused the GUI crash in this environment. The sequence of world startup, bridge startup, and robot spawn was also not stable.

## Q4. What is a ROS topic?

A topic is a communication channel where nodes publish or subscribe to messages. For example, the robot publishes LaserScan on `/scan` and Twist commands on `/cmd_vel`.

## Q5. What is `/scan`?

`/scan` is the topic carrying LiDAR range data. It is used by the obstacle-avoidance logic to measure distances around the robot.

## Q6. What is `/odom`?

`/odom` gives odometry data, which tells the robot its estimated position and velocity over time.

## Q7. What is `/cmd_vel`?

`/cmd_vel` is the command topic used to send speed instructions to the robot.

## Q8. What does the obstacle-avoidance node do?

It reads the sensor data, checks whether the front is blocked, and publishes safe movement commands to avoid obstacles.

## Q9. What is the difference between obstacle avoidance and autonomous navigation?

Obstacle avoidance is local and reacts to nearby obstacles. Autonomous navigation usually includes mapping, localization, path planning, and goal reaching.

## Q10. Did the project use Nav2?

No. This project does not claim Nav2 mapping or autonomous navigation. It is a simple local obstacle-avoidance demonstration.

## Q11. What was the main verification method?

We checked live ROS topics and ran a focused unit test for the controller logic.

## Q12. What were the test results?

The controller test passed with `2 passed in 1.22s`.

## Q13. What are the limitations of this project?

It is a demonstration project. It does not include SLAM, path planning, or a full navigation stack.

## Q14. What is the next improvement?

The next improvement could be adding real obstacles in the world, waypoint navigation, or a more advanced safety controller.

## Q16. Where does the robot start and finish?

It spawns at the world origin, `(x=0, y=0)`, follows seven waypoints, and returns to `(0, 0)` to finish. The green and red markers flank this shared point in Gazebo.

## Q17. How can I drive the robot manually?

Run `ros2 run campus_robot_bringup campus_teleop.py` from a second sourced terminal. W/S drive forward or backward, A/D turn, Space stops, and Q requests autonomous control again.

## Q15. Why is it important to verify actual messages?

Because a topic name existing does not mean the robot is publishing correct data. We must inspect the actual message content and confirm the data flows.

