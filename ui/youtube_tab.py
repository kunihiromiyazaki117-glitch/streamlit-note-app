from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

class YouTubeTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("YouTube 投稿機能"))
        self.setLayout(layout)