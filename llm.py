import streamlit as st
import google.generativeai as genai

@st.cache_resource
def get_client(api_key: str):
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai  # ← clientじゃなくてgenai自体を返す

def start_chat(client, model_name, system_prompt):
    model = client.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
        generation_config={"thinking_config": {"thinking_budget": 0}},
    )
    chat = model.start_chat()
    return chat
