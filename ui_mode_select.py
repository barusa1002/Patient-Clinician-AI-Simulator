# ui_mode_select.py
import streamlit as st

# icon は Material Symbols の名前。tone は highlight.css の .md-mode-icon.c-* に対応する。
LEARNING_MODES = {
    "スタンダードモード": {
        "icon": "school",
        "tone": "primary",
        "target": "薬学部 4〜5年生",
        "description": "患者応対・服薬指導・疑義照会などの基本的なシミュレーションを練習します。",
    },
    "スキルアップモード": {
        "icon": "local_pharmacy",
        "tone": "tertiary",
        "target": "5年生の実務実習（薬局・病院）",
        "description": "高血圧・糖尿病・脂質異常症・心不全・呼吸器疾患の服薬指導を、"
                       "同じ患者を継続して追いかけながら重点的に学びます。",
    },
    "初期研修": {
        "icon": "clinical_notes",
        "tone": "secondary",
        "target": "就職直後の薬剤師",
        "description": "ポリファーマシー・相互作用・チーム医療など、"
                       "より複雑な臨床場面を想定した実践的なトレーニングです。",
    },
}


def render_mode_select_page():
    st.markdown("## 学習モードを選択")
    st.markdown(
        '<p class="md-supporting">目的に合ったモードを選ぶと、シナリオと評価基準が切り替わります。'
        'あとからサイドバーで変更できます。</p>',
        unsafe_allow_html=True,
    )

    cols = st.columns(3, gap="medium")

    for col, (mode_name, info) in zip(cols, LEARNING_MODES.items()):
        with col:
            # MD3 のカード：アイコン・名称・対象・説明・操作を1枚にまとめる
            with st.container(border=True):
                st.markdown(
                    f'<div class="md-mode-icon c-{info["tone"]}">{info["icon"]}</div>'
                    f'<div class="md-mode-title">{mode_name}</div>'
                    f'<div class="md-mode-target">{info["target"]}</div>'
                    f'<div class="md-mode-desc">{info["description"]}</div>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    "このモードで始める",
                    key=f"mode_{mode_name}",
                    icon=":material/arrow_forward:",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state["learning_mode"] = mode_name
                    st.rerun()
