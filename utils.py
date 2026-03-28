# utils.py
# 共通ユーティリティ関数群

import re
import streamlit as st

# ==========================================================
# フィルタ関数
# ==========================================================
def strip_thought(text: str) -> str:
    """
    LLM出力から思考部分を削除し、患者の発話だけを返す
    """

    if not text:
        return text

    # THOUGHT削除
    text = re.sub(r"THOUGHT.*?回答[:：]", "", text, flags=re.DOTALL)
    text = re.sub(r"THOUGHT.*", "", text)

    # 回答ラベル削除
    text = re.sub(r"回答[:：]", "", text)

    # 🔥 発話がある場合はそこだけ残す
    if "発話：" in text:
        text = text.split("発話：")[-1]

    return text.strip()


# ==========================================================
# セッションリセット関数
# ==========================================================
def reset_session():
    for key in ["chat_history", "chat_session", "current_scenario"]:
        if key in st.session_state:
            del st.session_state[key]