import streamlit as st
import os
from datetime import datetime

# ==========================================================
# ページ設定
# ==========================================================
st.set_page_config(
    page_title="患者・医療従事者役 AI シミュレーター",
    layout="wide"
)

# ==========================================================
# CSS読み込み
# ==========================================================
def load_css():
    try:
        with open("components/highlight.css", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

load_css()

# ==========================================================
# セッション初期化
# ==========================================================
from session import init_session_state
init_session_state()

# ==========================================================
# Supabase Auth（最重要）
# ==========================================================
from db import get_current_user, logout, supabase
from auth import login_screen

user = get_current_user()

if not user:
    login_screen()
    st.stop()

st.session_state.user_id = user.id
st.session_state.email = user.email

# ==========================================================
# role取得（RLSと一致）
# ==========================================================
profile = supabase.table("profiles") \
    .select("role") \
    .eq("id", user.id) \
    .execute()

role = profile.data[0]["role"] if profile.data else "student"

# ==========================================================
# タイトル・ログアウト
# ==========================================================
st.title("患者・医療従事者役 AI シミュレーター")

st.sidebar.write(f"ログイン中: {user.email}")

if st.sidebar.button("ログアウト"):
    logout()

# ==========================================================
# チュートリアル
# ==========================================================
from tutorial import run_tutorial

if not st.session_state.get("tutorial_done", False):
    run_tutorial()

# ==========================================================
# スマホ判定
# ==========================================================
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
# APIキー
# ==========================================================
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
    API_KEY = os.environ["GEMINI_API_KEY"]
else:
    API_KEY = None

# ==========================================================
# Gemini
# ==========================================================
from config import MODEL_NAME
from llm import get_client, start_chat

CLIENT = get_client(API_KEY)

if CLIENT is None:
    st.error("Gemini APIキーが設定されていません")
    st.stop()

# ==========================================================
# その他import
# ==========================================================
from audio import speak_text, play_audio
from utils import strip_thought, reset_session

from evaluation import (
    build_evaluation_prompt,
    save_evaluation,
    load_user_evaluations
)

from prompts import (
    MODE_PROMPTS,
    SCENARIOS,
    SCENARIO_PROMPTS
)

from sidebar import render_sidebar

# ==========================================================
# 現在日時
# ==========================================================
current_datetime = datetime.now().strftime("%Y年%m月%d日 %H時%M分")

mode, scenario, subscenario, selected = render_sidebar(
    SCENARIOS,
    SCENARIO_PROMPTS,
    current_datetime
)

# ==========================================================
# 日付テンプレ置換
# ==========================================================
import re
from datetime import timedelta

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

# ==========================================================
# チャット初期化
# ==========================================================
def init_chat_session(mode, selected):

    for k, v in selected["task_info"].items():
        if isinstance(v, str):
            selected["task_info"][k] = replace_date_templates(v)

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
# シナリオ切替検知
# ==========================================================
scenario_key = f"{mode}-{scenario}-{subscenario}"

if "current_scenario" not in st.session_state:
    st.session_state.current_scenario = scenario_key

if st.session_state.current_scenario != scenario_key:
    st.session_state.chat_history = []
    st.session_state.chat_session = init_chat_session(mode, selected)
    st.session_state.current_scenario = scenario_key

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if st.session_state.get("chat_session") is None:
    st.session_state.chat_session = init_chat_session(mode, selected)

# ==========================================================
# UI
# ==========================================================
from ui_chat import render_chat_page
from ui_settings import render_settings_page
from ui_staff_dashboard import render_staff_dashboard

# ==========================================================
# ページ分岐
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

    if role != "teacher":
        st.error("このページは教員専用です")
    else:
        render_staff_dashboard()
