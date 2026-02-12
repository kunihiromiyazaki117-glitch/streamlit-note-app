from google.cloud import texttospeech
import os

# Google認証ファイルのパスを指定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

# クライアント作成
client = texttospeech.TextToSpeechClient()

# 読み上げたいテキスト
text = "デイリーニュースCFOのマークです。今日も3分で、あなたの情報武装をお手伝いします。"

# 入力テキスト
input_text = texttospeech.SynthesisInput(text=text)

# 声の設定（日本語・男性）
voice = texttospeech.VoiceSelectionParams(
    language_code="ja-JP",
    name="ja-JP-Neural2-D"
)

# 音声形式（MP3）
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)

# 音声生成
response = client.synthesize_speech(
    input=input_text,
    voice=voice,
    audio_config=audio_config
)

# 保存
with open("test_mark.mp3", "wb") as out:
    out.write(response.audio_content)

print("test_mark.mp3 を生成しました")
