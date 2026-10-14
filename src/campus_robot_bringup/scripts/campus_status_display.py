#!/usr/bin/env python3
"""Show STARTED / FINISHED signs inside the Gazebo world."""
from pathlib import Path

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import DeleteEntity, SpawnEntity
from std_msgs.msg import Bool


class CampusStatusDisplay(Node):
    def __init__(self):
        super().__init__('campus_status_display')
        self.spawn_client = self.create_client(SpawnEntity, '/world/campus_world/create')
        self.delete_client = self.create_client(DeleteEntity, '/world/campus_world/remove')
        self.create_subscription(Bool, '/campus_navigation/succeeded', self.done_cb, 10)
        self.sign_dir = Path(get_package_share_directory('campus_robot_bringup')) / 'models' / 'status_signs'
        self.done = False
        self.phase = 'waiting'
        self.create_timer(0.5, self.update)

    def done_cb(self, msg):
        if msg.data:
            self.done = True

    def update(self):
        if self.phase == 'waiting':
            if not self.spawn_client.service_is_ready():
                return
            self.spawn_sign('started.sdf', 'started')
        elif self.phase == 'started' and self.done:
            if self.delete_client.service_is_ready():
                request = DeleteEntity.Request()
                request.entity = Entity(name='campus_status_sign', type=Entity.MODEL)
                self.phase = 'removing'
                future = self.delete_client.call_async(request)
                future.add_done_callback(self.removed)
        elif self.phase == 'removed' and self.done:
            self.spawn_sign('finished.sdf', 'finished')
        elif self.phase == 'finished':
            return

    def spawn_sign(self, filename, phase):
        request = SpawnEntity.Request()
        request.entity_factory.name = 'campus_status_sign'
        request.entity_factory.sdf_filename = str(self.sign_dir / filename)
        request.entity_factory.pose.position.x = 0.0
        request.entity_factory.pose.position.y = 3.35
        request.entity_factory.pose.position.z = 1.80
        self.phase = phase + '_pending'
        future = self.spawn_client.call_async(request)
        future.add_done_callback(lambda result: self.spawned(result, phase))

    def spawned(self, future, phase):
        try:
            success = future.result().success
        except Exception as exc:
            self.get_logger().error(f'Could not show {phase} sign: {exc}')
            self.phase = 'waiting' if phase == 'started' else 'removed'
            return
        if success:
            self.phase = phase
            self.get_logger().info('Gazebo display: SIMULATION STARTED' if phase == 'started' else 'Gazebo display: ROUTE FINISHED')
        else:
            self.get_logger().warning(f'Gazebo did not create the {phase} sign; will retry.')
            self.phase = 'waiting' if phase == 'started' else 'removed'

    def removed(self, future):
        try:
            success = future.result().success
        except Exception as exc:
            self.get_logger().error(f'Could not replace the status sign: {exc}')
            self.phase = 'started'
            return
        if success:
            self.phase = 'removed'
        else:
            self.get_logger().warning('Could not remove the started sign; will retry.')
            self.phase = 'started'


def main(args=None):
    rclpy.init(args=args)
    node = CampusStatusDisplay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
