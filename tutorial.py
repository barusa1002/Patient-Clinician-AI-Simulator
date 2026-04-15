#tutorial.py
import streamlit as st
from db import supabase

TOTAL_STEPS = 6

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


def skip_tutorial():
    st.session_state.tutorial_done = True
    st.session_state.first_visit = False


def finish_tutorial():

    st.session_state.tutorial_done = True
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


# -----------------------------
# チュートリアル本体
# -----------------------------
def run_tutorial():

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

    if st.session_state.tutorial_done:
        return

    step = st.session_state.tutorial_step

    with st.container(border=True):

        st.subheader("チュートリアル")

        st.progress((step) / TOTAL_STEPS)

        # =========================
        # Step0 アプリ概要
        # =========================
        if step == 0:

            st.markdown("""
## このアプリについて

このアプリは **薬剤師としてのコミュニケーション練習**を行うための  
AIシミュレーターです。

患者応対や服薬指導を想定した会話を行い、  
AIが評価します。

### チュートリアル内容

1. 課題選択  
2. 会話開始  
3. 情報収集  
4. AI評価  
5. ユーザー設定  

所要時間：約3分
""")

            st.info("まずはアプリの基本的な流れを確認しましょう")

            col1, col2 = st.columns([1,1])

            with col1:
                st.button("スキップ", on_click=skip_tutorial, use_container_width=True)

            with col2:
                st.button("チュートリアル開始 →", on_click=next_step, use_container_width=True)

        # =========================
        # Step1 課題選択
        # =========================
        elif step == 1:

            st.markdown("""
## Step1 課題を選択
""")

            st.markdown(
                """
<div class="tutorial-highlight">
← サイドバーでシミュレーション課題を選択します
</div>
""",
                unsafe_allow_html=True
            )

            st.markdown("""
### 選択の流れ

① **モード選択**  
シミュレーションの種類を選択します。

② **課題（シナリオ）選択**  
練習するケースを選択します。

③ **サブシナリオ選択**  
同じ課題でも状況の違うケースを選択できます。
""")

            st.markdown("""
### 読み込まれる情報
""")

            st.markdown("""
📘 **課題内容**  
シミュレーションの目的

👤 **患者情報**  
年齢・症状など

🧑‍⚕️ **医療従事者情報**  
あなたの役割

💊 **処方内容**  
処方されている薬
""")

            st.success("これらの情報をもとに会話が開始されます")

            st.divider()

            col1, col2 = st.columns([1,1])

            with col1:
                st.button("← 前へ", on_click=prev_step, use_container_width=True)

            with col2:
                st.button("次へ →", on_click=next_step, use_container_width=True)

        # =========================
        # Step2 会話開始
        # =========================
        elif step == 2:

            st.markdown("""
## Step2 会話を開始する
""")

            st.markdown(
                """
<div class="input-highlight">
↓ 画面下の入力欄から質問を開始します
</div>
""",
                unsafe_allow_html=True
            )

            st.markdown("""
質問は **2つの方法**で行えます。
""")

            st.markdown("""
### ① テキスト入力
""")

            st.code("今日はどうされましたか？")

            st.markdown("""
テキストボックスに入力して**送信ボタン**を押します。  
 
""")

            st.markdown("""
### ② 音声入力
""")

            st.markdown("""
テキストボックスに  
Windows 10/11: Win + H  
Mac (macOS):Fn キーを2回  
スマートフォン:キーボードのマイクボタン🎤  
を使って音声入力をして**送信ボタン**を押します。              
""")

            st.success("音声入力を使うと実際の医療面接に近い練習ができます")

            st.divider()

            col1, col2 = st.columns([1,1])

            with col1:
                st.button("← 前へ", on_click=prev_step, use_container_width=True)

            with col2:
                st.button("次へ →", on_click=next_step, use_container_width=True)

        # =========================
        # Step3 情報収集
        # =========================
        elif step == 3:

            st.markdown("""
## Step3 情報収集・説明

患者へ質問し、必要な情報を収集します。
""")

            st.markdown(
                """
<div class="tutorial-highlight">
← サイドバーの「セッションリセット」で会話を初期化できます
</div>
""",
                unsafe_allow_html=True
            )

            st.divider()

            col1, col2 = st.columns([1,1])

            with col1:
                st.button("← 前へ", on_click=prev_step, use_container_width=True)

            with col2:
                st.button("次へ →", on_click=next_step, use_container_width=True)

        # =========================
        # Step4 AI評価
        # =========================
        elif step == 4:

            st.markdown("""
## Step4 AI評価
""")

            st.markdown(
                """
<div class="tutorial-highlight">
← サイドバーの「AI評価」ボタンを押すと評価が表示されます
</div>
""",
                unsafe_allow_html=True
            )

            st.markdown("""
評価では

・達成率  
・合格判定  
・達成できた項目  
・不足・不十分な項目  
・改善アドバイス  
・総合評価
 

が表示されます。
""")

            st.divider()

            col1, col2 = st.columns([1,1])

            with col1:
                st.button("← 前へ", on_click=prev_step, use_container_width=True)

            with col2:
                st.button("次へ →", on_click=next_step, use_container_width=True)

        # =========================
        # Step5 設定
        # =========================
        elif step == 5:

            st.markdown("""
## Step5 ユーザー設定
""")

            st.markdown(
                """
<div class="tutorial-highlight">
← サイドバーの「ユーザー設定」からアクセスできます
</div>
""",
                unsafe_allow_html=True
            )

            st.markdown("""
設定画面では次の操作ができます。
""")

            st.markdown("""
### ID・パスワード変更
ログイン情報を変更できます。
""")

            st.markdown("""
### 音声設定
・音声読み上げON/OFF  
・音声入力設定
""")

            st.markdown("""
### 評価履歴

過去のシミュレーション結果を確認できます。

・スコア  
・レーダーチャート  
・AIフィードバック
""")

            st.divider()

            col1, col2 = st.columns([1,1])

            with col1:
                st.button("← 前へ", on_click=prev_step, use_container_width=True)

            with col2:
                st.button("チュートリアル終了", on_click=finish_tutorial, use_container_width=True)
