from setuptools import find_packages, setup

package_name = "autonomous_mobile_robot_localization"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Dharun235",
    maintainer_email="dharunkumar.senthilkumar9@gmail.com",
    description="Differential-drive odometry from wheel encoder joint states",
    license="MIT",
    entry_points={
        "console_scripts": [
            "odometry_node = autonomous_mobile_robot_localization.odometry_node:main",
        ],
    },
)
