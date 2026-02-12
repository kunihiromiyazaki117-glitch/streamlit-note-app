from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton,
    QTextEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
import feedparser
from dotenv import load_dotenv
import os

from google import genai


class NewsTab(QWidget):
    def __init__(self):
        super().__init__()

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)

        layout = QVBoxLayout()

        self.info_label = QLabel("ニュース一覧 → 選択 → Gemini 台本生成")
        layout.addWidget(self.info_label)

        self.news_list = QListWidget()
        self.news_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.news_list)

        self.load_button = QPushButton("ニュースを読み込む")
        self.load_button.clicked.connect(self.load_news)
        layout.addWidget(self.load_button)

        self.script_button = QPushButton("選択したニュースで台本を作成")
        self.script_button.clicked.connect(self.generate_script)
        layout.addWidget(self.script_button)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_box)

        self.setLayout(layout)

        self.news_entries = []


    def load_news(self):
        """国内・経済・IT・科学のニュースをカテゴリごとに10件ずつ取得"""

        rss_urls = [
            ("国内", "https://news.yahoo.co.jp/rss/topics/domestic.xml"),
            ("経済", "https://news.yahoo.co.jp/rss/topics/business.xml"),
            ("IT", "https://news.yahoo.co.jp/rss/topics/it.xml"),
            ("科学", "https://news.yahoo.co.jp/rss/topics/science.xml"),
        ]

        self.news_list.clear()
        self.news_entries = []

        for category, url in rss_urls:

            # 見出し（選択不可）
            header = QListWidgetItem(f"=== {category} ===")
            header.setFlags(header.flags() & ~Qt.ItemIsSelectable)
            self.news_list.addItem(header)

            feed = feedparser.parse(url)
            entries = feed.entries[:10]

            for entry in entries:
                title = entry.title
                summary = getattr(entry, "summary", None)
                if summary is None:
                    summary = getattr(entry, "description", "（概要なし）")

                # news_entries に追加
                index = len(self.news_entries)
                self.news_entries.append({
                    "category": category,
                    "title": title,
                    "summary": summary
                })

                # ListWidgetItem に index を埋め込む
                item = QListWidgetItem(f"[{category}] {title}")
                item.setData(Qt.UserRole, index)
                self.news_list.addItem(item)

        self.result_box.setText("カテゴリ別ニュースを読み込みました。")


    def generate_script(self):
        """選択したニュースをまとめて台本生成"""

        selected_items = self.news_list.selectedItems()

        if not selected_items:
            self.result_box.setText("ニュースが選択されていません。")
            return

        selected_news = []

        for item in selected_items:
            index = item.data(Qt.UserRole)
            if index is None:
                continue  # 見出し行はスキップ
            selected_news.append(self.news_entries[index])

        if not selected_news:
            self.result_box.setText("ニュースが選択されていません。")
            return

        # Gemini に渡す文章を作成
        news_text = ""
        for i, news in enumerate(selected_news, start=1):
            news_text += f"【ニュース{i}】\nタイトル: {news['title']}\n概要: {news['summary']}\n\n"

        prompt = f"""
あなたは「デイリーニュースCFO マーク」というキャラクターとして話します。

【キャラクター設定】
- 年齢：38歳の男性
- 職業：企業のCFO（Chief Friendly Officer）
- 経歴：元コンサル、元新聞社の経済部記者、現在は経営企画室で働く社会人
- 性格：落ち着いていて論理的、視聴者に寄り添う、事実ベースで淡々と説明
- 話し方：丁寧で落ち着いたテンポ、語尾は「〜です」「〜ですね」
- 口癖：「今日も3分で、あなたの情報武装をお手伝いします」「ポイントを簡潔に整理しますね」
- 禁止事項：キャラを変えない、口調を変えない、若者言葉を使わない、感情的にならない、他のキャラを登場させない

【見た目】
- 黒髪の短髪、細いフレームの眼鏡
- ネイビーのスーツ、白シャツ、落ち着いた色のネクタイ
- 穏やかな目元で、落ち着いた雰囲気
- 声は低めで聞き取りやすい

【冒頭の挨拶】
必ず次の文言から始めてください：
「デイリーニュースCFOのマークです。今日も3分で、あなたの情報武装をお手伝いします。」

【構成テンプレート】
1. 導入（20秒）
    - 固定挨拶
    - 今日扱うニュースの概要
    - 視聴者のメリット提示

2. 本編（100〜130秒）
    ニュースごとに以下を説明：
    - 要点（30文字以内）
    - 背景（なぜ起きたのか）
    - 社会人にとっての影響（ビジネス視点）
    - 今後どうなるか（短期予測）

3. まとめ（30秒）
    - 今日のポイントを3つに整理
    - 明日へのアクションを一言
    - 固定の締めの挨拶

【対象ニュース】
{news_text}

全体で150〜180秒程度のスクリプトにまとめてください。
"""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        self.result_box.setText(response.text)