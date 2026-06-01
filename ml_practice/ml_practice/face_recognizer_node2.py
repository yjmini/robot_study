import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import face_recognition

class FaceRecognizerNode(Node):
    def __init__(self):
        super().__init__('face_recognizer_node')
        
        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.image_callback,
            10)
        self.bridge = CvBridge()
        
        # 등록된 얼굴의 인코딩(128차원 벡터)과 이름을 저장할 리스트
        self.known_face_encodings = []
        self.known_face_names = []
        
        self.is_registering = False
        
        self.get_logger().info('딥러닝 기반 얼굴 인식 노드가 시작되었습니다.')
        self.get_logger().info("⭐ 화면에 'Unknown' 얼굴이 보일 때 영상 창을 클릭하고 's' 키를 누르면 이름 등록이 가능합니다!")

    def image_callback(self, msg):
        if self.is_registering:
            return

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'이미지 변환 오류: {e}')
            return

        # 연산 속도를 높이기 위해 프레임 크기를 1/4로 축소
        small_frame = cv2.resize(cv_image, (0, 0), fx=0.25, fy=0.25)
        
        # OpenCV의 BGR 색상을 face_recognition이 사용하는 RGB 색상으로 변환
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # 현재 프레임에서 모든 얼굴의 위치와 인코딩 추출
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        face_names = []
        unknown_encodings = [] # 이번 프레임에서 감지된 모르는 얼굴들

        for face_encoding in face_encodings:
            # 등록된 얼굴들과 현재 얼굴 비교 (tolerance가 낮을수록 엄격하게 검사, 기본값 0.6)
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"

            # 등록된 얼굴이 있다면 가장 유사도가 높은 얼굴을 찾음
            if True in matches:
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]

            face_names.append(name)
            if name == "Unknown":
                unknown_encodings.append(face_encoding)

        # 결과 시각화 (축소했던 좌표를 다시 4배로 확대하여 원본에 그림)
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            
            # 얼굴 박스 그리기
            cv2.rectangle(cv_image, (left, top), (right, bottom), color, 2)
            # 이름 텍스트 그리기
            cv2.putText(cv_image, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        cv2.imshow('Deep Learning Face Recognizer', cv_image)
        
        # 키보드 입력 처리 ('s' 키로 얼굴 등록)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s') and len(unknown_encodings) > 0:
            self.is_registering = True
            
            # 가장 먼저 감지된 모르는 얼굴의 인코딩 데이터를 가져옴
            encoding_to_register = unknown_encodings[0] 
            
            print("\n" + "="*50)
            print("👤 새로운 얼굴이 감지되었습니다!")
            new_name = input("이 사람의 이름을 입력하세요 (영문 권장): ")
            
            if new_name.strip():
                self.known_face_encodings.append(encoding_to_register)
                self.known_face_names.append(new_name)
                print(f"✅ [{new_name}]님의 얼굴 특징이 성공적으로 등록되었습니다!")
            else:
                print("❌ 이름이 입력되지 않아 취소되었습니다.")
            print("="*50 + "\n")
            
            self.is_registering = False

def main(args=None):
    rclpy.init(args=args)
    node = FaceRecognizerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('사용자에 의해 노드가 종료되었습니다.')
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()