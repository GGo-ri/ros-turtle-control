import rclpy
import pymysql
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from std_msgs.msg import String
from std_srvs.srv import Empty


class TurtleBridge(Node):
    def __init__(self):
        super().__init__('turtle_bridge')
        self.declare_parameter('linear_speed', 2.0)
        self.declare_parameter('angular_speed', 2.0)
        self.declare_parameter('db_host', '127.0.0.1')
        self.declare_parameter('db_user', 'rosuser')
        self.declare_parameter('db_password', '')
        self.declare_parameter('db_name', 'rosdb')

        self.pose = None
        self.vel_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.create_subscription(Pose, '/turtle1/pose', self.on_pose, 10)
        self.create_subscription(String, '/turtle_gui_cmd', self.on_cmd, 10)
        self.reset_client = self.create_client(Empty, '/reset')

    def on_pose(self, msg):
        self.pose = msg

    def on_cmd(self, msg):
        cmd = msg.data
        if cmd in ('up', 'down', 'left', 'right'):
            self.move(cmd)
        elif cmd == 'reset':
            self.reset_client.call_async(Empty.Request())
        elif cmd == 'stop':
            self.vel_pub.publish(Twist())
        elif cmd == 'save':
            self.save()

    def move(self, cmd):
        lin = self.get_parameter('linear_speed').value
        ang = self.get_parameter('angular_speed').value
        twist = Twist()
        if cmd == 'up':
            twist.linear.x = lin
        elif cmd == 'down':
            twist.linear.x = -lin
        elif cmd == 'left':
            twist.angular.z = ang
        elif cmd == 'right':
            twist.angular.z = -ang
        self.vel_pub.publish(twist)

    def save(self):
        if self.pose is None:
            self.get_logger().warn('pose not received yet')
            return
        conn = None
        try:
            conn = pymysql.connect(
                host=self.get_parameter('db_host').value,
                user=self.get_parameter('db_user').value,
                password=self.get_parameter('db_password').value,
                database=self.get_parameter('db_name').value,
                connect_timeout=3,
            )
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO turtlepos (x, y, theta) VALUES (%s, %s, %s)',
                    (self.pose.x, self.pose.y, self.pose.theta),
                )
            conn.commit()
            self.get_logger().info(
                f'saved x={self.pose.x:.2f} y={self.pose.y:.2f} theta={self.pose.theta:.2f}')
        except pymysql.MySQLError as e:
            self.get_logger().error(f'db error: {e}')
        finally:
            if conn:
                conn.close()


def main(args=None):
    rclpy.init(args=args)
    node = TurtleBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()