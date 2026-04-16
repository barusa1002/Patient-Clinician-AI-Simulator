#ui_staff_dashboard.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from db import supabase
from ui_evaluation_viewer import (
    render_radar_chart,
    render_evaluation_history,
    get_font_prop,
    normalize_evaluation,
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
# シナリオ別達成率を計算
# ===============================
def compute_scenario_rates(evaluations):
    from collections import defaultdict
    scenario_scores = defaultdict(list)

    for e in evaluations:
        scenario = e.get("scenario", "不明")
        evaluation = normalize_evaluation(e)

        if not evaluation:
            continue

        scores = evaluation.get("scores", {})
        achieved = sum(1 for v in scores.values() if v == 1)
        total = sum(1 for v in scores.values() if v in (0, 1))

        if total > 0:
            scenario_scores[scenario].append(achieved / total * 100)

    return {s: sum(rates) / len(rates) for s, rates in scenario_scores.items()}


# ===============================
# 学生比較グラフ
# ===============================
def render_comparison_chart(selected_emails, student_options, grouped_data):
    all_rates = {}

    for email in selected_emails:
        user_id = student_options[email]
        evals = grouped_data[user_id]["data"]
        all_rates[email] = compute_scenario_rates(evals)

    all_scenarios = sorted({s for rates in all_rates.values() for s in rates})

    if not all_scenarios:
        st.warning("グラフを描画できるデータがありません")
        return

    font_prop = get_font_prop()
    n_students = len(selected_emails)
    bar_width = 0.8 / n_students
    x = np.arange(len(all_scenarios))
    colors = plt.cm.tab10.colors

    fig, ax = plt.subplots(figsize=(max(10, len(all_scenarios) * 1.5), 6))

    for i, email in enumerate(selected_emails):
        rates = all_rates[email]
        values = [rates.get(s, 0) for s in all_scenarios]
        offset = (i - n_students / 2 + 0.5) * bar_width
        ax.bar(x + offset, values, bar_width, label=email, color=colors[i % len(colors)])

    ax.set_xticks(x)
    if font_prop:
        ax.set_xticklabels(all_scenarios, rotation=45, ha="right", fontproperties=font_prop)
        ax.set_ylabel("達成率 (%)", fontproperties=font_prop)
        ax.set_title("シナリオ別達成率比較", fontproperties=font_prop)
        ax.legend(prop=font_prop)
    else:
        ax.set_xticklabels(all_scenarios, rotation=45, ha="right")
        ax.set_ylabel("達成率 (%)")
        ax.set_title("シナリオ別達成率比較")
        ax.legend()

    ax.set_ylim(0, 100)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


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

    # ===============================
    # 学生比較グラフ
    # ===============================
    st.markdown("## 📊 学生比較グラフ")

    selected_emails = st.multiselect(
        "👥 比較する学生を選択（2人以上）",
        list(student_options.keys())
    )

    if len(selected_emails) >= 2:
        render_comparison_chart(selected_emails, student_options, grouped_data)
    elif len(selected_emails) == 1:
        st.info("2人以上選択すると比較グラフが表示されます")

    st.markdown("---")

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
