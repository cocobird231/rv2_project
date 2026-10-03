"""Bring up the physical joystick acceptance path and observe sport requests."""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def _include(package, filename, enabled, arguments):
    """Keep the child launches' shared argument names in separate scopes."""
    return GroupAction(
        scoped=True,
        condition=IfCondition(LaunchConfiguration(enabled)),
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [FindPackageShare(package), "launch", filename]
                    )
                ),
                launch_arguments=arguments.items(),
            )
        ],
    )


def generate_launch_description():
    """Compose the existing R1 launches with independently controllable peers."""
    defaults = {
        "start_joy": ("true", "Start the physical joystick driver"),
        "start_bridge": ("true", "Start the Joy to R1 bridge"),
        "start_server": ("true", "Start the control server"),
        "start_master": ("true", "Start one independent CSM master"),
        "observe_requests": ("true", "Echo sport requests without sending responses"),
        "joy_topic": ("/joy", "Joy input topic shared by the driver and bridge"),
        "device_id": ("0", "SDL joystick index; device_name takes precedence"),
        "device_name": ("", "Optional exact SDL joystick name"),
        "autorepeat_rate": ("20.0", "Joy updates per second while controls are held"),
        "deadzone": ("0.05", "Joystick axis deadzone"),
        "server_name": ("control_server", "R1 target manager name"),
        "master_name": ("csm_master", "Shared R1 master name"),
        "bridge_name": ("topic_bridge", "R1 source manager name"),
    }
    arguments = [
        DeclareLaunchArgument(name, default_value=value, description=description)
        for name, (value, description) in defaults.items()
    ]
    for name, package, filename in (
        ("bridge_config_file", "rv2_csm_topic_bridge", "topic_bridge.yaml"),
        ("server_config_file", "rv2_server_control", "control_server.yaml"),
    ):
        arguments.append(
            DeclareLaunchArgument(
                name,
                default_value=PathJoinSubstitution(
                    [FindPackageShare(package), "config", filename]
                ),
            )
        )

    joy = Node(
        package="joy",
        executable="joy_node",
        name="joy_node",
        output="screen",
        condition=IfCondition(LaunchConfiguration("start_joy")),
        parameters=[
            {
                name: ParameterValue(LaunchConfiguration(name), value_type=value_type)
                for name, value_type in (
                    ("device_id", int),
                    ("device_name", str),
                    ("autorepeat_rate", float),
                    ("deadzone", float),
                )
            }
        ],
        remappings=[("joy", LaunchConfiguration("joy_topic"))],
    )
    master = Node(
        package="rv2_control_signal_transport",
        executable="csm_master_node",
        output="screen",
        condition=IfCondition(LaunchConfiguration("start_master")),
        parameters=[
            {
                "master_name": ParameterValue(
                    LaunchConfiguration("master_name"), value_type=str
                )
            }
        ],
    )
    bridge = _include(
        "rv2_csm_topic_bridge",
        "topic_bridge.launch.py",
        "start_bridge",
        {
            "config_file": LaunchConfiguration("bridge_config_file"),
            "topic_name": LaunchConfiguration("joy_topic"),
            "msg_type": "joy",
            "server_name": LaunchConfiguration("server_name"),
            "master_name": LaunchConfiguration("master_name"),
            "csm_name": LaunchConfiguration("bridge_name"),
        },
    )
    server = _include(
        "rv2_server_control",
        "control_server.launch.py",
        "start_server",
        {
            "config_file": LaunchConfiguration("server_config_file"),
            "server_name": LaunchConfiguration("server_name"),
            "master_name": LaunchConfiguration("master_name"),
            "start_master": "false",
        },
    )
    observer = ExecuteProcess(
        cmd=[
            FindExecutable(name="ros2"),
            "topic",
            "echo",
            "/api/sport/request",
            "unitree_api/msg/Request",
        ],
        name="unitree_requests",
        output="screen",
        additional_env={"PYTHONUNBUFFERED": "1"},
        condition=IfCondition(LaunchConfiguration("observe_requests")),
    )
    return LaunchDescription(arguments + [master, joy, bridge, server, observer])
