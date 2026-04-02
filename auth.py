#auth.py
import streamlit as st
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from db import supabase


# =========================
# ユーザー作成
# =========================
def create_user(username, password):

    try:
        res = supabase.table("users").select("id").eq("id", username).execute()

        if res.data:
            return False

        supabase.table("users").insert({
            "id": username,
            "password": generate_password_hash(password),
            "role": "student",
            "tutorial_done": False,
            "consent": True,
            "consent_timestamp": datetime.now().isoformat()
        }).execute()

        return True

    except Exception as e:
        st.error(f"ユーザー作成エラー: {e}")
        return False


# =========================
# staff作成
# =========================
def create_staff_user(username, password):

    try:
        res = supabase.table("users").select("id").eq("id", username).execute()

        if res.data:
            return False

        supabase.table("users").insert({
            "id": username,
            "password": generate_password_hash(password),
            "role": "staff",
            "tutorial_done": False,
            "consent": True,
            "consent_timestamp": datetime.now().isoformat()
        }).execute()

        return True

    except Exception as e:
        st.error(f"ユーザー作成エラー: {e}")
        return False


# =========================
# 認証
# =========================
def authenticate(username, password):

    try:
        res = supabase.table("users").select("*").eq("id", username).execute()

        if not res.data:
            return False, None, None

        user = res.data[0]

        if check_password_hash(user["password"], password):
            return True, user["role"], user

        return False, None, None

    except Exception as e:
        st.error(f"ログインエラー: {e}")
        return False, None, None


# =========================
# ユーザーID変更（⚠非推奨）
# =========================
def update_user_id(old_id, new_id):

    st.warning("ユーザーID変更は現在非対応です（Supabase制約）")
    return False


# =========================
# パスワード変更
# =========================
def update_password(username, new_password):

    try:
        supabase.table("users").update({
            "password": generate_password_hash(new_password)
        }).eq("id", username).execute()

        return True

    except Exception as e:
        st.error(f"パスワード更新エラー: {e}")
        return False


# =========================
# ログイン画面
# =========================
def login_screen():

    col1, col2, col3 = st.columns([1, 8, 1])

    with col2:
        st.image("images/logo.png", width=800)
        st.caption("💊 患者・医療従事者役 AI シミュレーター")

    tab_login, tab_register = st.tabs(["ログイン", "初期登録"])

    # ---------------------------
    # ログイン
    # ---------------------------
    with tab_login:

        username = st.text_input("ID", key="login_id")
        password = st.text_input("パスワード", type="password", key="login_pass")

        if st.button("ログイン", key="login_btn"):

            ok, role, user_data = authenticate(username, password)

            if ok:

                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_id = username
                st.session_state.role = role

                st.session_state.tutorial_done = user_data.get("tutorial_done", False)

                st.success("ログイン成功")
                st.rerun()

            else:
                st.error("IDまたはパスワードが違います")

    # ---------------------------
    # 初期登録
    # ---------------------------
    with tab_register:

        new_user = st.text_input("新しいID", key="reg_id")
        new_pass1 = st.text_input("新しいパスワード", type="password", key="reg_pass1")
        new_pass2 = st.text_input("新しいパスワード（確認）", type="password", key="reg_pass2")

        st.markdown("""
---
### 📄 研究利用について
本アプリの利用データは教育・研究目的で使用される場合があります。  
個人を特定する情報は収集されません。
""")

        consent = st.checkbox("上記内容を理解し、研究利用に同意します", key="consent")

        if st.button("登録", key="register_btn"):

            if not new_user:
                st.error("IDを入力してください")

            elif new_pass1 != new_pass2:
                st.error("パスワードが一致しません")

            elif not consent:
                st.error("研究利用への同意が必要です")

            else:
                if create_user(new_user, new_pass1):
                    st.success("登録完了！ログインしてください")
                else:
                    st.error("そのIDはすでに使われています")

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
