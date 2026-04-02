#ui_evaluation_viewer.py
import streamlit as st
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os


# ===============================
# 日本語フォント設定（確実版）
# ===============================
def get_font_prop():
    font_path = os.path.join("fonts", "NotoSansJP-Regular.ttf")

    if os.path.exists(font_path):
        return fm.FontProperties(fname=font_path)
    else:
        st.warning("⚠ 日本語フォントが見つかりません")
        return None


# ===============================
# evaluation正規化（超重要）
# ===============================
def normalize_evaluation(h):
    evaluation = h.get("evaluation")

    if not evaluation:
        return None

    # Supabase構造対応
    if isinstance(evaluation, dict) and "result" in evaluation:
        evaluation = evaluation["result"]

    # JSON文字列対応
    if isinstance(evaluation, str):
        try:
            evaluation = json.loads(evaluation)
        except:
            return None

    if not isinstance(evaluation, dict):
        return None

    return evaluation


# ===============================
# レーダーチャート
# ===============================
def render_radar_chart(histories, mode="平均"):

    font_prop = get_font_prop()

    categories = [
        "薬局での患者応対",
        "病棟での初回面談",
        "来局者応対",
        "在宅での薬学的管理",
        "薬局での薬剤交付",
        "病棟での服薬指導",
        "一般医薬品の情報提供",
        "疑義照会",
        "医療従事者への情報提供"
    ]

    category_scores = {c: [] for c in categories}

    # ===============================
    # データ収集
    # ===============================
    for h in histories:

        scenario = str(h.get("scenario", "")).strip()

        if scenario not in categories:
            continue

        evaluation = normalize_evaluation(h)
        if not evaluation:
            continue

        scores = evaluation.get("scores", {})
        valid_scores = [v for v in scores.values() if v in [0, 1]]

        if not valid_scores:
            continue

        rate = sum(valid_scores) / len(valid_scores)
        category_scores[scenario].append(rate)

    # ===============================
    # 値生成
    # ===============================
    values = []

    for c in categories:
        scores = category_scores[c]

        if not scores:
            values.append(0)
        elif mode == "平均":
            values.append(np.mean(scores))
        elif mode == "最高":
            values.append(max(scores))
        elif mode == "最新":
            values.append(scores[-1])

    if not any(values):
        st.info("まだレーダーチャートを作成できる評価データがありません")
        return

    # ===============================
    # 描画
    # ===============================
    labels = categories
    num_vars = len(labels)

    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)

    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))

    # 色分け
    colors = []
    for v in values:
        if v >= 0.7:
            colors.append("green")
        elif v < 0.5:
            colors.append("red")
        else:
            colors.append("orange")

    # 軸ライン
    for i in range(num_vars):
        ax.plot(
            [angles[i], angles[i]],
            [0, values[i]],
            color=colors[i],
            linewidth=1
        )

    # 閉じる
    angles_closed = np.append(angles, angles[0])
    values_closed = np.append(values, values[0])

    ax.plot(angles_closed, values_closed, color="black", linewidth=1)
    ax.fill(angles_closed, values_closed, alpha=0.15)

    # ===============================
    # ラベル（日本語フォント適用）
    # ===============================
    ax.set_xticks(angles)

    if font_prop:
        ax.set_xticklabels(
            labels,
            fontsize=4,
            color="navy",
            fontweight="bold",
            fontproperties=font_prop
        )
    else:
        ax.set_xticklabels(labels, fontsize=6)

    ax.tick_params(axis='x', pad=40)

    # ===============================
    # %表示
    # ===============================
    for i in range(num_vars):
        angle = angles[i]
        value = values[i]
        r = 1.23

        ha = "right" if np.pi/2 < angle < 3*np.pi/2 else "left"

        if font_prop:
            ax.text(
                angle, r, f"{int(value*100)}%",
                color=colors[i],
                fontsize=7,
                fontweight="bold",
                ha=ha,
                va="center",
                fontproperties=font_prop
            )
        else:
            ax.text(angle, r, f"{int(value*100)}%")

    ax.set_ylim(0, 1.2)

    # ===============================
    # 合格ラインラベル
    # ===============================
    if font_prop:
        fig.text(
            1.10, 1.00,
            "- - -合格ライン 70%",
            ha="right",
            fontsize=6,
            color="green",
            fontproperties=font_prop,
            bbox=dict(
                facecolor="white",
                edgecolor="green",
                boxstyle="round,pad=0.3"
            )
        )
    else:
        fig.text(1.10, 1.00, "- - -合格ライン 70%")

    # 合格ライン
    pass_rate = 0.7
    ax.plot(
        np.linspace(0, 2*np.pi, 200),
        [pass_rate]*200,
        linestyle="--",
        linewidth=1,
        color="green",
        alpha=0.6
    )

    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels([])
    ax.grid(alpha=0.3)

    st.pyplot(fig)


# ===============================
# 評価履歴
# ===============================
def render_evaluation_history(histories, show_detail=True):

    if not histories:
        st.info("まだ評価履歴はありません")
        return

    for h in reversed(histories):

        evaluation = normalize_evaluation(h)
        if not evaluation:
            continue

        scores = evaluation.get("scores", {})
        valid_scores = {k: v for k, v in scores.items() if v in [0, 1]}

        total = len(valid_scores)
        achieved = sum(valid_scores.values())
        rate = achieved / total if total else 0
        passed = rate >= 0.7

        timestamp = h.get("created_at") or h.get("timestamp", "日時不明")
        scenario = str(h.get("scenario", "")).strip()

        with st.expander(f"{timestamp}｜{scenario}"):

            st.write(f"達成率：{achieved}/{total}（{rate*100:.1f}%）")

            if passed:
                st.success("🎉 合格")
            else:
                st.error("❌ 不合格")

            st.markdown("### ✅ 達成項目")
            for item in evaluation.get("achieved", []):
                st.markdown(f"- {item}")

            st.markdown("### ⚠ 不足項目")
            for m in evaluation.get("missing", []):
                st.markdown(f"- {m['item']}")

            if show_detail:
                st.markdown("### 🧪 各評価項目")

                for item, val in scores.items():
                    if val == 1:
                        st.markdown(f"🟢 {item}")
                    elif val == 0:
                        st.markdown(f"🔴 {item}")
                    else:
                        st.markdown(f"⚪ {item}")
