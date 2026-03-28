#sidebar.py
import streamlit as st
from utils import reset_session

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

    # sidebar表示専用（selectedは壊さない）
    task_info_display = {}
    for k, v in selected["task_info"].items():
        if isinstance(v, str):
            task_info_display[k] = v.replace("{{TODAY}}", today)
        else:
            task_info_display[k] = v


    # ============================
    # 情報表示
    # ============================
    st.sidebar.markdown("### 📘 課題内容")
    st.sidebar.write(task_info_display["課題内容"])

    st.sidebar.markdown("### 👤 患者情報")
    st.sidebar.text(task_info_display["患者情報"])

    st.sidebar.markdown("### 🧑‍⚕️ 医療従事者情報")
    st.sidebar.text(task_info_display["医療従事者情報"])

    st.sidebar.markdown("### 💊 処方内容")
    st.sidebar.text(task_info_display["処方内容"])

    st.sidebar.markdown(f"### 🕒 日時\n{current_datetime}")

    # ============================
    # セッションリセット
    # ============================
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 セッションをリセット", key="reset_session"):
        reset_session()
        st.rerun()

    # ============================
    # AI評価
    # ============================
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📝 AI評価")

    if st.sidebar.button(
        "AIによる評価を実行",
        disabled=len(st.session_state.get("chat_history", [])) == 0,
        key="run_eval"
    ):
        st.session_state.run_evaluation = True

    # ============================
    # 設定メニュー
    # ============================
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ 設定")

    if st.sidebar.button("⚙️ ユーザー設定", key="go_settings"):
        st.session_state.page = "settings"

    if st.sidebar.button("⬅ チャットに戻る", key="go_chat"):
        st.session_state.page = "chat"

    # ============================
    # 🔐 教職員専用メニュー
    # ============================
    st.sidebar.markdown("---")
    if st.session_state.get("role") == "staff":
        st.sidebar.markdown("### 👨‍🏫 教職員メニュー")
        if st.sidebar.button("📊 学生評価一覧"):
            st.session_state.page = "staff_dashboard"
            st.rerun()
    
    # ============================
    # ログイン情報
    # ============================
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 ログイン中")
    st.sidebar.write(f"ユーザー：**{st.session_state.get('username', '')}**")

    if st.sidebar.button("🚪 ログアウト", key="logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.chat_history = []
        st.session_state.page = "chat"
        st.rerun()

    st.sidebar.markdown("---")

    st.sidebar.markdown("### 📩 お問い合わせ")
    st.sidebar.markdown(
    """
    不具合や質問がある場合は  
    以下までご連絡ください。

    ✉ a22071@ug.shoyaku.ac.jp
    """
    )

    st.sidebar.markdown(
    """
    ### 📝 使用後アンケート

    以下のフォームからご回答ください👇  
    [アンケートに回答する](https://forms.gle/JDxUAMchNLXoYsCYA)
    """
    )

    st.sidebar.image(
        "images/form.png",
        caption="QRコードから回答できます",
        use_container_width=True
    )

    st.sidebar.markdown("### 🛠 開発者情報")
    st.sidebar.markdown(
    """
    昭和薬科大学  
    薬学部 数理科学瀧澤研究室  
    💊 患者・医療従事者役 AI シミュレーター  

    開発：高嶋 貫多
    """
    )

    st.sidebar.caption("Version 1.0")

    return mode, scenario, subscenario, selected






