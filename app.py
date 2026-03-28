import streamlit as st
import os
from datetime import datetime

# ==========================================================
# ページ設定（必ず最初）
# ==========================================================
st.set_page_config(
    page_title="患者・医療従事者役 AI シミュレーター",
    layout="wide"
)

# ==========================================================
# CSS読み込み
# ==========================================================
def load_css():
    with open("components/highlight.css", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

load_css()

#ui_staff_dashboard.py
from ui_staff_dashboard import render_staff_dashboard

# ==========================================================
# チュートリアル
# ==========================================================
from tutorial import run_tutorial

# ==========================================================
# session 初期化
# ==========================================================
from session import init_session_state
init_session_state()

# ==========================================================
# スマホ判定（最も安定）
# ==========================================================
user_agent = st.context.headers.get("user-agent", "").lower()

if "is_mobile" not in st.session_state:

    user_agent = st.context.headers.get("user-agent", "").lower()

    st.session_state.is_mobile = any(
        keyword in user_agent
        for keyword in ["iphone", "android", "ipad"]
    )



# ==========================================================
# ページ管理
# ==========================================================
if "page" not in st.session_state:
    st.session_state.page = "chat"

# ==========================================================
# 認証
# ==========================================================
from auth import login_screen

if not st.session_state.logged_in:
    login_screen()
    st.stop()

# ==========================================================
# タイトル
# ==========================================================
st.title("患者・医療従事者役 AI シミュレーター")

# ==========================================================
# チュートリアル表示
# ==========================================================
# チュートリアル表示
if not st.session_state.get("tutorial_done", False):
    run_tutorial()


# ==========================================================
# 現在日時
# ==========================================================
current_datetime = datetime.now().strftime("%Y年%m月%d日 %H時%M分")

# ==========================================================
# APIキー
# ==========================================================
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
    API_KEY = os.environ["GEMINI_API_KEY"]
else:
    API_KEY = None

# ==========================================================
# Gemini Client
# ==========================================================

#config.py
from config import MODEL_NAME

#llm.py
from llm import get_client, start_chat

CLIENT = get_client(API_KEY)

if CLIENT is None:
    st.error("Gemini APIキーが設定されていません")
    st.stop()


#audio.py
from audio import speak_text, play_audio

# utils.py
from utils import strip_thought, reset_session


#evaluation.py
from evaluation import (
    build_evaluation_prompt,
    save_evaluation,
    load_user_evaluations
)

#prompts.py
from prompts import (
    MODE_PROMPTS,
    SCENARIOS,
    SCENARIO_PROMPTS
)

#sidebar.py
from sidebar import render_sidebar

mode, scenario, subscenario, selected = render_sidebar(
    SCENARIOS,
    SCENARIO_PROMPTS,
    current_datetime
)

# ==========================================================
# チャット初期化関数
# ==========================================================
import re
from datetime import datetime, timedelta

def replace_date_templates(text):

    today = datetime.now()

    pattern = r"\{\{TODAY([+-]\d+)?([DY])?\}\}"

    def repl(match):

        number = match.group(1)
        unit = match.group(2)

        date = today

        if number and unit:

            value = int(number)

            if unit == "D":
                date = today + timedelta(days=value)

            elif unit == "Y":
                date = today + timedelta(days=365 * value)

        return date.strftime("%Y年%m月%d日")

    return re.sub(pattern, repl, text)

def init_chat_session(mode, selected):
    for k, v in selected["task_info"].items():
        if isinstance(v, str):
            selected["task_info"][k] = replace_date_templates(v)

    # 人間が読む形式に整形
    task_text = "\n".join(
        f"【{k}】\n{v}" for k, v in selected["task_info"].items()
    )

    system_prompt = (
        MODE_PROMPTS[mode]
        + "\n\n"
        + task_text
        + "\n\n"
        + selected["prompt"]
    )

    return start_chat(
        client=CLIENT,
        model_name=MODEL_NAME,
        system_prompt=system_prompt
    )

# ==========================================================
# チャット初期化
# ==========================================================
scenario_key = f"{mode}-{scenario}-{subscenario}"

if "current_scenario" not in st.session_state:
    st.session_state.current_scenario = scenario_key

if st.session_state.current_scenario != scenario_key:
    st.session_state.chat_history = []
    st.session_state.chat_session = init_chat_session(
        mode=mode,
        selected=selected
    )
    st.session_state.current_scenario = scenario_key

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==========================================================
# チャット開始
# ==========================================================
if st.session_state.get("chat_session") is None:
    st.session_state.chat_session = init_chat_session(
        mode=mode,
        selected=selected
    )


# ui_setting.py
from ui_settings import render_settings_page

#ui_chat.py
from ui_chat import render_chat_page


# ==========================================================
# メイン画面 分岐
# ==========================================================
if st.session_state.page == "chat":
    render_chat_page(
    scenario=scenario,
    subscenario=subscenario,
    chat_session=st.session_state.chat_session
    )


elif st.session_state.page == "settings":
    render_settings_page()
elif st.session_state.page == "staff_dashboard":
    if st.session_state.role != "staff":
        st.error("このページは教職員専用です")
    else:
        render_staff_dashboard()
