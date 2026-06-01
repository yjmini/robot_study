import cv2
import numpy as np
import pyrealsense2 as rs

class RealSenseApp:
    def __init__(self):
        # Realsense setup
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.pipeline.start(config)

        # ROI variables 
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
            self.roi_end = (x,y)

        elif event == cv2.EVENT_LBUTTONUP:
            self.roi_end = (x,y)
            self.drawing = False

            if self.roi_start and self.roi_end:
                x1, y1 = self.roi_start
                x2, y2 = self.roi_end
                roi_coords = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                print(f"Selected ROI: {roi_coords}")

    def run(self):
        try:
            while True:
                frames =self.pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()

                if not color_frame:
                    continue

                self.color_image = np.asanyarray(color_frame.get_data())

                if self.roi_start and self.roi_end:
                    cv2.rectangle(self.color_image, self.roi_start, self.roi_end,(0, 255, 0), 2)

                cv2.imshow('frame', self.color_image)
                key = cv2.waitKey(1)

                if key == ord('q'):
                    break

        finally:
            self.pipeline.stop()
            cv2.destroyAllWindows()

if __name__ == '__main__':
    app = RealSenseApp()
    app.run()