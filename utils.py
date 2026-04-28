# utils.py
# 共通ユーティリティ関数群


import re
import streamlit as st

# Gemini 2.5が思考プロセスを出力するときに現れるキーワード一覧
# （患者の実際のセリフには絶対に現れない語句のみ登録する）
_THINKING_INDICATORS = [
    "ユーザーは",
    "私は患者役",
    "患者役として",
    "前の回答で",
    "と答えるのが適切",
    "と返答するのが適切",
    "と答えるのが自然",
    "と答えるべき",
    "質問されたことに答える",
    "のみを返す",
    "のみ答える",
    "のみ出力する",
    "患者情報に",
    "課題は",
    "最も無難",
    "受け答えが良い",
    "説明を促す",
    "避けるべき",
]

# ==========================================================
# フィルタ関数
# ==========================================================
def strip_thought(text: str) -> str:
    """
    LLM出力から思考部分を削除し、患者の発話だけを返す
    """

    if not text:
        return text

    # THOUGHT削除（明示ラベルあり）
    text = re.sub(r"THOUGHT.*?回答[:：]", "", text, flags=re.DOTALL)
    text = re.sub(r"THOUGHT.*", "", text)

    # 先頭のラベル削除（Response: / 回答: / 発言: など）
    text = re.sub(r"^(Response|回答|発言|セリフ|患者|返答)[:：]\s*", "", text, flags=re.IGNORECASE)

    # 発話ラベルがある場合はそこだけ残す
    if "発話：" in text:
        text = text.split("発話：")[-1]

    # Gemini 2.5の暗黙的思考対応（1）：
    # 空行区切りで複数段落がある場合は最後の段落のみ残す
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) > 1:
        text = paragraphs[-1]

    # Gemini 2.5の暗黙的思考対応（2）：
    # 思考キーワードが含まれる場合、「。」で分割して最後の文だけを返す
    # （最後の文がメタ言語でない場合のみ採用）
    if any(kw in text for kw in _THINKING_INDICATORS):
        sentences = [s.strip() for s in text.split("。") if s.strip()]
        if sentences:
            last = sentences[-1]
            if not any(kw in last for kw in _THINKING_INDICATORS):
                if not last.endswith(("。", "？", "！")):
                    last += "。"
                text = last

    return text.strip()


# ==========================================================
# モバイル判定関数
# ==========================================================
MOBILE_KEYWORDS = ["iphone", "android", "ipad", "mobile", "blackberry", "windows phone"]

def detect_mobile() -> bool:
    """
    User-Agentを解析してモバイル端末かどうか判定する
    """
    try:
        user_agent = st.context.headers.get("user-agent", "").lower()
        return any(keyword in user_agent for keyword in MOBILE_KEYWORDS)
    except Exception:
        return False


# ==========================================================
# セッションリセット関数
# ==========================================================
def reset_session():
    for key in [
        "chat_history", "chat_session", "current_scenario",
        "prescription_notes", "prescription_submitted",
        "model_answer_text", "evaluation_done", "last_evaluation_json",
        "hint_text", "run_evaluation",
    ]:
        if key in st.session_state:
            del st.session_state[key]
