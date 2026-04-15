#auth.py
import streamlit as st
from db import supabase


# =========================
# ユーザー作成（Auth）
# =========================
def create_user(email, password):

    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if res.user:
            user_id = res.user.id

            # profiles作成（存在してもOK）
            supabase.table("profiles").upsert({
                "id": user_id,
                "role": "student",
                "tutorial_done": False,
                "email": email
            }).execute()

            return True

        return False

    except Exception as e:
        st.error(f"ユーザー作成エラー: {e}")
        return False
# =========================
# staff作成（同じでOK）
# =========================
def create_staff_user(email, password):
    return create_user(email, password)


# =========================
# 認証（Auth）
# =========================
def authenticate(email, password):

    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if res.user:
            return True, res.user
        else:
            return False, None

    except Exception as e:
        st.error(f"ログインエラー: {e}")
        return False, None


# =========================
# プロフィール取得
# =========================
def get_user_profile(user_id):

    try:
        res = supabase.table("profiles").select("*").eq("id", user_id).execute()

        if res.data:
            return res.data[0]
        return None

    except Exception as e:
        st.error(f"プロフィール取得エラー: {e}")
        return None


# =========================
# ログイン画面
# =========================
def login_screen():

    col1, col2, col3 = st.columns([1, 8, 1])

    with col2:
        st.image("images/logo.png", width=800)
        st.caption("💊 患者・医療従事者役 AI シミュレーター")

    tab_login, tab_register = st.tabs(["ログイン", "新規登録"])

    # ---------------------------
    # ログイン
    # ---------------------------
    with tab_login:

        email = st.text_input("メールアドレス", key="login_email")
        password = st.text_input("パスワード", type="password", key="login_pass")

        if st.button("ログイン", key="login_btn"):

            ok, user = authenticate(email, password)

            if ok:

                user_id = user.id

                profile = get_user_profile(user_id)

                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.email = user.email
                st.session_state.role = profile["role"] if profile else "student"
                if profile:
                    st.session_state.role = profile.get("role", "student")
                    st.session_state.tutorial_done = profile.get("tutorial_done") is True
                else:
                    st.session_state.role = "student"
                    st.session_state.tutorial_done = False
                st.success("ログイン成功")
                st.rerun()

            else:
                st.error("メールアドレスまたはパスワードが違います")

    # ---------------------------
    # 新規登録
    # ---------------------------
    with tab_register:

        new_email = st.text_input("メールアドレス", key="reg_email")
        new_pass1 = st.text_input("パスワード", type="password", key="reg_pass1")
        new_pass2 = st.text_input("パスワード（確認）", type="password", key="reg_pass2")

        st.markdown("""
---
### 📄 研究利用について
本アプリの利用データは教育・研究目的で使用される場合があります。  
個人を特定する情報は収集されません。
""")

        consent = st.checkbox("上記内容を理解し、研究利用に同意します", key="consent")

        if st.button("登録", key="register_btn"):

            if not new_email:
                st.error("メールアドレスを入力してください")

            elif new_pass1 != new_pass2:
                st.error("パスワードが一致しません")

            elif not consent:
                st.error("研究利用への同意が必要です")

            else:
                if create_user(new_email, new_pass1):
                    st.success("登録完了！ログインしてください")
                else:
                    st.error("登録に失敗しました")

    # ---------------------------
    # お知らせ
    # ---------------------------
    st.markdown("---")
    st.subheader("📢 お知らせ")

    st.info(
        """
・このアプリは **OSCE練習用AIシミュレーター**です  
・評価履歴はクラウドに保存されます  
・不具合があればお問い合わせください
"""
    )

    # ---------------------------
    # フッター
    # ---------------------------
    st.markdown("---")

    st.caption("📩 お問い合わせ")
    st.caption("a22071@ug.shoyaku.ac.jp")

    st.caption("")
    st.caption("🛠 開発")
    st.caption("昭和薬科大学 薬学部 数理科学 瀧澤研究室")
    st.caption("開発者：高嶋 貫多")

    st.caption("")
    st.caption("Version 1.0")
