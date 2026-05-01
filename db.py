#db.py
from supabase import create_client, Client
import streamlit as st
import logging

logger = logging.getLogger(__name__)


# =========================
# Supabaseクライアント取得
# =========================
@st.cache_resource
def get_supabase() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]

        client = create_client(url, key)
        return client

    except Exception as e:
        logger.error(f"get_supabase error: {e}")
        st.error(f"Supabase接続エラー: {e}")
        return None


supabase: Client = get_supabase()


# =========================
# 現在のログインユーザー取得
# =========================
def get_current_user():
    # st.session_state に保存したトークンで検証する。
    # @st.cache_resource のシングルトンクライアントに依存しないことで
    # 複数ユーザー・複数デバイス間のセッション混入を防ぐ。
    access_token = st.session_state.get("access_token")
    if not access_token:
        return None
    try:
        res = supabase.auth.get_user(access_token)
        if res and res.user:
            return res.user
        return None
    except Exception as e:
        logger.error(f"get_current_user error: {e}")
        return None


# =========================
# ログアウト処理
# =========================
def logout():

    access_token = st.session_state.get("access_token")
    if access_token:
        try:
            supabase.auth.sign_out()
        except Exception as e:
            logger.error(f"logout error: {e}")

    # Streamlit側セッションをクリア（access_token も消えるので次回は未認証）
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()
