"""Exercise the installed joystick launch with synthetic input and real peers."""

import json
import signal
import time
import unittest
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_testing import post_shutdown_test
from launch_testing.actions import ReadyToTest
from launch_testing.asserts import assertExitCodes
from rclpy import create_node, init, shutdown
from rclpy.executors import SingleThreadedExecutor
from rclpy.parameter_client import AsyncParameterClient
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Joy
from unitree_api.msg import Request

JOY_TOPIC = "/project_test/joy"
MASTER = "project_test_master"
SERVER = "project_test_server"
BRIDGE = "project_test_bridge"
MOVE, STOP = 1008, 1003


def generate_test_description():
    """Load the installed entry point without opening a physical joystick."""
    share = Path(get_package_share_directory("rv2_project"))
    path = share / "launch/test_joystick.launch.py"
    pipeline = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(path)),
        launch_arguments={
            "joy_topic": JOY_TOPIC,
            "device_id": "999999",
            "device_name": "",
            "server_name": SERVER,
            "master_name": MASTER,
            "bridge_name": BRIDGE,
        }.items(),
    )
    return LaunchDescription([pipeline, ReadyToTest()])


class TestJoystickLaunch(unittest.TestCase):
    """Check launch wiring, observable commands, input loss, and recovery."""

    def setUp(self):
        """Use one manually spun executor so cleanup has no worker to drain."""
        init()
        self.addCleanup(shutdown)
        self.node = create_node("project_joystick_probe")
        self.addCleanup(self.node.destroy_node)
        self.executor = SingleThreadedExecutor()
        self.addCleanup(self.executor.shutdown)
        self.executor.add_node(self.node)
        self.requests = []
        self.subscription = self.node.create_subscription(
            Request, "/api/sport/request", self.requests.append, 100
        )
        self.publisher = self.node.create_publisher(
            Joy, JOY_TOPIC, qos_profile_sensor_data
        )
        self.enabled = False
        self.timer = self.node.create_timer(0.05, self.publish_joy)

    def publish_joy(self):
        """Send fresh identical samples at 20 Hz, with both triggers released."""
        if self.enabled:
            message = Joy()
            message.header.stamp = self.node.get_clock().now().to_msg()
            message.axes = [0.47, -0.23, 1.0, 0.31, 0.0, 1.0, 0.0, 0.0]
            message.buttons = [0] * 12
            self.publisher.publish(message)

    def wait_for(self, predicate, timeout=20.0):
        """Keep ROS callbacks moving until an observable condition or deadline."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return True
            self.executor.spin_once(timeout_sec=0.02)
        return predicate()

    def parameters(self, node_name, names):
        """Read the effective running configuration through ROS services."""
        client = AsyncParameterClient(self.node, node_name)
        self.assertTrue(self.wait_for(client.services_are_ready), node_name)
        future = client.get_parameters(names)
        self.assertTrue(self.wait_for(future.done), node_name)
        return future.result().values

    def count(self, api):
        """Count actual Unitree messages, independent of runtime log wording."""
        return sum(message.header.identity.api_id == api for message in self.requests)

    def test_installed_pipeline(self, proc_output):
        """Verify production launches share one master and recover after silence."""
        expected = {"joy_node", "csm_master_node", "control_server", "topic_bridge"}
        self.assertTrue(
            self.wait_for(lambda: expected <= set(self.node.get_node_names()))
        )
        self.assertEqual(self.node.get_node_names().count("csm_master_node"), 1)
        joy = self.parameters("joy_node", ["device_id", "autorepeat_rate"])
        self.assertEqual(joy[0].integer_value, 999999)
        self.assertAlmostEqual(joy[1].double_value, 20.0)
        configurations = {
            "csm_master_node": {"master_name": MASTER},
            "control_server": {"server_name": SERVER, "master_name": MASTER},
            "topic_bridge": {
                "server_name": SERVER,
                "master_name": MASTER,
                "csm_name": BRIDGE,
                "topic_name": JOY_TOPIC,
            },
        }
        for node_name, values in configurations.items():
            actual = self.parameters(node_name, list(values))
            self.assertEqual(
                [value.string_value for value in actual], list(values.values())
            )
        self.assertTrue(
            self.wait_for(lambda: self.publisher.get_subscription_count() > 0)
        )
        self.assertTrue(
            self.wait_for(
                lambda: self.node.count_subscribers("/api/sport/request") >= 2
            ),
            "request observer did not subscribe",
        )
        self.enabled = True
        self.assertTrue(self.wait_for(lambda: self.count(MOVE) > 0), "no Move request")
        move = next(
            message
            for message in self.requests
            if message.header.identity.api_id == MOVE
        )
        payload = json.loads(move.parameter)
        for key, value in {"x": 0.47, "y": -0.23, "z": 0.31}.items():
            self.assertAlmostEqual(payload[key], value, places=5)

        before_stop, before_move = self.count(STOP), self.count(MOVE)
        self.enabled = False
        self.assertTrue(self.wait_for(lambda: self.count(STOP) > before_stop, 8.0))
        self.assertEqual(self.count(MOVE), before_move, "silence replayed cached input")
        self.enabled = True
        self.assertTrue(
            self.wait_for(lambda: self.count(MOVE) > before_move),
            "same-value input did not recover after STOP",
        )
        self.assertEqual(self.node.get_node_names().count("csm_master_node"), 1)
        self.enabled = False
        for api in (MOVE, STOP):
            proc_output.assertWaitFor(
                f"api_id: {api}", process="unitree_requests", timeout=5, stream="stdout"
            )


@post_shutdown_test()
class TestJoystickLaunchExit(unittest.TestCase):
    """Reject crashed or forcibly killed launch children."""

    def test_exit_codes(self, proc_info):
        """ros2cli converts KeyboardInterrupt to positive SIGINT; nodes do not."""
        for process in proc_info.processes():
            allowed = [0, -signal.SIGINT]
            if process.process_details["name"].startswith("unitree_requests-"):
                allowed.append(signal.SIGINT)
            assertExitCodes(proc_info, process=process, allowable_exit_codes=allowed)
