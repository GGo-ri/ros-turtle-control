import sys
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout

DIRECTIONS = {'up', 'down', 'left', 'right'}


class TurtleGui(QWidget):
    def __init__(self, node):
        super().__init__()
        self.pub = node.create_publisher(String, '/turtle_gui_cmd', 10)
        self.held = None
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.repeat)
        self.setWindowTitle('Turtle Control')

        layout = QGridLayout(self)
        buttons = {
            'up': ('▲', 0, 1, 1),
            'left': ('◀', 1, 0, 1),
            'down': ('▼', 1, 1, 1),
            'right': ('▶', 1, 2, 1),
            'reset': ('Reset', 2, 0, 1),
            'save': ('Save Pose', 2, 1, 2),
        }
        for cmd, (label, row, col, span) in buttons.items():
            btn = QPushButton(label)
            btn.setMinimumSize(80, 60)
            if cmd in DIRECTIONS:
                btn.pressed.connect(lambda c=cmd: self.start(c))
                btn.released.connect(self.stop)
            else:
                btn.clicked.connect(lambda _, c=cmd: self.send(c))
            layout.addWidget(btn, row, col, 1, span)

    def send(self, cmd):
        self.pub.publish(String(data=cmd))

    def start(self, cmd):
        self.held = cmd
        self.send(cmd)
        self.timer.start()

    def repeat(self):
        self.send(self.held)

    def stop(self):
        self.timer.stop()
        self.held = None
        self.send('stop')


def main():
    rclpy.init()
    node = Node('turtle_gui')
    app = QApplication(sys.argv)
    gui = TurtleGui(node)
    gui.show()
    code = app.exec_()
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(code)


if __name__ == '__main__':
    main()