import streamlit as st

def init_session_state():
    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "show_history" not in st.session_state:
        st.session_state.show_history = False

    if "run_evaluation" not in st.session_state:
        st.session_state.run_evaluation = False

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "page" not in st.session_state:
        st.session_state.page = "chat"

    if "autoplay_enabled" not in st.session_state:
        st.session_state.autoplay_enabled = True

    if "speech_speed" not in st.session_state:
        st.session_state.speech_speed = "ふつう"
