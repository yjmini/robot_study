from setuptools import find_packages, setup

package_name = 'pjt_llm'

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
    maintainer_email='u79jm@koreatech.ac.kr',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'step2_agent = pjt_llm.step2_agent:main',
            'step3_agent = pjt_llm.step3_agent:main',
            'step4_chatbot = pjt_llm.step4_chatbot:main',
            'ros2_controller = pjt_llm.ros2_controller:main',
            'step5_controller_agent = pjt_llm.step5_controller_agent:main',
            'step6_orchestrator = pjt_llm.step6_orchestrator:main',
        ],
    },
)
