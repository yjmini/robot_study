import cv2
import numpy as np

class WebcamApp:
    def __init__(self):
        self.cap = cv2.VideoCapture(0) # 0번 카메라 (웹캠)

        # 해상도 설정 (기존 코드와 동일하게 640x480으로 맞춤)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not self.cap.isOpened():
            print("웹캠을 열 수 없습니다.")
            exit()

        # ROI 변수들 (기존과 동일)
        self.roi_start = None
        self.roi_end = None
        self.drawing = False
        self.color_image = None

        cv2.namedWindow('frame')
        cv2.setMouseCallback('frame', self.mouse_callback)

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.roi_start = (x, y)
            self.drawing = True

        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.roi_end = (x, y)

        elif event == cv2.EVENT_LBUTTONUP:
            self.roi_end = (x, y)
            self.drawing = False

            if self.roi_start and self.roi_end:
                x1, y1 = self.roi_start
                x2, y2 = self.roi_end
                roi_coords = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                print(f"Selected ROI: {roi_coords}")

    def run(self):
        try:
            while True:
                ret, frame = self.cap.read()

                if not ret:
                    print("프레임을 받아올 수 없습니다. (종료)")
                    break

                self.color_image = frame

                if self.roi_start and self.roi_end:
                    cv2.rectangle(self.color_image, self.roi_start, self.roi_end, (0, 255, 0), 2)

                cv2.imshow('frame', self.color_image)
                key = cv2.waitKey(1)

                if key == ord('q'):
                    break

        finally:
            self.cap.release()
            cv2.destroyAllWindows()

if __name__ == '__main__':
    app = WebcamApp()
    app.run()