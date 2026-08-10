#tutorial.py
import streamlit as st
from db import supabase

TOTAL_STEPS = 6

STEP_TITLES = [
    "アプリについて",
    "課題を選ぶ",
    "会話を始める",
    "会話を続ける",
    "AIに評価してもらう",
    "その他の機能",
]

# -----------------------------
# 初期化
# -----------------------------
def init_tutorial():

    if "tutorial_step" not in st.session_state:
        st.session_state.tutorial_step = 0

    if "tutorial_done" not in st.session_state:
        st.session_state.tutorial_done = False

    if "first_visit" not in st.session_state:
        st.session_state.first_visit = True


# -----------------------------
# 操作関数
# -----------------------------
def next_step():
    if st.session_state.tutorial_step < TOTAL_STEPS - 1:
        st.session_state.tutorial_step += 1


def prev_step():
    if st.session_state.tutorial_step > 0:
        st.session_state.tutorial_step -= 1


def _mark_tutorial_done():
    """チュートリアル完了状態をセッション・DB両方に保存する"""
    st.session_state.tutorial_done = True
    st.session_state.show_tutorial = False
    st.session_state.first_visit = False
    st.session_state.tutorial_step = 0

    user_id = st.session_state.get("user_id")
    if not user_id:
        return

    try:
        supabase.table("profiles").update({
            "tutorial_done": True
        }).eq("id", user_id).execute()
    except Exception as e:
        st.error(f"チュートリアル更新エラー: {e}")


def skip_tutorial():
    _mark_tutorial_done()


def finish_tutorial():
    _mark_tutorial_done()


# -----------------------------
# 共通パーツ
# -----------------------------
def _render_header(step: int):
    """ステップ番号・タイトル・進捗バーをまとめて表示"""
    st.subheader(f"チュートリアル（{step + 1} / {TOTAL_STEPS}） ── {STEP_TITLES[step]}")
    st.progress((step + 1) / TOTAL_STEPS)

    # ステップドット（●が現在地より前後、番号が見た目でも分かるように）
    dots = " ".join(
        "🟣" if i == step else ("✅" if i < step else "⚪")
        for i in range(TOTAL_STEPS)
    )
    st.caption(dots)


def _render_nav(show_prev=True, next_label="次へ →", on_next=next_step, show_skip=False):
    """前へ／次へ（／スキップ）のボタン行"""
    st.divider()

    cols = st.columns([1, 1, 1]) if show_skip else st.columns([1, 1])

    with cols[0]:
        if show_prev:
            st.button("← 前へ", on_click=prev_step, use_container_width=True)
        else:
            st.button("スキップして始める", on_click=skip_tutorial, use_container_width=True)

    with cols[1]:
        st.button(next_label, on_click=on_next, use_container_width=True, type="primary")

    if show_skip:
        with cols[2]:
            st.button("スキップ", on_click=skip_tutorial, use_container_width=True)


# -----------------------------
# チュートリアル本体
# -----------------------------
def run_tutorial() -> bool:
    """
    チュートリアルを表示する。
    表示した場合は True を返す（呼び出し側はこの戻り値を見て st.stop() する）。
    """

    init_tutorial()

    user_id = st.session_state.get("user_id")

    # DBからも確認（重要）
    if user_id:
        res = supabase.table("profiles") \
            .select("tutorial_done") \
            .eq("id", user_id) \
            .execute()

        if res.data and res.data[0].get("tutorial_done"):
            st.session_state.tutorial_done = True

    if st.session_state.tutorial_done and not st.session_state.get("show_tutorial"):
        return False

    step = st.session_state.tutorial_step

    with st.container(border=True):

        _render_header(step)

        # =========================
        # Step0 アプリ概要
        # =========================
        if step == 0:

            st.markdown("""
### 👋 ようこそ

このアプリは、**薬剤師として患者さんや医療スタッフと話す練習**を
AI相手に何度でもできるシミュレーターです。

1. シナリオを選ぶ
2. AI（患者役・医療者役）と会話する
3. AIが会話を自動で採点し、アドバイスをくれる

この3ステップを、**実際の画面を見ながら約2分**で確認していきましょう。
""")

            st.info("次へ →　を押して進めてください。下の「スキップして始める」でいつでも中断できます。")

            _render_nav(show_prev=False, next_label="はじめる →")

        # =========================
        # Step1 課題選択
        # =========================
        elif step == 1:

            st.markdown("### 📋 まずは練習したい課題（シナリオ）を選びます")

            st.markdown(
                """
<div class="tutorial-highlight">
👈 画面左のサイドバーで、上から順に選んでいきます
</div>
""",
                unsafe_allow_html=True
            )

            st.markdown("""
サイドバーには、上から **3段階の選択メニュー** が並んでいます。

**① モード**　─　練習の種類（患者応対／服薬指導 など）

**② 課題（シナリオ）**　─　練習したい具体的なケース

**③ サブシナリオ**　─　同じ課題の中での状況違い（初診／再診 など）
""")

            st.markdown("選ぶと、画面上部に次の情報が自動で表示されます。")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("📘 **課題内容**\n\nこの練習で何をすべきか")
                st.markdown("👤 **患者情報**\n\n年齢・症状など")
            with c2:
                st.markdown("🧑‍⚕️ **あなたの役割**\n\n実習生／薬剤師など")
                st.markdown("💊 **処方内容**\n\n処方されている薬")

            st.success("これらを読んでから会話を始めると、スムーズに練習できます。")

            _render_nav()

        # =========================
        # Step2 会話開始
        # =========================
        elif step == 2:

            st.markdown("### 💬 会話を始めましょう")

            st.markdown(
                """
<div class="input-highlight">
👇 画面下の入力欄に話しかけたい内容を入力します
</div>
""",
                unsafe_allow_html=True
            )

            st.markdown("入力方法は2通りあります。")

            st.markdown("**① キーボードで入力する**")
            st.code("本日はどうされましたか？", language=None)
            st.caption("入力欄に文章を打って送信すればOKです。")

            st.markdown("**② 音声で入力する（実際の面接に近い練習ができます）**")
            st.markdown("""
| 環境 | 操作方法 |
|---|---|
| Windows 10/11 | `Win + H` キーで音声入力 |
| Mac | `Fn` キーを2回 |
| スマートフォン | キーボードのマイクボタン 🎤 |
""")

            st.success("最初は困ったら『ヒントを見る』ボタンも使えます（会話画面に表示されています）。")

            _render_nav()

        # =========================
        # Step3 会話を続ける
        # =========================
        elif step == 3:

            st.markdown("### 🔁 会話を続けて、必要な情報を集めます")

            st.markdown("""
患者さん（AI）に質問を重ねて、症状や困りごとを聞き出していきましょう。
1回で終わらせず、**やり取りを重ねるほど評価の対象が増えます**。
""")

            st.markdown("**質問の例：**")
            st.code(
                "・いつからその症状がありますか？\n"
                "・他に飲んでいるお薬はありますか？\n"
                "・アレルギーはありますか？",
                language=None
            )

            st.markdown(
                """
<div class="tutorial-highlight">
👈 会話をやり直したいときは、サイドバーの「セッションをリセット」を押します
</div>
""",
                unsafe_allow_html=True
            )

            st.info("同じシナリオに何度でも挑戦できます。うまく聞き出せなかったら気軽にリセットしましょう。")

            _render_nav()

        # =========================
        # Step4 AI評価
        # =========================
        elif step == 4:

            st.markdown("### 📝 会話が終わったらAIに評価してもらいましょう")

            st.markdown(
                """
<div class="tutorial-highlight">
👈 サイドバーの「AIによる評価を実行」ボタンを押します
</div>
""",
                unsafe_allow_html=True
            )

            st.markdown("評価結果には、次の内容が表示されます。")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("""
✅ **達成率・合格判定**

達成できた項目
""")
            with c2:
                st.markdown("""
⚠️ 不足・不十分だった項目

💡 次回への改善アドバイス
""")

            st.success("「模範解答」も確認できるので、自分の会話と見比べて次回に活かしましょう。")

            _render_nav()

        # =========================
        # Step5 設定
        # =========================
        elif step == 5:

            st.markdown("### ⚙️ 最後に、その他の便利機能です")

            st.markdown(
                """
<div class="tutorial-highlight">
👈 サイドバー下部の「ユーザー設定」からアクセスできます
</div>
""",
                unsafe_allow_html=True
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("🔑 **ID・パスワード**\n\nログイン情報の変更")
            with c2:
                st.markdown("🔊 **音声設定**\n\n読み上げ・音声入力のON/OFF")
            with c3:
                st.markdown("📊 **評価履歴**\n\nスコア・レーダーチャート・過去のAIフィードバック")

            st.markdown("---")
            st.markdown("""
### 🎉 これでチュートリアルは終わりです

「チュートリアル終了」を押すと練習画面に戻ります。
このチュートリアルは、サイドバー下部からいつでも再表示できます。
""")

            st.divider()
            col1, col2 = st.columns([1, 1])
            with col1:
                st.button("← 前へ", on_click=prev_step, use_container_width=True)
            with col2:
                st.button("チュートリアル終了 ✓", on_click=finish_tutorial,
                           use_container_width=True, type="primary")

    return True
