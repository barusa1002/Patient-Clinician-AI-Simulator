import streamlit as st
from google import genai
from google.genai import types

@st.cache_resource
def get_client(api_key: str):
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def start_chat(client, model_name, system_prompt):
    config = types.GenerateContentConfig(
        system_instruction=system_prompt
    )
    return client.chats.create(
        model=model_name,
        config=config
    )
