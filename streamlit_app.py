import streamlit as st
import feedparser
import google.generativeai as genai
import re

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# =========================
# 記事解析関数
# =========================
def parse_article(text):
    # Extract sections using regex
    title_match = re.search(r'【TITLE】\s*(.*?)\s*【FREE】', text, re.DOTALL)
    free_match = re.search(r'【FREE】\s*(.*?)\s*【PAYWALL】', text, re.DOTALL)
    paid_match = re.search(r'【PAID】\s*(.*?)\s*【SNS】', text, re.DOTALL)
    sns_match = re.search(r'【SNS】\s*(.*?)\s*【HASHTAG】', text, re.DOTALL)
    hashtag_match = re.search(r'【HASHTAG】\s*(.*?)\s*【ニュース】', text, re.DOTALL)

    return {
        "title": title_match.group(1).strip() if title_match else "",
        "free": free_match.group(1).strip() if free_match else "",
        "paid": paid_match.group(1).strip() if paid_match else "",
        "sns": sns_match.group(1).strip() if sns_match else "",
        "hashtag": hashtag_match.group(1).strip() if hashtag_match else ""
    }

# =========================
# セッション管理
# =========================
if "free_article" not in st.session_state:
    st.session_state.free_article = None

if "paid_article" not in st.session_state:
    st.session_state.paid_article = None


# =========================
# ページ設定
# =========================
st.set_page_config(
    page_title="NOTE自動生成",
    layout="wide"
)

st.title("📝 NOTE記事ジェネレーター")
st.caption("ニュース選択 → NOTE記事生成（API節約設計）")

# =========================
# RSS 定義
# =========================
RSS_URLS = {
    "国内": "https://news.yahoo.co.jp/rss/topics/domestic.xml",
    "経済": "https://news.yahoo.co.jp/rss/topics/business.xml",
    "IT": "https://news.yahoo.co.jp/rss/topics/it.xml",
    "科学": "https://news.yahoo.co.jp/rss/topics/science.xml",
}

# =========================
# ニュース取得
# =========================
@st.cache_data(ttl=600)
def load_news():
    items = []
    for category, url in RSS_URLS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            items.append({
                "category": category,
                "title": entry.title,
                "summary": getattr(entry, "summary", "（概要なし）")
            })
    return items

# =========================
# STEP 1：ニュース選択
# =========================
st.subheader("① ニュースを選択")

with st.spinner("ニュース取得中…"):
    news_list = load_news()

labels = [
    f"[{n['category']}] {n['title']}"
    for n in news_list
]

selected_labels = st.multiselect(
    "NOTEに使うニュースを選んでください（複数可）",
    labels
)

selected_news = []
for label in selected_labels:
    for n in news_list:
        if label == f"[{n['category']}] {n['title']}":
            selected_news.append(n)
            break

# =========================
# STEP 2：選択内容確認
# =========================
if selected_news:
    st.subheader("② 選択中のニュース")

    for i, n in enumerate(selected_news, 1):
        st.markdown(f"### ニュース{i}")
        st.markdown(f"**カテゴリ**：{n['category']}")
        st.markdown(f"**タイトル**：{n['title']}")
        st.markdown(f"**概要**：{n['summary']}")

# =========================
# STEP 3：NOTE記事生成
# =========================
st.subheader("③ NOTE記事を生成（無料＋有料）")

if selected_news:
    if st.button("NOTE記事を生成する（無料＋有料）"):

        # ===== ニュースまとめ =====
        news_text = ""
        for i, n in enumerate(selected_news, 1):
            news_text += f"""
【ニュース{i}】
カテゴリ：{n['category']}
タイトル：{n['title']}
概要：{n['summary']}
"""

            prompt = f"""
あなたはNOTEで継続的に収益を上げているプロ編集者です。

以下のニュースを元に、
「無料部分」と「有料部分」が明確に分かれた
NOTE向け記事を1本作成してください。

【重要ルール】
- 煽らない
- 信頼感のある落ち着いた文体
- 社会人・ビジネスパーソン向け
- 専門用語は噛み砕いて説明
- 有料に価値が集まる構成にする

【文字量の目安】
- FREE：600〜800文字
- PAID：800〜1200文字

【出力形式（厳守）】
以下のタグを必ず使い、順番も変えないこと。

【TITLE】
記事タイトル（1行）

【FREE】
・導入
・ニュースの要点
・なぜ重要か
・「続きが読みたい」と思わせるところまで

【PAYWALL】
ここから先は有料です。
この続きでは、
・背景の深掘り
・本質的な構造
・今後の展開予測
・社会人が取るべき具体的アクション
を解説します。

【PAID】
・表に出ない背景
・因果関係の整理
・中長期的な影響
・読者が「知れてよかった」と思う視点

【SNS】
この記事を紹介するSNS用要約（140文字以内）

【HASHTAG】
この記事に関連するハッシュタグ（5個以内、#付きで）

【ニュース】
{news_text}
"""


            with st.spinner("NOTE記事を生成中…"):
                response = model.generate_content(prompt)
                text = response.text


            article = response.text
            st.session_state["article"] = article

            st.success("記事生成が完了しました！")

else:
    st.info("ニュースを選択すると有効になります。")

if "article" in st.session_state:
    article = parse_article(st.session_state["article"])

    st.subheader("📰 記事タイトル")
    st.code(article["title"], language="text")

    st.subheader("🆓 無料パート")
    st.code(article["free"], language="text")

    st.subheader("💰 有料パート")
    st.code(article["paid"], language="text")

    st.subheader("📣 SNS用要約")
    st.code(article["sns"], language="text")

    st.subheader("🏷️ ハッシュタグ")
    st.code(article["hashtag"], language="text")

    st.divider()
    st.subheader("🚀 投稿する")

    col1, col2 = st.columns(2)

    with col1:
        st.link_button(
            "📝 NOTEに投稿する",
            "https://note.com/notes/create"
        )

    with col2:
        st.link_button(
            "🐦 Xに投稿する",
            "https://twitter.com/intent/tweet"
        )





# =========================
# STEP 4：結果表示
# =========================
if "article" in st.session_state:
    st.subheader("④ 生成されたNOTE記事")

    st.text_area(
        "全文（コピーしてNOTEに貼り付けてください）",
        st.session_state["article"],
        height=600
    )

    st.link_button(
        "🌐 NOTE投稿ページを開く",
        "https://note.com/notes/new"
    )

# =========================
# フッター
# =========================
st.divider()
st.caption("STEP D 完了：NOTE記事生成")
