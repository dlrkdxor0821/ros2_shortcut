from setuptools import find_packages, setup

package_name = "ros2sc_web"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/web_inspector.launch.py"]),
        ("share/" + package_name + "/static", ["ros2sc_web/static/index.html"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="TODO",
    maintainer_email="TODO@example.com",
    description="Local web UI for inspecting ROS 2 graph (topics/services/nodes/types/packages).",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "ros2sc_web_server = ros2sc_web.server:main",
        ]
    },
)

