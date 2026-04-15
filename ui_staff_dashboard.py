#ui_staff_dashboard.py
import streamlit as st
from db import supabase
from ui_evaluation_viewer import (
    render_radar_chart,
    render_evaluation_history
)

# ===============================
# 評価＋ユーザー情報取得（JOINしない）
# ===============================
def load_all_evaluations_with_profile():

    # ① evaluations取得
    eval_res = supabase.table("evaluations") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()

    evaluations = eval_res.data or []

    # ② profiles取得
    prof_res = supabase.table("profiles") \
        .select("id, email") \
        .execute()
    
    # 🔥 修正①：キーを統一
    profiles = {
        str(p["id"]).strip(): p.get("email", "不明")
        for p in (prof_res.data or [])
    }
    
    # 🔥 修正②：lookupも統一
    for e in evaluations:
        uid = str(e.get("user_id", "")).strip()
        e["email"] = profiles.get(uid, f"不明ユーザー ({uid[:6]})")

    return evaluations


# ===============================
# ユーザーごとに整理
# ===============================
def group_by_user(evaluations):

    grouped = {}

    for e in evaluations:
        user_id = e.get("user_id")
        email = e.get("email", "不明ユーザー")

        if not user_id:
            continue

        if user_id not in grouped:
            grouped[user_id] = {
                "email": email,
                "data": []
            }

        grouped[user_id]["data"].append(e)

    return grouped


# ===============================
# フィルタ処理
# ===============================
def apply_filters(evaluations, selected_date, selected_scenario):

    filtered = evaluations

    if selected_date != "すべて":
        filtered = [
            e for e in filtered
            if e.get("created_at", "").startswith(selected_date)
        ]

    if selected_scenario != "すべて":
        filtered = [
            e for e in filtered
            if e.get("scenario") == selected_scenario
        ]

    return filtered


# ===============================
# メインUI
# ===============================
def render_staff_dashboard():

    st.title("👨‍🏫 教員ダッシュボード")

    # ===============================
    # 権限チェック
    # ===============================
    if st.session_state.get("role") != "staff":
        st.error("このページにアクセスする権限がありません")
        return

    # ===============================
    # データ取得
    # ===============================
    all_evaluations = load_all_evaluations_with_profile()

    if not all_evaluations:
        st.info("評価データがまだありません")
        return

    grouped_data = group_by_user(all_evaluations)

    # ===============================
    # 学生選択（email表示）
    # ===============================
    student_options = {
        v["email"]: k
        for k, v in grouped_data.items()
    }

    selected_label = st.selectbox(
        "👤 学生を選択",
        list(student_options.keys())
    )

    selected_user_id = student_options[selected_label]
    evaluations = grouped_data[selected_user_id]["data"]

    # ===============================
    # フィルタUI
    # ===============================
    st.markdown("### 🔍 絞り込み")

    # 日付
    dates = [
        e.get("created_at", "")[:10]
        for e in evaluations if e.get("created_at")
    ]
    unique_dates = sorted(list(set(dates)))

    selected_date = st.selectbox(
        "📅 日付",
        ["すべて"] + unique_dates
    )

    # シナリオ
    scenarios = [
        e.get("scenario", "不明")
        for e in evaluations
    ]
    unique_scenarios = sorted(list(set(scenarios)))

    selected_scenario = st.selectbox(
        "📘 シナリオ",
        ["すべて"] + unique_scenarios
    )

    # フィルタ適用
    evaluations = apply_filters(
        evaluations,
        selected_date,
        selected_scenario
    )

    if not evaluations:
        st.warning("条件に一致するデータがありません")
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
