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
    now_utc = datetime.now(timezone.utc)
    last_activity = st.session_state.get("last_activity")

    if last_activity is None:
        # ── 新規セッション（ブラウザ再起動・再接続） ──────────────
        # DBの最終操作時刻を毎回直接取得して判定する
        # （session_state のキャッシュは使わず、常に最新値を参照）
        try:
            res = supabase.table("profiles") \
                .select("last_active_at") \
                .eq("id", user_id) \
                .execute()
            if res.data and res.data[0].get("last_active_at"):
                raw = res.data[0]["last_active_at"]
                db_last = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if (now_utc - db_last) > timedelta(minutes=TIMEOUT_MINUTES):
                    st.query_params["expired"] = "1"
                    logout()
                    return
        except Exception:
            pass  # DB読み取り失敗時はログアウトしない
    else:
        # ── 継続セッション ────────────────────────────────────────
        # 最後の操作（rerun）から30分経過していればログアウト
        if (now_local - last_activity) > timedelta(minutes=TIMEOUT_MINUTES):
            st.query_params["expired"] = "1"
            logout()
            return

    # 最終操作時刻を現在時刻に更新
    st.session_state["last_activity"] = now_local

    # DBへの書き込みは30秒に1回に制限
    last_db_write = st.session_state.get("_last_db_activity_write")
    if last_db_write is None or (now_local - last_db_write) > timedelta(seconds=30):
        try:
            supabase.table("profiles") \
                .update({"last_active_at": now_utc.isoformat()}) \
                .eq("id", user_id) \
                .execute()
            st.session_state["_last_db_activity_write"] = now_local
        except Exception:
            pass


check_auto_logout(user.id)

# ==========================================================
# ブラウザ側の非活動タイマー
# Streamlit はユーザー操作がなければ app.py を再実行しないため、
# サーバーサイドのみでは自動ログアウトが発動しない。
# JS タイマーで 30 分間操作がなければ ?expired=1 へリダイレクトする。
# ==========================================================
_timeout_ms = TIMEOUT_MINUTES * 60 * 1000
_uid = user.id
components.html(f"""
<script>
(function() {{
    var p = window.parent;
    var timeoutMs = {_timeout_ms};
    // ユーザーIDをキーに含めて別アカウントと干渉しない
    var STORAGE_KEY = '__sim_last_activity_{_uid}';

    // ① ページロード時チェック（タブ再オープン・リロード後もここで判定）
    try {{
        var stored = p.localStorage.getItem(STORAGE_KEY);
        if (stored && (Date.now() - parseInt(stored)) > timeoutMs) {{
            p.localStorage.removeItem(STORAGE_KEY);
            p.location.href = '/?expired=1';
            return;
        }}
    }} catch(e) {{}}

    // ② 現在時刻を記録（rerun = 何らかの操作あり）
    try {{ p.localStorage.setItem(STORAGE_KEY, Date.now()); }} catch(e) {{}}

    // ③ 初回のみイベントリスナーとインターバルをセットアップ（重複防止）
    if (!p.__idleWatcherActive) {{
        p.__idleWatcherActive = true;

        function resetActivity() {{
            try {{ p.localStorage.setItem(STORAGE_KEY, Date.now()); }} catch(e) {{}}
        }}

        ['mousemove', 'mousedown', 'keypress', 'touchstart', 'scroll', 'click'].forEach(function(evt) {{
            p.document.addEventListener(evt, resetActivity, {{passive: true, capture: true}});
        }});

        // 30秒ごとにアイドル時間をチェック（タブが開いたままの場合）
        p.__idleInterval = setInterval(function() {{
            try {{
                var last = parseInt(p.localStorage.getItem(STORAGE_KEY) || Date.now());
                if (Date.now() - last > timeoutMs) {{
                    clearInterval(p.__idleInterval);
                    p.__idleWatcherActive = false;
                    p.localStorage.removeItem(STORAGE_KEY);
                    p.location.href = '/?expired=1';
                }}
            }} catch(e) {{}}
        }}, 30000);
    }}
}})();
</script>
""", height=0)

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
_learning_mode = st.session_state.get("learning_mode", "スタンダードモード")

if _learning_mode == "スキルアップモード":
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
else:  # スタンダードモード（デフォルト）
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

    _no_thinking = (
        "\n\n【絶対ルール - 最優先】"
        "思考過程・分析・理由づけ・判断プロセスを一切テキストとして出力してはならない。"
        "キャラクターのセリフ文のみを出力すること。"
        "「Response:」「回答:」「発言:」などのラベルを先頭に付けることも禁止。"
        "「課題は」「〜すべき」「〜が最も無難」「〜が適切」「〜を返す」"
        "「〜はず」「〜べき」など推論を示す表現で始まる文は絶対に出力禁止。"
    )

    system_prompt = (
        MODE_PROMPTS[mode]
        + "\n\n"
        + task_text
        + "\n\n"
        + selected["prompt"]
        + _no_thinking
    )

    return start_chat(
        client=CLIENT,
        model_name=MODEL_NAME,
        system_prompt=system_prompt,
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
    st.session_state.pop("prescription_notes", None)
    st.session_state.pop("prescription_submitted", None)

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
