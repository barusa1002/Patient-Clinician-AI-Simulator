# ui_settings.py
import streamlit as st

from auth import update_user_id, update_password
from evaluation import load_user_evaluations

# ★ 追加（超重要）
from ui_evaluation_viewer import (
    render_radar_chart,
    render_evaluation_history
)


def render_settings_page():

    st.header("⚙️ ユーザー設定")

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("ログイン情報が見つかりません")
        return

    st.subheader("👤 アカウント情報")
    st.markdown(f"**現在のID**： `{user_id}`")

    # ===============================
    # ID変更
    # ===============================
    st.markdown("### 🆔 ID変更")
    new_id = st.text_input("新しいID").strip()

    if st.button("IDを変更"):
        if not new_id:
            st.error("新しいIDを入力してください")

        elif update_user_id(user_id, new_id):
            st.session_state.user_id = new_id
            st.session_state.username = new_id
            st.success("IDを変更しました")
            st.rerun()
        else:
            st.error("そのIDは使用できません")

    # ===============================
    # パスワード変更
    # ===============================
    st.subheader("🔐 パスワード変更")

    new_password1 = st.text_input("新しいパスワード", type="password", key="settings_new_pass1")
    new_password2 = st.text_input("新しいパスワード（確認）", type="password", key="settings_new_pass2")

    if st.button("パスワードを変更", key="settings_change_pass_btn"):
        if not new_password1 or not new_password2:
            st.error("パスワードを入力してください")
        elif new_password1 != new_password2:
            st.error("パスワードが一致しません")
        else:
            update_password(user_id, new_password1)
            st.success("パスワードを変更しました")

    # ===============================
    # 音声設定
    # ===============================
    st.markdown("---")
    st.subheader("🔊 音声設定")

    st.session_state.autoplay_enabled = st.checkbox(
        "音声を自動再生する",
        value=st.session_state.autoplay_enabled
    )

    st.session_state.speech_speed = st.radio(
        "話速",
        ["ゆっくり", "ふつう", "はやい"],
        index=["ゆっくり", "ふつう", "はやい"].index(
            st.session_state.speech_speed
        )
    )

    # ===============================
    # レーダーチャート
    # ===============================
    st.markdown("## 📊 9課題の達成率")

    mode = st.radio(
        "表示方法",
        ["平均", "最高", "最新"],
        horizontal=True
    )

    evaluations = load_user_evaluations(user_id)

    render_radar_chart(evaluations, mode)

    # ===============================
    # 評価履歴
    # ===============================
    st.markdown("---")
    st.subheader("📚 評価履歴")

    render_evaluation_history(evaluations, show_detail=True)

    # ===============================
    # チュートリアル
    # ===============================
    st.markdown("---")

    st.subheader("チュートリアル")

    st.write("チュートリアルをもう一度確認できます。")

    if st.button("📘 チュートリアルを見る"):
        st.session_state.tutorial_done = False
        st.session_state.tutorial_step = 0
        st.rerun()

    # ===============================
    # 戻る
    # ===============================
    st.markdown("---")

    if st.button("💬 チャット画面に戻る"):
        st.session_state.page = "chat"
        st.rerun()