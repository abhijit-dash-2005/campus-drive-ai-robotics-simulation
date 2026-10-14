import importlib.util
import math
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'lidar_avoid.py'

spec = importlib.util.spec_from_file_location('lidar_avoid', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_front_obstacle_stops_robot():
    ranges = [math.inf] * 360
    for i in range(150, 210):
        ranges[i] = 0.5
    cmd = module.choose_twist(ranges)
    assert cmd.linear.x == 0.0
    assert abs(cmd.angular.z) <= 0.05


def test_clear_path_moves_forward():
    ranges = [5.0] * 360
    cmd = module.choose_twist(ranges)
    assert cmd.linear.x > 0.0
    assert abs(cmd.angular.z) <= 0.05
