# Robot Study

ROS 2, RealSense, Dobot, YOLO, SLAM, URDF, RoboDK 실습을 모아둔 로봇 소프트웨어 학습 저장소입니다.

## 프로젝트 개요

로봇 소프트웨어 실습 과정에서 작성한 ROS 2 패키지와 Python 실험 코드를 주제별로 정리했습니다. RGB-D 카메라 데이터 처리, YOLO 인식, Dobot 제어, SLAM, URDF 모델링, 웹소켓 연동 등 실제 로봇 시스템 구성에 필요한 요소를 다룹니다.

## 주요 구성

| 폴더 | 내용 |
| --- | --- |
| `integrate_prac/` | RealSense, YOLO, Dobot, conveyor/socket 통합 실습 |
| `slam_pjt/`, `slam_tuning_pkg/` | SLAM 및 맵/파라미터 튜닝 실습 |
| `urdf_practice/` | URDF/Xacro 로봇 모델링 실습 |
| `my_robot_controller/`, `move_car_tf/` | ROS 2 제어 및 TF 실습 |
| `rs_dobot_sub_pkg/`, `sensor_sub_pkg/` | 센서/로봇 구독 패키지 |
| `pjt_llm/` | LLM 연동 실험 |
| `ml_practice/` | 머신러닝/비전 보조 실습 |

## 기술 스택

- **Middleware**: ROS 2, rclpy
- **Robot/Device**: Dobot Magician, Intel RealSense, TurtleBot-style mobile robot
- **Vision**: OpenCV, YOLOv5, cv_bridge
- **Simulation/Tools**: RViz, Gazebo, RoboDK
- **Language**: Python

## 프로젝트 구조

```text
.
├── integrate_prac/
├── slam_pjt/
├── slam_tuning_pkg/
├── urdf_practice/
├── clean_robot/
├── my_robot_controller/
├── rs_dobot_sub_pkg/
├── sensor_sub_pkg/
└── requirements.txt
```

## 핵심 구현 내용

### 1. RGB-D 기반 물체 위치 추정
RealSense color/depth topic을 구독하고, pixel 좌표와 depth 정보를 사용해 3D 좌표를 계산하는 실습을 포함합니다.

### 2. Dobot 제어와 Pick-and-Place
Dobot action/service client를 통해 homing, PTP 이동, suction cup, gripper 제어를 수행하는 노드를 작성했습니다.

### 3. Vision-Robot 통합
YOLO 탐지 결과를 ROS topic으로 발행하고, 탐지 좌표를 로봇 동작이나 시각화 흐름에 연결하는 실습을 구성했습니다.

### 4. SLAM/URDF/RViz 실습
맵 생성, RViz 시각화, URDF 모델링, TF 이동 제어 등 로봇 SW의 기본 구성 요소를 각각 실험했습니다.

## 실행 예시

```bash
pip install -r requirements.txt
colcon build
source install/setup.bash
ros2 run integrate_prac <node_name>
```

---
ROS 2 기반 로봇 인식·제어·시뮬레이션 실습을 모아둔 학습 저장소입니다.
