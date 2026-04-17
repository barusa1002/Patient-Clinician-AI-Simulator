#auth.py
import streamlit as st
from db import supabase
import re
import logging

logger = logging.getLogger(__name__)


# =========================
# バリデーション
# =========================
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


def is_valid_password(password):
    return len(password) >= 6


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

            supabase.table("profiles").upsert({
                "id": user_id,
                "role": "student",
                "tutorial_done": False,
                "email": email
            }).execute()

            return True

        return False

    except Exception as e:
        error_msg = str(e)
        logger.error(f"create_user error: {e}")

        if "User already registered" in error_msg:
            st.error("このメールアドレスは既に登録されています")
        else:
            st.error("登録に失敗しました")

        return False


# =========================
# staff作成
# =========================
def create_staff_user(email, password):
    return create_user(email, password)


# =========================
# パスワード再設定メール送信
# =========================
def send_password_reset_email(email):
    try:
        app_url = st.secrets.get("APP_URL", "")
        options = {"redirect_to": app_url} if app_url else {}
        supabase.auth.reset_password_for_email(email, options=options)
        return True
    except Exception as e:
        logger.error(f"send_password_reset_email error: {e}")
        return False


# =========================
# パスワード更新
# =========================
def update_user_password(access_token, refresh_token, new_password):
    try:
        supabase.auth.set_session(access_token, refresh_token)
        supabase.auth.update_user({"password": new_password})
        return True
    except Exception as e:
        logger.error(f"update_user_password error: {e}")
        return False


# =========================
# パスワード再設定フォーム（リンク経由）
# =========================
def show_reset_password_form(access_token, refresh_token):
    col1, col2, col3 = st.columns([1, 8, 1])
    with col2:
        st.image("images/logo.png", width=800)
        st.subheader("🔑 新しいパスワードを設定")

        new_pass1 = st.text_input("新しいパスワード", type="password", key="new_pass1")
        new_pass2 = st.text_input("新しいパスワード（確認）", type="password", key="new_pass2")

        if st.button("パスワードを更新", key="update_pass_btn"):
            if not new_pass1:
                st.error("パスワードを入力してください")
            elif not is_valid_password(new_pass1):
                st.error("パスワードは6文字以上で入力してください")
            elif new_pass1 != new_pass2:
                st.error("パスワードが一致しません")
            else:
                ok = update_user_password(access_token, refresh_token, new_pass1)
                if ok:
                    st.success("パスワードを更新しました。ログインしてください。")
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error("更新に失敗しました。リンクの有効期限が切れている可能性があります。")


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
        return False, None

    except Exception as e:
        logger.error(f"authenticate error: {e}")
        return False, None


# =========================
# プロフィール取得
# =========================
def get_user_profile(user_id):

    try:
        res = supabase.table("profiles") \
            .select("*") \
            .eq("id", user_id) \
            .execute()

        if res.data:
            return res.data[0]

        return None

    except Exception as e:
        logger.error(f"get_user_profile error: {e}")
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

            if not email:
                st.error("メールアドレスを入力してください")

            elif not password:
                st.error("パスワードを入力してください")

            else:
                ok, user = authenticate(email, password)

                if ok:
                    user_id = user.id
                    profile = get_user_profile(user_id)

                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.email = user.email

                    if profile:
                        st.session_state.role = profile.get("role", "student")
                        st.session_state.tutorial_done = profile.get("tutorial_done", False)
                    else:
                        st.session_state.role = "student"
                        st.session_state.tutorial_done = False

                    st.success("ログイン成功")
                    st.rerun()

                else:
                    st.error("メールアドレスまたはパスワードが違います")

        with st.expander("パスワードをお忘れの方はこちら"):
            reset_email = st.text_input("登録済みのメールアドレス", key="reset_email")
            if st.button("パスワード再設定メールを送信", key="reset_btn"):
                if not reset_email:
                    st.error("メールアドレスを入力してください")
                elif not is_valid_email(reset_email):
                    st.error("正しいメールアドレス形式で入力してください")
                else:
                    ok = send_password_reset_email(reset_email)
                    if ok:
                        st.success("パスワード再設定メールを送信しました。メールをご確認ください。")
                    else:
                        st.error("送信に失敗しました。メールアドレスをご確認ください。")

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

            elif not is_valid_email(new_email):
                st.error("正しいメールアドレス形式で入力してください")

            elif not new_pass1:
                st.error("パスワードを入力してください")

            elif not is_valid_password(new_pass1):
                st.error("パスワードは6文字以上で入力してください")

            elif new_pass1 != new_pass2:
                st.error("パスワードが一致しません")

            elif not consent:
                st.error("研究利用への同意が必要です")

            else:
                success = create_user(new_email, new_pass1)

                if success:
                    st.success("登録完了！ログインしてください")
                else:
                    st.error("登録に失敗しました（既に登録済みの可能性があります）")

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
