from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QTextEdit
from PySide6.QtCore import Qt

import datetime
import os.path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class CalendarTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.info_label = QLabel("Google Calendar の予定を取得できます")
        layout.addWidget(self.info_label)

        self.button = QPushButton("予定を取得する")
        self.button.clicked.connect(self.load_events)
        layout.addWidget(self.button)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_box)

        self.setLayout(layout)

    def load_events(self):
        creds = None

        # token.json があれば再利用
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        # 認証が必要な場合
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)

            # 認証情報を保存
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        # Calendar API に接続
        service = build("calendar", "v3", credentials=creds)

        # 今日〜7日後までの予定を取得
        now = datetime.datetime.utcnow().isoformat() + "Z"
        week_later = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat() + "Z"

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                timeMax=week_later,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        # 表示
        if not events:
            self.result_box.setText("今後1週間の予定はありません。")
            return

        text = ""
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            summary = event.get("summary", "（タイトルなし）")
            text += f"{start} : {summary}\n"

        self.result_box.setText(text)