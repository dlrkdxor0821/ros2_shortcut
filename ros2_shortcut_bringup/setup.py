from setuptools import find_packages, setup

package_name = "ros2_shortcut_bringup"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/foxglove_bridge.launch.py"]),
        ("share/" + package_name + "/config", ["config/foxglove_bridge.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="TODO",
    maintainer_email="TODO@example.com",
    description="Bringup/launch package for ros2_shortcut (Foxglove bridge prototype).",
    license="Apache-2.0",
    entry_points={"console_scripts": []},
)

