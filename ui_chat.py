# ui_chat.py
import streamlit as st
import io
import json

from audio import speak_text, play_audio
from evaluation import (
    build_evaluation_prompt,
    save_evaluation,
)
from utils import strip_thought



def render_chat_page(
    scenario,
    subscenario,
    chat_session,
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

        st.rerun()


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
            raw_eval = st.session_state.chat_session.send_message(
                eval_prompt
            ).text

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
        save_evaluation(
            user_id=st.session_state["user_id"],
            scenario=scenario,
            subscenario=subscenario,
            chat_history=st.session_state.chat_history,
            evaluation_text=evaluation_json   # ← ここ重要
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



