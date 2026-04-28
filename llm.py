import streamlit as st
import google.generativeai as genai

# 患者・医師ロールプレイ用：暗黙的思考の出力を禁止する追加指示
_NO_THINKING_SUFFIX = (
    "\n\n"
    "【絶対ルール - 最優先】\n"
    "思考過程・分析・理由づけ・判断プロセスを一切テキストとして出力してはならない。\n"
    "キャラクターのセリフ文のみを出力すること。\n"
    "以下のような文頭・表現を含む文は絶対に出力禁止：\n"
    "「課題は」「〜すべき」「〜が最も無難」「〜が適切」「〜を返す」「〜と答える」"
    "「〜はず」「〜べき」「〜良い」など分析・推論を示す表現。"
)

@st.cache_resource
def get_client(api_key: str):
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai  # ← clientじゃなくてgenai自体を返す

def start_chat(client, model_name, system_prompt, no_thinking=False):
    if no_thinking:
        system_prompt = system_prompt + _NO_THINKING_SUFFIX
    model = client.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
    )
    chat = model.start_chat()
    return chat
