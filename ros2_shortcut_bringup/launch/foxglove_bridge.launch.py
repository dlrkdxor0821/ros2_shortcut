from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution


def generate_launch_description():
    address = LaunchConfiguration("address")
    port = LaunchConfiguration("port")

    default_config = PathJoinSubstitution(
        [FindPackageShare("ros2_shortcut_bringup"), "config", "foxglove_bridge.yaml"]
    )

    bridge_node = Node(
        package="foxglove_bridge",
        executable="foxglove_bridge",
        name="foxglove_bridge",
        output="screen",
        parameters=[
            default_config,
            {"address": address, "port": port},
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "address",
                default_value="127.0.0.1",
                description="Bind address for WebSocket server (127.0.0.1 local only, 0.0.0.0 for LAN).",
            ),
            DeclareLaunchArgument(
                "port",
                default_value="8765",
                description="TCP port for WebSocket server.",
            ),
            bridge_node,
        ]
    )

