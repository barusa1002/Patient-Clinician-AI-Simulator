#ui_staff_dashboard.py
import streamlit as st
from db import supabase, get_current_user
from ui_evaluation_viewer import (
    render_radar_chart,
    render_evaluation_history
)


# ===============================
# 全評価取得（RLS前提）
# ===============================
def load_all_evaluations():

    res = supabase.table("evaluations") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()

    return res.data


# ===============================
# ユーザーごとに整理
# ===============================
def group_by_user(evaluations):

    grouped = {}

    for e in evaluations:
        user_id = e.get("user_id")

        if not user_id:
            continue

        if user_id not in grouped:
            grouped[user_id] = []

        grouped[user_id].append(e)

    return grouped


# ===============================
# ダッシュボード
# ===============================
def render_staff_dashboard():

    st.title("👨‍🏫 教員ダッシュボード")

    # ===============================
    # 権限チェック（超重要）
    # ===============================
    user = get_current_user()

    if not user:
        st.error("ログインしてください")
        return

    profile = supabase.table("profiles") \
        .select("role") \
        .eq("id", user.id) \
        .execute()

    role = profile.data[0]["role"] if profile.data else "student"

    if role != "teacher":
        st.error("このページにアクセスする権限がありません")
        return

    # ===============================
    # データ取得
    # ===============================
    all_evaluations = load_all_evaluations()

    if not all_evaluations:
        st.info("評価データがまだありません")
        return

    grouped_data = group_by_user(all_evaluations)

    student_ids = list(grouped_data.keys())

    # ===============================
    # 学生選択
    # ===============================
    selected_student = st.selectbox(
        "学生を選択（user_id）",
        student_ids
    )

    evaluations = grouped_data.get(selected_student, [])

    if not evaluations:
        st.warning("この学生には評価データがありません")
        return

    # ===============================
    # レーダーチャート
    # ===============================
    st.markdown("## 📊 レーダーチャート")

    mode = st.radio(
        "表示方法",
        ["平均", "最高", "最新"],
        horizontal=True
    )

    render_radar_chart(evaluations, mode)

    # ===============================
    # 評価履歴
    # ===============================
    st.markdown("## 📚 評価履歴")

    render_evaluation_history(
        evaluations,
        show_detail=True
    )

    # ===============================
    # 戻る
    # ===============================
    st.markdown("---")

    if st.button("💬 チャット画面に戻る"):
        st.session_state.page = "chat"
        st.rerun()
