import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

import torch

from cv_bridge import CvBridge
import cv2

class YOLOv5Publisher(Node):
    def __init__(self):
        super().__init__('yolov5_publisher')
        
        # Create publishers
        self.result_publisher = self.create_publisher(String, 'yolov5_results', 10)
        self.image_publisher = self.create_publisher(Image, 'yolov5_image_with_boxes', 10)
        
        # Subscribe to the image topic
        self.image_subscriber = self.create_subscription(Image, '/camera/camera/color/image_raw', self.image_callback, 10)
        
        # Load YOLOv5 model
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.bridge = CvBridge()
        

    def image_callback(self, msg):
        # Convert ROS Image message to OpenCV image
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return
        
        # Run YOLOv5 inference
        results = self.model(cv_image)
        detections = results.pandas().xyxy[0]  # Get bounding boxes and labels as a pandas DataFrame

        detection_data = []
        
        for _, row in detections.iterrows():
            label = row['name']
            confidence = row['confidence']
            xmin, ymin, xmax, ymax = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            # Add detection information to the result message
            detection_info = f"Label: {label}, Confidence: {confidence:.2f}, BBox: ({xmin}, {ymin}, {xmax}, {ymax})"
            detection_data.append(detection_info)

            # Draw bounding box and label on the image
            cv2.rectangle(cv_image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            cv2.putText(cv_image, f"{label} {confidence:.2f}", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Publish detection results as text
        result_message = String()
        result_message.data = '\n'.join(detection_data)
        self.result_publisher.publish(result_message)
        self.get_logger().info("Published YOLOv5 detection results.")
        
        # Convert the modified image to ROS Image message and publish
        try:
            boxed_image_msg = self.bridge.cv2_to_imgmsg(cv_image, encoding="bgr8")
            self.image_publisher.publish(boxed_image_msg)
            self.get_logger().info("Published image with bounding boxes.")
        except Exception as e:
            self.get_logger().error(f"Failed to publish image: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = YOLOv5Publisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
