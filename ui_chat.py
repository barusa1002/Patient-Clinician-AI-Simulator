# ui_chat.py
import streamlit as st
import io
import json
from db import get_current_user

from audio import speak_text, play_audio
from evaluation import (
    build_evaluation_prompt,
    save_evaluation,
    EVALUATION_CHECKLISTS,
)
from utils import strip_thought
from llm import start_chat
from config import MODEL_NAME



def render_chat_page(
    scenario,
    subscenario,
    chat_session,
    selected,
):
    # スマホ判定（毎回取得）
    IS_MOBILE = st.session_state.get("is_mobile", False)

    # ==================================================
    # タイトル
    # ==================================================
    st.header(f"{scenario}｜{subscenario}")

    # ==================================================
    # チャット履歴表示
    # ==================================================
    for i, (role, msg) in enumerate(st.session_state.chat_history):

        with st.chat_message(role):

            st.markdown(msg)

            if (
                role == "assistant"
                and not IS_MOBILE
                and st.session_state.get("need_audio")
                and i == len(st.session_state.chat_history) - 1
            ):
                try:
                    audio_bytes = speak_text(msg)

                    if audio_bytes:
                        audio_key = f"audio_{i}"
                        st.session_state[audio_key] = audio_bytes.getvalue()

                        play_audio(
                            io.BytesIO(st.session_state[audio_key]),
                            autoplay=True,
                            speed=st.session_state.speech_speed
                        )

                    # 🔥 ここ重要
                    st.session_state["need_audio"] = False

                except Exception:
                    st.warning("音声生成に失敗しました")

            if role == "assistant" and IS_MOBILE:

                if st.button("▶ 音声再生", key=f"history_play_{i}"):

                    audio_bytes = speak_text(msg)

                    play_audio(
                        audio_bytes,
                        autoplay=False,
                        speed=st.session_state.speech_speed
                    )



    # ==================================================
    # 入力欄（完全統一）
    # ==================================================
    st.markdown("---")

    text_input = st.chat_input("メッセージを入力")

    # ==================================================
    # メッセージ送信
    # ==================================================
    if text_input:
        st.session_state.chat_history.append(("user", text_input))

        try:
            raw_response = chat_session.send_message(text_input).text
            response = strip_thought(raw_response)

            if not response or not response.strip():
                response = "（応答が生成されませんでした）"

        except Exception:
            response = "（現在システムが混み合っています）"

        st.session_state.chat_history.append(("assistant", response))

        # 音声再生フラグ
        st.session_state["need_audio"] = True
        # メッセージ送信時にヒント・模範解答・評価済みフラグをリセット
        st.session_state["hint_text"] = None
        st.session_state["evaluation_done"] = False
        st.session_state["model_answer_text"] = None

        st.rerun()


    # ==================================================
    # ヒント機能
    # ==================================================
    has_history = len(st.session_state.chat_history) > 0

    if st.button("💡 ヒントを見る", disabled=not has_history):
        checklist = EVALUATION_CHECKLISTS.get(scenario, {})
        checklist_text = "\n".join(f"- {item}" for item in checklist)

        conversation = ""
        for role, msg in st.session_state.chat_history:
            speaker = "実習生" if role == "user" else "患者・医療者"
            conversation += f"{speaker}：{msg}\n"

        hint_prompt = f"""
あなたは薬学実習のコーチです。
以下の会話を見て、実習生が次に確認すべきことをヒントとして伝えてください。

【シナリオ】
{scenario} / {subscenario}

【会話ログ】
{conversation}

【評価項目（参考）】
{checklist_text}

【ヒントのルール】
- 答えを直接言わない
- 「〜について確認してみましょう」のような柔らかい表現で促す
- 1〜2文で簡潔にまとめる
- 日本語で回答する
"""

        try:
            hint_session = start_chat(
                client=st.session_state.gemini_client,
                model_name=MODEL_NAME,
                system_prompt="あなたは薬学実習のコーチです。学生が自分で気づけるよう、直接答えを言わずにヒントを与えます。"
            )
            st.session_state["hint_text"] = hint_session.send_message(hint_prompt).text
        except Exception:
            st.session_state["hint_text"] = "ヒントの生成に失敗しました。"

    if st.session_state.get("hint_text"):
        st.info(st.session_state["hint_text"])

    # ==================================================
    # 評価実行
    # ==================================================
    if st.session_state.get("run_evaluation"):

        eval_prompt = build_evaluation_prompt(
            scenario,
            subscenario,
            st.session_state.chat_history
        )

        raw_eval = None

        try:
            eval_session = start_chat(
                client=st.session_state.gemini_client,
                model_name=MODEL_NAME,
                system_prompt="あなたは薬学実習の評価者です。会話ログをもとに客観的な評価を行います。"
            )
            raw_eval = eval_session.send_message(eval_prompt).text

            start = raw_eval.find("{")
            end = raw_eval.rfind("}") + 1

            if start == -1 or end == -1:
                raise ValueError("JSONが見つかりません")

            json_text = raw_eval[start:end]
            evaluation_json = json.loads(json_text)

        except Exception as e:
            st.error("評価の解析に失敗しました")

            if raw_eval:
                st.write("▼AIの生レスポンス")
                st.write(raw_eval)

            st.write("▼エラー内容")
            st.write(e)

            st.session_state.run_evaluation = False
            return


        # =============================
        # 点数計算（表示項目ベース）
        # =============================

        scores = evaluation_json["scores"]

        achieved = sum(1 for v in scores.values() if v == 1)
        missing = sum(1 for v in scores.values() if v == 0)

        total = achieved + missing

        if total == 0:
            st.error("評価可能な項目がありません")
            return

        rate = achieved / total
        passed = rate >= 0.7


        # =============================
        # 保存
        # =============================
        user = get_current_user()
        
        if not user:
            st.error("ログイン状態が無効です")
            return
        
        save_evaluation(
            user_id=user.id,
            scenario=scenario,
            subscenario=subscenario,
            chat_history=st.session_state.chat_history,
            evaluation_text=evaluation_json
        )

        # =============================
        # 表示
        # =============================
        st.markdown("## 📊 評価結果")

        st.write(f"達成率：{achieved}/{total}（{rate*100:.1f}%）")

        if passed:
            st.success("🎉 OSCE合格")
        else:
            st.error("❌ OSCE不合格")

        st.markdown("---")

        # ==================================================
        # 1️⃣ 達成できた項目
        # ==================================================
        st.markdown("## ① 達成できた項目")

        achieved_items = evaluation_json.get("achieved", [])

        if achieved_items:
            for item in achieved_items:
                st.markdown(f"- {item}")
        else:
            st.markdown("（該当なし）")

        st.markdown("---")

        # ==================================================
        # 2️⃣ 不足・不十分な項目
        # ==================================================
        st.markdown("## ② 不足・不十分な項目")

        missing_items = evaluation_json.get("missing", [])

        if missing_items:
            for m in missing_items:
                st.markdown(f"**{m['item']}**")
                st.markdown(f"- 理由：{m['reason']}")
                st.markdown("")
        else:
            st.markdown("（該当なし）")

        st.markdown("---")

        # ==================================================
        # 3️⃣ 改善アドバイス
        # ==================================================
        st.markdown("## ③ 改善アドバイス")

        advice_list = evaluation_json.get("advice", [])

        if advice_list:
            for adv in advice_list:
                st.markdown(f"- {adv}")
        else:
            st.markdown("（アドバイスなし）")

        st.markdown("---")

        # ==================================================
        # 4️⃣ 総合評価
        # ==================================================
        st.markdown("## ④ 総合評価")

        if "comment" in evaluation_json:
            st.markdown(evaluation_json["comment"])
        else:
            st.markdown("（総合評価なし）")

        st.session_state.run_evaluation = False
        st.session_state["evaluation_done"] = True


    # ==================================================
    # 模範解答
    # ==================================================
    if st.session_state.get("evaluation_done"):

        st.markdown("---")

        if st.button("📖 模範解答を見る"):
            checklist = EVALUATION_CHECKLISTS.get(scenario, {})
            checklist_text = "\n".join(f"- {item}" for item in checklist)

            phrases_text = "\n".join(
                f"- {item}：「{phrase}」"
                for item, phrase in checklist.items()
                if phrase
            )

            task_info_text = "\n".join(
                f"【{k}】\n{v}" for k, v in selected.get("task_info", {}).items()
            )

            model_answer_prompt = f"""
あなたは薬学実習の指導教員です。
以下のシナリオ情報に忠実に従い、模範的な薬剤師と患者の会話例を生成してください。

【課題名】
{scenario} / {subscenario}

【シナリオ詳細情報】
{task_info_text}

【評価チェックリスト（全項目を満たすこと）】
{checklist_text}

【各評価項目の模範セリフ（記載がある項目は必ずそのまま使うこと）】
{phrases_text if phrases_text else "（なし）"}

【表示形式】
必ず以下の形式で、1行1発言として出力してください。
薬剤師：「〇〇」
患者：「〇〇」
薬剤師：「〇〇」
...

【ルール】
- シナリオ詳細情報に記載された患者情報・処方内容・症状をそのまま使うこと
- 独自に患者情報や処方内容を作らないこと
- 評価チェックリストの全項目を自然な流れでカバーすること
- 模範セリフが指定されている項目は、その言葉をそのまま使うこと
- 丁寧で実践的な言葉遣いを使うこと
- 会話形式のみ出力すること（説明文・前置きは不要）
- 日本語で出力すること
"""

            with st.spinner("模範解答を生成中..."):
                try:
                    model_answer_session = start_chat(
                        client=st.session_state.gemini_client,
                        model_name=MODEL_NAME,
                        system_prompt="あなたは薬学実習の指導教員です。模範的な薬剤師の会話例を生成します。"
                    )
                    st.session_state["model_answer_text"] = model_answer_session.send_message(
                        model_answer_prompt
                    ).text
                except Exception:
                    st.session_state["model_answer_text"] = "模範解答の生成に失敗しました。"

        if st.session_state.get("model_answer_text"):
            with st.expander("📖 模範的な会話例を見る", expanded=True):
                lines = [
                    line.strip()
                    for line in st.session_state["model_answer_text"].splitlines()
                    if line.strip()
                ]
                st.markdown("\n\n".join(lines))


