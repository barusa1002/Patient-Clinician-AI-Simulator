# ui_settings.py
import streamlit as st
from db import supabase, get_current_user
from evaluation import load_user_evaluations

from ui_evaluation_viewer import (
    render_radar_chart,
    render_evaluation_history
)


def render_settings_page():

    st.header("⚙️ ユーザー設定")

    user = get_current_user()

    if not user:
        st.error("ログイン情報が見つかりません")
        return

    user_id = user.id
    email = user.email

    # ===============================
    # アカウント情報
    # ===============================
    st.subheader("👤 アカウント情報")
    st.markdown(f"**メールアドレス**： `{email}`")

    # ===============================
    # パスワード変更（Auth版）
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
            try:
                supabase.auth.update_user({
                    "password": new_password1
                })
                st.success("パスワードを変更しました")

            except Exception as e:
                st.error(f"変更に失敗しました: {e}")

    # ===============================
    # 音声設定
    # ===============================
    st.markdown("---")
    st.subheader("🔊 音声設定")

    st.session_state.autoplay_enabled = st.checkbox(
        "音声を自動再生する",
        value=st.session_state.get("autoplay_enabled", True)
    )

    st.session_state.speech_speed = st.radio(
        "話速",
        ["ゆっくり", "ふつう", "はやい"],
        index=["ゆっくり", "ふつう", "はやい"].index(
            st.session_state.get("speech_speed", "ふつう")
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
        st.session_state.show_tutorial = True
        st.session_state.tutorial_step = 0
        st.session_state.page = "chat"
        st.rerun()

    # ===============================
    # 戻る
    # ===============================
    st.markdown("---")

    if st.button("💬 チャット画面に戻る"):
        st.session_state.page = "chat"
        st.rerun()
