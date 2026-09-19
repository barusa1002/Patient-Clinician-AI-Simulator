#ui_evaluation_viewer.py
import streamlit as st
import json
import html as _html
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from datetime import datetime, timedelta, timezone

from utils import md_list, md_score

_JST = timezone(timedelta(hours=9))


# ===============================
# 日本語フォント設定（確実版）
# ===============================
def get_font_prop():
    font_path = os.path.join("fonts", "NotoSansJP-Regular.ttf")

    if os.path.exists(font_path):
        return fm.FontProperties(fname=font_path)
    else:
        st.warning("日本語フォントが見つかりません", icon=":material/warning:")
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
        except (json.JSONDecodeError, TypeError):
            return None

    if not isinstance(evaluation, dict):
        return None

    return evaluation


# ===============================
# レーダーチャート
# ===============================
def render_radar_chart(histories, mode="平均", categories=None):

    font_prop = get_font_prop()

    if categories is None:
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

    ax.tick_params(axis='x', pad=50)

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
    plt.close(fig)


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

        raw_time = h.get("created_at") or h.get("timestamp")

        if raw_time:
            try:
                # Supabase の created_at は UTC。日本時間に変換して表示する
                dt = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                if dt.tzinfo is not None:
                    dt = dt.astimezone(_JST)
                timestamp = dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                timestamp = raw_time
        else:
            timestamp = "日時不明"
        scenario = str(h.get("scenario", "")).strip()

        with st.expander(
            f"{timestamp}｜{scenario}",
            icon=":material/check_circle:" if passed else ":material/cancel:",
        ):

            st.markdown(md_score(rate, achieved, total, passed, small=True),
                        unsafe_allow_html=True)
            st.progress(rate)

            st.markdown("#### 達成項目")
            achieved_items = evaluation.get("achieved", [])
            if achieved_items:
                st.markdown(md_list([("check_circle", "ok", i, "") for i in achieved_items]),
                            unsafe_allow_html=True)
            else:
                st.caption("該当なし")

            st.markdown("#### 不足項目")
            missing_rows = [
                ("error", "ng", m.get("item", "不明") if isinstance(m, dict) else m, "")
                for m in evaluation.get("missing", [])
            ]
            if missing_rows:
                st.markdown(md_list(missing_rows), unsafe_allow_html=True)
            else:
                st.caption("該当なし")

            if show_detail:
                st.markdown("#### 各評価項目")
                view = {1: ("check_circle", "ok"), 0: ("cancel", "ng")}
                st.markdown(
                    md_list([(*view.get(val, ("remove", "")), item, "")
                             for item, val in scores.items()]),
                    unsafe_allow_html=True,
                )


# ===============================
# 評価履歴（課題別・日付別にまとめて表示）
# ===============================
_WEEKDAYS = "月火水木金土日"
_MIN_DT = datetime(1970, 1, 1, tzinfo=_JST)


def _parse_jst(raw):
    """Supabase の created_at（UTC）を日本時間の datetime にする。読めなければ None"""
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=_JST)
    return dt.astimezone(_JST)


def _history_rows(histories):
    """表示に必要な値だけを取り出して、新しい順に並べる"""
    rows = []
    for h in histories:
        evaluation = normalize_evaluation(h)
        if not evaluation:
            continue
        scores = evaluation.get("scores", {})
        valid = {k: v for k, v in scores.items() if v in (0, 1)}
        total = len(valid)
        achieved = sum(valid.values())
        rate = achieved / total if total else 0
        rows.append({
            "evaluation": evaluation,
            "scores": scores,
            "total": total,
            "achieved": achieved,
            "rate": rate,
            "passed": rate >= 0.7,
            "dt": _parse_jst(h.get("created_at") or h.get("timestamp")),
            "scenario": str(h.get("scenario") or "").strip() or "（課題名なし）",
            "subscenario": str(h.get("subscenario") or "").strip(),
        })
    rows.sort(key=lambda r: r["dt"] or _MIN_DT, reverse=True)
    return rows


def _date_label(dt):
    if dt is None:
        return "日時不明"
    return f"{dt.year}年{dt.month}月{dt.day}日（{_WEEKDAYS[dt.weekday()]}）"


def _attempt_html(row, title, subtitle):
    """1回分の結果。<details> で開閉する（st.expander は入れ子にできないため）"""
    esc = _html.escape
    ev = row["evaluation"]
    pct = round(row["rate"] * 100)
    icon, cls = ("check_circle", "ok") if row["passed"] else ("cancel", "ng")

    parts = [
        md_score(row["rate"], row["achieved"], row["total"], row["passed"], small=True),
        f'<div class="md-bar"><span style="width:{pct}%"></span></div>',
    ]

    achieved_items = ev.get("achieved", [])
    if achieved_items:
        parts.append('<div class="md-attempt-h">達成できた項目</div>')
        parts.append(md_list([("check_circle", "ok", i, "") for i in achieved_items]))

    missing_rows = []
    for m in ev.get("missing", []):
        if isinstance(m, dict):
            reason = m.get("reason", "")
            missing_rows.append(("error", "ng", m.get("item", "不明"),
                                 f"理由：{reason}" if reason else ""))
        else:
            missing_rows.append(("error", "ng", m, ""))
    if missing_rows:
        parts.append('<div class="md-attempt-h">不足・不十分な項目</div>')
        parts.append(md_list(missing_rows))

    advice = ev.get("advice", [])
    if advice:
        parts.append('<div class="md-attempt-h">改善アドバイス</div>')
        parts.append(md_list([("lightbulb", "tip", a, "") for a in advice]))

    # 評価チェックリストの各項目は、達成・未達をチップで一覧する
    chips = []
    for item, val in row["scores"].items():
        c = "ok" if val == 1 else ("ng" if val == 0 else "")
        chips.append(f'<span class="md-chipmark {c}">{esc(str(item))}</span>')
    if chips:
        parts.append('<div class="md-attempt-h">評価項目</div>')
        parts.append('<div class="md-chipline">' + "".join(chips) + "</div>")

    sub_html = f'<span class="s">{esc(subtitle)}</span>' if subtitle else ""
    return (
        '<details class="md-attempt">'
        f'<summary><span class="ms {cls}">{icon}</span>'
        f'<span class="md-attempt-main"><span class="t">{esc(title)}</span>{sub_html}</span>'
        f'<span class="md-attempt-rate {cls}">{pct}%</span>'
        '<span class="ms chev">expand_more</span></summary>'
        f'<div class="md-attempt-body">{"".join(parts)}</div>'
        "</details>"
    )


def _trend_html(rows):
    """同じ課題の達成率の推移（古い順）"""
    chips = []
    for r in reversed(rows):
        cls = "ok" if r["passed"] else "ng"
        chips.append(f'<span class="md-trend-pt {cls}">{round(r["rate"] * 100)}%</span>')
    return ('<div class="md-trend"><span class="md-trend-label">推移（古い順）</span>'
            + '<span class="ms md-trend-arrow">arrow_forward</span>'.join(chips) + "</div>")


def render_grouped_history(histories):
    """評価履歴を「課題別」か「日付別」にまとめて表示する"""
    rows = _history_rows(histories)
    if not rows:
        st.info("まだ評価履歴はありません", icon=":material/info:")
        return

    group_by = st.segmented_control(
        "まとめ方",
        ["課題別", "日付別"],
        default="課題別",
        key="history_group_by",
    ) or "課題別"

    n_scenarios = len({r["scenario"] for r in rows})
    n_days = len({r["dt"].date() for r in rows if r["dt"]})
    st.caption(f"全{len(rows)}回　{n_scenarios}課題　{n_days}日分")

    if group_by == "課題別":
        groups = {}
        for r in rows:                      # rows は新しい順なので、最近練習した課題が先頭に来る
            groups.setdefault(r["scenario"], []).append(r)
        for i, (scenario, items) in enumerate(groups.items()):
            best = max(round(x["rate"] * 100) for x in items)
            latest = round(items[0]["rate"] * 100)
            label = f"{scenario}　{len(items)}回・最新 {latest}%・最高 {best}%"
            icon = ":material/check_circle:" if items[0]["passed"] else ":material/pending:"
            with st.expander(label, expanded=(i == 0), icon=icon):
                if len(items) > 1:
                    st.markdown(_trend_html(items), unsafe_allow_html=True)
                st.markdown(
                    "".join(
                        _attempt_html(
                            x,
                            (f"{_date_label(x['dt'])} {x['dt']:%H:%M}" if x["dt"] else "日時不明"),
                            x["subscenario"],
                        )
                        for x in items
                    ),
                    unsafe_allow_html=True,
                )
    else:
        groups = {}
        for r in rows:
            groups.setdefault(_date_label(r["dt"]), []).append(r)
        for i, (day, items) in enumerate(groups.items()):
            avg = round(sum(x["rate"] for x in items) / len(items) * 100)
            n_pass = sum(1 for x in items if x["passed"])
            label = f"{day}　{len(items)}回・平均 {avg}%・達成 {n_pass}回"
            with st.expander(label, expanded=(i == 0), icon=":material/calendar_today:"):
                st.markdown(
                    "".join(
                        _attempt_html(
                            x,
                            x["scenario"],
                            "　".join(filter(None, [
                                f"{x['dt']:%H:%M}" if x["dt"] else "",
                                x["subscenario"],
                            ])),
                        )
                        for x in items
                    ),
                    unsafe_allow_html=True,
                )
