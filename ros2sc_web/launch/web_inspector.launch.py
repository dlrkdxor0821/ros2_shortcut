from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    address = LaunchConfiguration("address")
    port = LaunchConfiguration("port")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "address",
                default_value="127.0.0.1",
                description="HTTP bind address (default: local only).",
            ),
            DeclareLaunchArgument(
                "port",
                default_value="8081",
                description="HTTP port for the web inspector.",
            ),
            SetEnvironmentVariable("ROS2SC_WEB_ADDRESS", address),
            SetEnvironmentVariable("ROS2SC_WEB_PORT", port),
            Node(
                package="ros2sc_web",
                executable="ros2sc_web_server",
                name="ros2sc_web_server",
                output="screen",
            ),
        ]
    )

