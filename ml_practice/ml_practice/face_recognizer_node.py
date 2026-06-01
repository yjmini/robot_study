import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

class FaceRecognizerNode(Node):
    def __init__(self):
        super().__init__('face_recognizer_node')
        
        # 카메라 데이터 Subscriber
        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.image_callback,
            10)
        self.bridge = CvBridge()
        
        # OpenCV 기본 얼굴 감지 모델 (Haar Cascade) 로드
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # 등록된 얼굴 데이터를 저장할 리스트 [{'name': '...', 'face_roi': np.array}]
        self.known_faces = []
        
        # 터미널 입력을 받을 때 화면 업데이트를 멈추기 위한 플래그
        self.is_registering = False
        
        self.get_logger().info('얼굴 인식 노드가 시작되었습니다.')
        self.get_logger().info("⭐ 화면에 'Unknown' 얼굴이 보일 때 영상 창을 클릭하고 's' 키를 누르면 터미널에서 이름을 등록할 수 있습니다!")

    def mse(self, imageA, imageB):
        # 두 이미지 간의 평균 제곱 오차(Mean Squared Error) 계산 - 특징 비교용
        err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
        err /= float(imageA.shape[0] * imageA.shape[1])
        return err

    def image_callback(self, msg):
        # 이름 입력 중에는 영상 처리를 잠시 중단
        if self.is_registering:
            return

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'이미지 변환 오류: {e}')
            return

        # 얼굴 인식을 위해 흑백 이미지로 변환
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # 얼굴 감지 (크기 및 민감도 조절)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=6, minSize=(80, 80)
        )
        
        detected_unknown_faces = []

        for (x, y, w, h) in faces:
            # 감지된 얼굴 영역(ROI)만 잘라내어 100x100 크기로 정규화
            roi_gray = gray[y:y+h, x:x+w]
            roi_resized = cv2.resize(roi_gray, (100, 100))
            
            name = "Unknown"
            min_error = float('inf')
            
            # 1. 저장된 얼굴(기억)들과 현재 얼굴 비교
            for known_face in self.known_faces:
                error = self.mse(roi_resized, known_face['face_roi'])
                if error < min_error:
                    min_error = error
                    
            # 2. 오차율이 임계값(Threshold)보다 낮으면 아는 사람으로 판별
            # (주변 밝기에 따라 4000~6000 사이로 조절이 필요할 수 있습니다)
            threshold = 4500
            if min_error < threshold:
                for known_face in self.known_faces:
                    if self.mse(roi_resized, known_face['face_roi']) == min_error:
                        name = known_face['name']
                        break
            else:
                detected_unknown_faces.append(roi_resized)

            # 3. 결과 시각화 (아는 사람이면 초록색, 모르면 빨간색 테두리)
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(cv_image, (x, y), (x+w, y+h), color, 2)
            cv2.putText(cv_image, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        cv2.imshow('Face Recognizer', cv_image)
        
        # 키보드 입력 처리
        key = cv2.waitKey(1) & 0xFF
        
        # 's' 키를 누르고 화면에 등록 안 된 얼굴이 있으면 등록 절차 진행
        if key == ord('s') and len(detected_unknown_faces) > 0:
            self.is_registering = True
            face_to_register = detected_unknown_faces[0] # 가장 첫 번째 얼굴 추출
            
            print("\n" + "="*50)
            print("👤 새로운 얼굴이 감지되었습니다!")
            # 터미널에서 입력을 대기
            new_name = input("이 사람의 이름을 입력하세요 (영문 권장): ")
            
            if new_name.strip():
                # 리스트에 이름과 얼굴 데이터 쌍으로 저장
                self.known_faces.append({'name': new_name, 'face_roi': face_to_register})
                print(f"✅ [{new_name}]님의 얼굴이 기억되었습니다!")
            else:
                print("❌ 이름이 입력되지 않아 등록이 취소되었습니다.")
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