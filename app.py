#app.py
import streamlit as st
import os
from datetime import datetime, timedelta

# ==========================================================
# ページ設定（⚠️最上部）
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

# モバイル向け追加スタイル（フォールバック用インライン）
st.markdown("""
<style>
/* モバイル：タイトル圧縮 */
@media screen and (max-width: 768px) {
    h1 { font-size: 1.1rem !important; padding-top: 0 !important; margin-top: 0 !important; }
    h2 { font-size: 0.95rem !important; }
    .main .block-container { padding-top: 0.4rem !important; }
    /* Streamlit デフォルトの上部余白を削減 */
    .stAppViewBlockContainer { padding-top: 0.5rem !important; }
}
/* チャット入力を常に下部に固定 */
[data-testid="stBottom"] {
    background: rgba(14, 17, 23, 0.92) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border-top: 1px solid rgba(255,255,255,0.08) !important;
    padding: 0.5rem 0.75rem !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# URLフラグメント → クエリパラメータ変換（パスワードリセット用）
# ==========================================================
import streamlit.components.v1 as components
components.html("""
<script>
(function() {
    var hash = window.parent.location.hash;
    if (hash && hash.includes('type=recovery')) {
        var params = hash.substring(1);
        window.parent.location.replace('/?' + params);
    }
})();
</script>
""", height=0)

# ==========================================================
# セッション初期化
# ==========================================================
from session import init_session_state
init_session_state()

# ==========================================================
# パスワードリセットリンク経由の検出
# ==========================================================
from auth import login_screen, show_reset_password_form

query = st.query_params
if query.get("type") == "recovery":
    access_token = query.get("access_token", "")
    refresh_token = query.get("refresh_token", "")
    show_reset_password_form(access_token, refresh_token)
    st.stop()

# ==========================================================
# Supabase Auth
# ==========================================================
from db import get_current_user, logout, supabase

user = get_current_user()

if not user:
    login_screen()
    st.stop()

# ==========================================================
# ⏱ 自動ログアウト
# ==========================================================
TIMEOUT_MINUTES = 30

def check_auto_logout(user_id: str):
    from datetime import timezone

    now_local = datetime.now()
    last_activity = st.session_state.get("last_activity")

    if last_activity is None:
        # 新しいセッション or 再接続 → DBの last_active_at で判定
        if "db_last_active_at" not in st.session_state:
            try:
                res = supabase.table("profiles") \
                    .select("last_active_at") \
                    .eq("id", user_id) \
                    .execute()
                if res.data and res.data[0].get("last_active_at"):
                    raw = res.data[0]["last_active_at"]
                    st.session_state["db_last_active_at"] = datetime.fromisoformat(
                        raw.replace("Z", "+00:00")
                    )
            except Exception:
                pass

        db_last = st.session_state.get("db_last_active_at")
        if db_last:
            now_utc = datetime.now(timezone.utc)
            if (now_utc - db_last) > timedelta(minutes=TIMEOUT_MINUTES):
                st.query_params["expired"] = "1"
                logout()
                return
    else:
        # 既存セッション → session_state で判定
        if (now_local - last_activity) > timedelta(minutes=TIMEOUT_MINUTES):
            st.query_params["expired"] = "1"
            logout()
            return

    st.session_state.last_activity = now_local

    # DB書き込みは1分に1回に制限
    last_db_write = st.session_state.get("_last_db_activity_write")
    if last_db_write is None or (now_local - last_db_write) > timedelta(minutes=1):
        try:
            now_utc = datetime.now(timezone.utc)
            supabase.table("profiles") \
                .update({"last_active_at": now_utc.isoformat()}) \
                .eq("id", user_id) \
                .execute()
            st.session_state["_last_db_activity_write"] = now_local
        except Exception:
            pass


check_auto_logout(user.id)

# ==========================================================
# セッションに基本情報保存
# ==========================================================
st.session_state.user_id = user.id
st.session_state.email = user.email

# ==========================================================
# 🔥 role & tutorial取得
# ==========================================================
profile = supabase.table("profiles") \
    .select("*") \
    .eq("id", user.id) \
    .execute()

if profile.data and len(profile.data) > 0:
    row = profile.data[0]
    st.session_state.role = row.get("role") or "student"
    st.session_state.tutorial_done = row.get("tutorial_done") is True
else:
    st.session_state.role = "student"
    st.session_state.tutorial_done = False

# ==========================================================
# スマホ判定（タイトル表示前に実施）
# ==========================================================
from utils import strip_thought, reset_session, detect_mobile

if "is_mobile" not in st.session_state:
    st.session_state.is_mobile = detect_mobile()

# ==========================================================
# タイトル
# ==========================================================
st.title("患者・医療従事者役 AI シミュレーター")

# ==========================================================
# チュートリアル（🔥最優先）
# ==========================================================
from tutorial import run_tutorial

if (
    not st.session_state.get("tutorial_done", False)
    or st.session_state.get("show_tutorial", False)
):
    run_tutorial()

# ==========================================================
# 学習モード選択
# ==========================================================
from ui_mode_select import render_mode_select_page

if "learning_mode" not in st.session_state:
    render_mode_select_page()
    st.stop()

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

st.session_state.gemini_client = CLIENT

# ==========================================================
# その他import
# ==========================================================
from audio import speak_text, play_audio

from evaluation import (
    build_evaluation_prompt,
    save_evaluation,
    load_user_evaluations
)

# 学習モードに応じてプロンプトセットを切り替え
_learning_mode = st.session_state.get("learning_mode", "OSCE対策")

if _learning_mode == "実習前練習":
    from prompts_jisshu import (
        JISSHU_MODE_PROMPTS as MODE_PROMPTS,
        JISSHU_SCENARIOS as SCENARIOS,
        JISSHU_SCENARIO_PROMPTS as SCENARIO_PROMPTS,
    )
elif _learning_mode == "初期研修":
    from prompts_kenshu import (
        KENSHU_MODE_PROMPTS as MODE_PROMPTS,
        KENSHU_SCENARIOS as SCENARIOS,
        KENSHU_SCENARIO_PROMPTS as SCENARIO_PROMPTS,
    )
else:  # OSCE対策（デフォルト）
    from prompts import (
        MODE_PROMPTS,
        SCENARIOS,
        SCENARIO_PROMPTS,
    )

# ==========================================================
# 🔥 サイドバー（チュートリアル後に実行）
# ==========================================================
from sidebar import render_sidebar

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
        chat_session=st.session_state.chat_session,
        selected=selected
    )

elif st.session_state.page == "settings":
    render_settings_page()

elif st.session_state.page == "staff_dashboard":

    if st.session_state.get("role") != "staff":
        st.error("このページにアクセスする権限がありません")
    else:
        render_staff_dashboard()
