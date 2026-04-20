# ui_mode_select.py
import streamlit as st

LEARNING_MODES = {
    "OSCE対策": {
        "icon": "🏥",
        "description": "薬学部4〜5年生向け。OSCE試験対策として、患者応対・服薬指導・疑義照会などの基本手技を練習します。",
        "color": "#7c3aed",
    },
    "実習前練習": {
        "icon": "🎓",
        "description": "5年生の実務実習（薬局・病院）に向けた練習。代表的な疾患（高血圧・糖尿病・脂質異常症・心不全・呼吸器疾患）の服薬指導を重点的に学びます。",
        "color": "#2563eb",
    },
    "初期研修": {
        "icon": "🔬",
        "description": "薬剤師就職直後の初期研修向け。ポリファーマシー・相互作用・チーム医療など、より複雑な臨床場面を想定した実践的なトレーニングです。",
        "color": "#059669",
    },
}


def render_mode_select_page():
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem 0 0.5rem;">
            <h2 style="font-size: 1.3rem; font-weight: 700; color: rgba(255,255,255,0.9);">
                学習モードを選択してください
            </h2>
            <p style="font-size: 0.85rem; color: rgba(255,255,255,0.5); margin-top: 0.2rem;">
                目的に合ったモードを選ぶと、シナリオと評価基準が切り替わります
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)

    for i, (mode_name, info) in enumerate(LEARNING_MODES.items()):
        with cols[i]:
            color = info["color"]
            st.markdown(
                f"""
                <div style="
                    background: rgba(255,255,255,0.04);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 16px;
                    padding: 1.2rem 1rem;
                    min-height: 180px;
                    margin-bottom: 0.5rem;
                ">
                    <div style="font-size: 2rem; text-align: center;">{info['icon']}</div>
                    <div style="
                        font-size: 1rem;
                        font-weight: 700;
                        text-align: center;
                        color: white;
                        margin: 0.4rem 0;
                    ">{mode_name}</div>
                    <div style="
                        font-size: 0.78rem;
                        color: rgba(255,255,255,0.55);
                        line-height: 1.55;
                        text-align: center;
                    ">{info['description']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                f"{info['icon']} {mode_name}を始める",
                key=f"mode_{mode_name}",
                use_container_width=True,
            ):
                st.session_state["learning_mode"] = mode_name
                st.rerun()
