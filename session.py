import streamlit as st
import copy

SESSION_DEFAULTS = {
    "user_id": None,
    "logged_in": False,
    "show_history": False,
    "run_evaluation": False,
    "chat_history": [],
    "page": "chat",
    "autoplay_enabled": True,
    "speech_speed": "ふつう",
}

def init_session_state():
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = copy.deepcopy(default)
