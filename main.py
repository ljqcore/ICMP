import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit
import frame


class Frame(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = frame.Ui_Form()
        self.ui.setupUi(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Frame()
    window.show()
    sys.exit(app.exec_())
