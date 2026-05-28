from setuptools import find_packages, setup

package_name = 'sensor_sub_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ssafy',
    maintainer_email='ssafy@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'odom_sub = sensor_sub_pkg.odom_subscriber:main',
            'imu_sub = sensor_sub_pkg.imu_subscriber:main',
            'laser_sub = sensor_sub_pkg.laser_subscriber:main',
        ],
    },
)
