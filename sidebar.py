#sidebar.py
import streamlit as st
from utils import reset_session
from db import logout


def render_sidebar(
    SCENARIOS,
    SCENARIO_PROMPTS,
    current_datetime
):
    st.sidebar.header("📝 課題設定")

    # ============================
    # 課題選択
    # ============================
    mode = st.sidebar.selectbox("モード", list(SCENARIOS.keys()))
    scenario = st.sidebar.selectbox("課題", SCENARIOS[mode])
    subscenario = st.sidebar.selectbox(
        "サブシナリオ",
        list(SCENARIO_PROMPTS[mode][scenario].keys())
    )

    selected = SCENARIO_PROMPTS[mode][scenario][subscenario]

    from datetime import datetime
    today = datetime.now().strftime("%Y年%m月%d日")

    # 表示用（selectedは壊さない）
    task_info_display = {}
    for k, v in selected["task_info"].items():
        if isinstance(v, str):
            task_info_display[k] = v.replace("{{TODAY}}", today)
        else:
            task_info_display[k] = v

    # ============================
    # 課題詳細（折りたたみ）
    # ============================
    with st.sidebar.expander("📘 課題詳細", expanded=True):

        st.markdown("### 📘 課題内容")
        st.write(task_info_display["課題内容"])

        st.markdown("### 👤 患者情報")
        st.text(task_info_display["患者情報"])

        st.markdown("### 🧑‍⚕️ 医療従事者情報")
        st.text(task_info_display["医療従事者情報"])

        st.markdown("### 💊 処方内容")
        st.text(task_info_display["処方内容"])

        st.markdown(f"### 🕒 日時\n{current_datetime}")

    # ============================
    # セッションリセット
    # ============================
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 セッションをリセット"):
        reset_session()
        st.rerun()

    # ============================
    # AI評価
    # ============================
    st.sidebar.markdown("---")
    st.sidebar.subheader("📝 AI評価")

    if st.sidebar.button(
        "AIによる評価を実行",
        disabled=len(st.session_state.get("chat_history", [])) == 0
    ):
        st.session_state.run_evaluation = True

    # ============================
    # 設定
    # ============================
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ 設定")

    if st.sidebar.button("⚙️ ユーザー設定"):
        st.session_state.page = "settings"

    if st.sidebar.button("⬅ チャットに戻る"):
        st.session_state.page = "chat"

    # ============================
    # 教員専用
    # ============================
    if st.session_state.get("role") == "staff":
        st.sidebar.markdown("---")
        st.sidebar.subheader("👨‍🏫 教職員メニュー")

        if st.sidebar.button("📊 学生評価一覧"):
            st.session_state.page = "staff_dashboard"
            st.rerun()

    # ============================
    # ログイン情報
    # ============================
    st.sidebar.markdown("---")

    with st.sidebar.expander("👤 ログイン情報", expanded=True):
        st.write(f"**{st.session_state.get('email', '')}**")

        if st.button("🚪 ログアウト"):
            logout()
            st.rerun()

    # ============================
    # お問い合わせ
    # ============================
    with st.sidebar.expander("📩 お問い合わせ"):
        st.markdown("""
不具合や質問がある場合は  
✉ a22071@ug.shoyaku.ac.jp
""")

    # ============================
    # アンケート
    # ============================
    with st.sidebar.expander("📝 使用後アンケート"):
        st.markdown("[アンケートに回答する](https://forms.gle/JDxUAMchNLXoYsCYA)")
        st.image("images/form.png", use_container_width=True)

    # ============================
    # 開発者情報
    # ============================
    with st.sidebar.expander("🛠 開発者情報"):
        st.markdown("""
昭和薬科大学  
薬学部 数理科学 瀧澤研究室  

💊 患者・医療従事者役 AI シミュレーター  

開発：高嶋 貫多
""")

    st.sidebar.caption("Version 1.0")

    return mode, scenario, subscenario, selected
