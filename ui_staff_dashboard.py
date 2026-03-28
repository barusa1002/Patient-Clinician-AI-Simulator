#ui_staff_dashboard.py
import streamlit as st
import json
from evaluation import load_all_students_evaluations

# ★ 追加
from ui_evaluation_viewer import (
    render_radar_chart,
    render_evaluation_history
)


def render_staff_dashboard():

    st.title("👨‍🏫 教員ダッシュボード")

    all_data = load_all_students_evaluations()

    if not all_data:
        st.info("評価データがまだありません")
        return

    student_ids = list(all_data.keys())

    # ===============================
    # 学生選択
    # ===============================
    selected_student = st.selectbox(
        "学生を選択",
        student_ids
    )

    evaluations = all_data.get(selected_student, [])

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
    # 評価履歴（学生と同じUI）
    # ===============================
    st.markdown("## 📚 評価履歴")
    render_evaluation_history(evaluations, show_detail=True)



    # ===============================
    # 戻るボタン
    # ===============================
    st.markdown("---")

    if st.button("💬 チャット画面に戻る"):
        st.session_state.page = "chat"
        st.rerun()