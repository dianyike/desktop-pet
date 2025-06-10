from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtGui import QMovie
from PySide6.QtCore import Qt, QPoint, QSize
import sys

class DesktopPet(QLabel):
    def __init__(self):
        super().__init__()

        # 載入動畫
        self.movie = QMovie("assets/test.gif")  # 替換為你的 GIF 檔
        self.movie.setScaledSize(QSize(150, 150))   # 縮放尺寸
        self.setMovie(self.movie)

        # 設定無邊框 + 透明背景 + 最上層
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(150, 150)

        # 開始動畫
        self.movie.start()

        self.drag_position = None  # 拖曳起點位置

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec())