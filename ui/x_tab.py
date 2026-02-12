from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QTextEdit,
    QListWidget, QListWidgetItem,
    QApplication
)
from PySide6.QtCore import Qt

import feedparser
from dotenv import load_dotenv
import os
from google import genai


class XTab(QWidget):
    def __init__(self):
        super().__init__()

        # Gemini 初期化
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)

        layout = QVBoxLayout()

        # 説明
        self.info_label = QLabel(
            "X（旧Twitter）用：ニュースを選択して投稿文を生成します"
        )
        layout.addWidget(self.info_label)

        # ステータス表示
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # ニュース一覧
        self.news_list = QListWidget()
        self.news_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.news_list)

        # ニュース読み込みボタン
        self.load_button = QPushButton("ニュースを読み込む")
        self.load_button.clicked.connect(self.load_news)
        layout.addWidget(self.load_button)

        # 投稿文生成ボタン
        self.generate_button = QPushButton("X投稿文を作成")
        self.generate_button.clicked.connect(self.generate_x_post)
        layout.addWidget(self.generate_button)

        # 結果表示
        self.result_box = QTextEdit()
        layout.addWidget(self.result_box)

        self.setLayout(layout)

        # ニュースデータ保持用
        self.news_entries = []

    def load_news(self):
        """Yahooニュースを取得して一覧表示"""
        rss_urls = [
            ("国内", "https://news.yahoo.co.jp/rss/topics/domestic.xml"),
            ("経済", "https://news.yahoo.co.jp/rss/topics/business.xml"),
            ("IT", "https://news.yahoo.co.jp/rss/topics/it.xml"),
            ("科学", "https://news.yahoo.co.jp/rss/topics/science.xml"),
        ]

        self.news_list.clear()
        self.news_entries = []

        for category, url in rss_urls:
            # カテゴリ見出し（選択不可）
            header = QListWidgetItem(f"=== {category} ===")
            header.setFlags(header.flags() & ~Qt.ItemIsSelectable)
            self.news_list.addItem(header)

            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                index = len(self.news_entries)
                self.news_entries.append({
                    "title": entry.title,
                    "summary": getattr(entry, "summary", "（概要なし）")
                })

                item = QListWidgetItem(f"[{category}] {entry.title}")
                item.setData(Qt.UserRole, index)
                self.news_list.addItem(item)

        self.result_box.setText("ニュースを読み込みました。")

    def generate_x_post(self):
        """選択されたニュースからX投稿文を生成"""
        selected_items = self.news_list.selectedItems()

        if not selected_items:
            self.result_box.setText("ニュースが選択されていません。")
            return

        # ===== 処理中表示 START =====
        self.status_label.setText("X投稿文を生成中です…しばらくお待ちください")
        self.generate_button.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        # ===========================

        try:
            selected_news = []
            for item in selected_items:
                index = item.data(Qt.UserRole)
                if index is not None:
                    selected_news.append(self.news_entries[index])

            news_text = ""
            for i, news in enumerate(selected_news, start=1):
                news_text += (
                    f"【ニュース{i}】\n"
                    f"タイトル: {news['title']}\n"
                    f"概要: {news['summary']}\n\n"
                )

            prompt = f"""
あなたは「デイリーニュースCFO マーク」です。

以下のニュースを、X（旧Twitter）向けに
1ニュース＝4〜5ポストのスレッド形式でまとめてください。

【ルール】
- 1ポスト140文字以内
- 丁寧で落ち着いた口調
- 煽らない
- 絵文字なし
- そのままコピペできる形式

【ニュース】
{news_text}
"""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            self.result_box.setText(response.text)

        finally:
            # ===== 処理中表示 END =====
            self.status_label.setText("生成が完了しました。")
            self.generate_button.setEnabled(True)
            QApplication.restoreOverrideCursor()
