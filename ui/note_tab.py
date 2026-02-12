from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QTextEdit, QListWidget, QListWidgetItem,
    QApplication, QHBoxLayout
)
from PySide6.QtCore import Qt
import feedparser
from dotenv import load_dotenv
import os
import webbrowser
from google import genai
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime


class NoteTab(QWidget):
    def __init__(self):
        super().__init__()

        # ===== Gemini 初期化 =====
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)

        layout = QVBoxLayout()

        self.info_label = QLabel(
            "NOTE用：ニュース選択 → 記事生成 → コピーして投稿"
        )
        layout.addWidget(self.info_label)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # ===== ニュース一覧 =====
        self.news_list = QListWidget()
        self.news_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.news_list)

        self.load_button = QPushButton("ニュースを読み込む")
        self.load_button.clicked.connect(self.load_news)
        layout.addWidget(self.load_button)

        self.generate_button = QPushButton("NOTE記事を生成")
        self.generate_button.clicked.connect(self.generate_note_article)
        layout.addWidget(self.generate_button)

        # ===== 結果表示 =====
        self.result_box = QTextEdit()
        layout.addWidget(self.result_box)

        # ===== 投稿補助ボタン =====
        button_layout = QHBoxLayout()

        self.generate_image_button = QPushButton("NOTE用画像を生成")
        self.generate_image_button.clicked.connect(self.generate_note_image)
        button_layout.addWidget(self.generate_image_button)

        self.copy_title_button = QPushButton("タイトルをコピー")
        self.copy_title_button.clicked.connect(self.copy_title)
        button_layout.addWidget(self.copy_title_button)

        self.copy_body_button = QPushButton("本文をコピー")
        self.copy_body_button.clicked.connect(self.copy_body)
        button_layout.addWidget(self.copy_body_button)

        self.open_note_button = QPushButton("NOTE投稿ページを開く")
        self.open_note_button.clicked.connect(self.open_note)
        button_layout.addWidget(self.open_note_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.news_entries = []
        self.generated_title = ""
        self.generated_body = ""

    # ===== ニュース取得 =====
    def load_news(self):
        rss_urls = [
            ("国内", "https://news.yahoo.co.jp/rss/topics/domestic.xml"),
            ("経済", "https://news.yahoo.co.jp/rss/topics/business.xml"),
            ("IT", "https://news.yahoo.co.jp/rss/topics/it.xml"),
            ("科学", "https://news.yahoo.co.jp/rss/topics/science.xml"),
        ]

        self.news_list.clear()
        self.news_entries = []

        for category, url in rss_urls:
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

    # ===== NOTE記事生成 =====
    def generate_note_article(self):
        selected_items = self.news_list.selectedItems()
        if not selected_items:
            self.result_box.setText("ニュースが選択されていません。")
            return

        self.status_label.setText("NOTE記事を生成中です…")
        self.generate_button.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()

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
あなたはNOTEで収益化を目的としたプロの編集者です。

以下のニュースを元に、
NOTE用の記事を書いてください。

【構成ルール】
必ず次の構成で出力してください。

--------------------------------
【タイトル】
（NOTE向け・知的・煽らない）

【無料公開部分】
・導入
・ニュースの要点整理
・背景の解説
・ここまででも「読んでよかった」と思える内容

【ここから有料】
※この見出しを必ず入れる

【有料部分】
・一歩踏み込んだ考察
・ニュースの裏にある構造
・今後どうなりそうか
・社会人が取るべき視点や行動
--------------------------------

【条件】
・落ち着いた知的な文体
・煽らない
・断定しすぎない
・ニュース解説＋考察型
・全体で1500〜2000文字程度

【ニュース】
{news_text}

"""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            text = response.text.strip()

            # ===== タイトルと本文を分離 =====
            lines = text.splitlines()
            self.generated_title = lines[0].replace("【タイトル】", "").strip()
            self.generated_body = "\n".join(lines[1:]).replace("【本文】", "").strip()

            self.result_box.setText(
                f"【タイトル】\n{self.generated_title}\n\n{self.generated_body}"
            )

        finally:
            self.status_label.setText("生成完了。コピーしてNOTEに投稿できます。")
            self.generate_button.setEnabled(True)
            QApplication.restoreOverrideCursor()

    # ===== コピー＆投稿補助 =====
    def copy_title(self):
        if self.generated_title:
            QApplication.clipboard().setText(self.generated_title)
            self.status_label.setText("タイトルをコピーしました。")

    def copy_body(self):
        if self.generated_body:
            QApplication.clipboard().setText(self.generated_body)
            self.status_label.setText("本文をコピーしました。")

    def open_note(self):
        webbrowser.open("https://note.com/notes/create")

    def detect_background_category(self, title: str) -> str:
        if any(word in title for word in ["AI", "IT", "テクノロジー", "半導体"]):
            return "it"
        if any(word in title for word in ["株", "経済", "金融", "円", "インフレ"]):
            return "economy"
        if any(word in title for word in ["政府", "政策", "法案", "選挙"]):
            return "policy"
        if any(word in title for word in ["研究", "科学", "実験", "宇宙"]):
            return "science"
        return "default"
        
    def generate_note_image(self):
        if not self.generated_title:
            self.status_label.setText("先に記事を生成してください。")
            return

        try:
            # ===== カテゴリ判定 =====
            category = self.detect_background_category(self.generated_title)
            # ===== ベース画像 =====
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            base_path = os.path.join(BASE_DIR, "assets", f"note_base_{category}.jpg")

            if not os.path.exists(base_path):
              base_path = os.path.join(
                  BASE_DIR,
                  "assets",
                  "note_base_default.jpg"
              )
            image = Image.open(base_path).convert("RGB")
            draw = ImageDraw.Draw(image)

            # ===== フォント設定 =====
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            font_path = os.path.join(
                BASE_DIR,
                "assets",
                "fonts",
                "NotoSansJP-Regular.ttf"
            )
            title_font = ImageFont.truetype(font_path, 48)
            date_font = ImageFont.truetype(font_path, 28)

            # ===== テキスト =====
            title = self.generated_title
            date_text = datetime.now().strftime("%Y.%m.%d")

            # ===== タイトル折り返し =====
            max_width = 900
            lines = []
            current = ""

            for char in title:
                test = current + char

                bbox = draw.textbbox((0, 0), test, font=title_font)
                w = bbox[2] - bbox[0]

                if w <= max_width:
                    current = test
                else:
                    lines.append(current)
                    current = char

            if current:
                lines.append(current)

            # ===== 描画位置 =====
            x = 100
            y = 300
            line_height = 60  # 行間（調整可）

            for line in lines:
                draw.text((x, y), line, font=title_font, fill="white")
                y += line_height

            draw.text((x, y + 20), date_text, font=date_font, fill="white")

            # ===== 保存 =====
            output_path = os.path.join("assets", "note_output.jpg")
            image.save(output_path)

            self.status_label.setText("NOTE用画像を生成しました。")


        except Exception as e:
            self.status_label.setText(f"画像生成エラー: {e}")
