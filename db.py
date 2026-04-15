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

    try:
        res = supabase.auth.get_user()

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

    try:
        supabase.auth.sign_out()
    except Exception as e:
        logger.error(f"logout error: {e}")

    # Streamlit側セッションもクリア
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()
