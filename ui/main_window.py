from PySide6.QtWidgets import QMainWindow, QTabWidget

from .calendar_tab import CalendarTab
from .news_tab import NewsTab
from .youtube_tab import YouTubeTab
from .x_tab import XTab
from .note_tab import NoteTab   # 追加


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My Automation App")
        self.setMinimumSize(900, 600)

        tabs = QTabWidget()
        tabs.addTab(CalendarTab(), "Google Calendar")
        tabs.addTab(NewsTab(), "News → Script")
        tabs.addTab(NoteTab(), "NOTE 記事生成")   # 追加
        tabs.addTab(XTab(), "X Post")
        tabs.addTab(YouTubeTab(), "YouTube Upload")

        self.setCentralWidget(tabs)
