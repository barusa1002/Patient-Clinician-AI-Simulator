#db.py
from supabase import create_client, Client
import streamlit as st


# =========================
# Supabaseクライアント取得
# =========================
@st.cache_resource
def get_supabase() -> Client:
    try:
        url = st.secrets["https://rhwejvrxcdsblzbtyvdu.supabase.co"]
        key = st.secrets["sb_publishable_BN1cbBGuL1NJs2j4Mf02DA_DKatk3u2"]

        client = create_client(url, key)
        return client

    except Exception as e:
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

    except Exception:
        return None


# =========================
# ログアウト処理
# =========================
def logout():

    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    # Streamlit側セッションもクリア
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()
