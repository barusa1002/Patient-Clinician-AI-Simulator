#auth.py
import streamlit as st
import os
import json
import shutil
from werkzeug.security import generate_password_hash, check_password_hash

USER_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)


def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def create_user(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "password": generate_password_hash(password),
        "role": "student",
        "tutorial_done": False
    }
    save_users(users)
    return True

def create_staff_user(username, password):
    users = load_users()
    if username in users:
        return False

    users[username] = {
        "password": generate_password_hash(password),
        "role": "staff",
        "tutorial_done": False
    }
    save_users(users)
    return True


def authenticate(username, password):
    users = load_users()
    if username not in users:
        return False, None

    if check_password_hash(users[username]["password"], password):
        return True, users[username]["role"]

    return False, None




def update_user_id(old_id, new_id):
    users = load_users()

    if old_id not in users or new_id in users:
        return False

    # --- users.json 更新 ---
    users[new_id] = users.pop(old_id)
    save_users(users)

    # --- 評価履歴ファイルの名前変更 ---
    old_eval = f"data/evaluations/{old_id}.json"
    new_eval = f"data/evaluations/{new_id}.json"

    if os.path.exists(old_eval) and not os.path.exists(new_eval):
        os.rename(old_eval, new_eval)

    return True

def update_password(username, new_password):
    users = load_users()
    if username not in users:
        return False
    users[username]["password"] = generate_password_hash(new_password)
    save_users(users)
    return True

def login_screen():

    # タイトル
    col1, col2, col3 = st.columns([1,8,1])

    with col2:
        st.image("images/logo.png", width=800)
        st.caption("💊 患者・医療従事者役 AI シミュレーター")

    tab_login, tab_register = st.tabs(["ログイン", "初期登録"])

    # ---------------------------
    # ログイン
    # ---------------------------
    with tab_login:

        username = st.text_input("ID")
        password = st.text_input("パスワード", type="password")

        if st.button("ログイン"):

            ok, role = authenticate(username, password)

            if ok:

                users = load_users()

                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_id = username
                st.session_state.role = role

                # チュートリアル状態読み込み
                st.session_state.tutorial_done = users[username].get("tutorial_done", False)

                st.success("ログイン成功")
                st.rerun()

            else:
                st.error("IDまたはパスワードが違います")

    # ---------------------------
    # 初期登録
    # ---------------------------
    with tab_register:

        new_user = st.text_input("新しいID")
        new_pass1 = st.text_input("新しいパスワード", type="password")
        new_pass2 = st.text_input("新しいパスワード（確認）", type="password")

        if st.button("登録"):

            if not new_user:
                st.error("IDを入力してください")

            elif new_pass1 != new_pass2:
                st.error("パスワードが一致しません")

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
・評価履歴は自動保存されます  
・不具合があればお問い合わせください
"""
    )

    # ---------------------------
    # 問い合わせ・開発情報
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

    

        