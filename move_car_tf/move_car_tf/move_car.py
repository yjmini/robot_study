import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped # tf 정보를 내보내기 위해 사용
from geometry_msgs.msg import Twist
from math import sin, cos

class SimpleCarTF(Node):
    def __init__(self):
        super().__init__('simple_car_tf')
        self.br = TransformBroadcaster(self)
        self.subscription = self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.timer = self.create_timer(0.1, self.update_transform)

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0

    def cmd_vel_callback(self, msg):
        self.linear_velocity = msg.linear.x
        self.angular_velocity = msg.angular.z

    def update_transform(self):
        now = self.get_clock().now().to_msg() # 현재 시간
        
        # 원 그리도록
        self.x += self.linear_velocity * cos(self.theta) * 0.1
        self.y += self.linear_velocity * sin(self.theta) * 0.1
        self.theta += self.angular_velocity * 0.1

        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = 'world' # 기준좌표계
        t.child_frame_id = 'base_link' #기준좌표계의 자식. base link

        t.transform.translation.x = self.x
        t.transform.translation.y = self.y 
        t.transform.translation.z = 0.0
        
        t.transform.rotation.z = sin(self.theta / 2.0)
        t.transform.rotation.w = cos(self.theta / 2.0)

        self.br.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = SimpleCarTF()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
