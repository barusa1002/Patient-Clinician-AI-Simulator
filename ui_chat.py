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


# ==================================================
# 疑義照会：会話終了検知
# ==================================================
_FAREWELL_KEYWORDS = [
    "失礼いたします", "失礼します",
    "ありがとうございました",
    "お電話ありがとうございました",
    "では失礼", "電話を切",
]

def _detect_gigi_end(chat_history):
    """AIの最後のメッセージに終了挨拶が含まれるか判定する"""
    for role, msg in reversed(chat_history):
        if role == "assistant":
            return any(kw in msg for kw in _FAREWELL_KEYWORDS)
    return False


# ==================================================
# 疑義照会：処方箋備考欄フォーム
# ==================================================
def _render_prescription_form():
    """疑義照会完了後の処方箋備考欄記入フォームを描画する"""
    from datetime import datetime as _dt
    st.markdown("---")
    st.markdown("### 📋 処方箋 備考欄記載")
    st.caption("疑義照会が完了しました。処方箋の備考欄に記載する内容を入力してください。")

    if st.session_state.get("prescription_submitted"):
        notes = st.session_state.get("prescription_notes", {})
        st.success("✅ 備考欄を記録しました")
        st.markdown(
            f"- **日時**：{notes.get('date_time', '（未記載）')}\n"
            f"- **照会方法**：{notes.get('method', '（未記載）')}\n"
            f"- **照会者（自分）**：{notes.get('pharmacist_name', '（未記載）')}\n"
            f"- **照会先（医師名）**：{notes.get('doctor_name', '（未記載）')}\n"
            f"- **変更内容**：{notes.get('change_content', '（未記載）')}"
        )
        if st.button("📝 再記入する", key="prescription_redo"):
            st.session_state["prescription_submitted"] = False
            st.rerun()
        return

    with st.form("prescription_notes_form"):
        default_date = _dt.now().strftime("%Y年%m月%d日")
        date_time = st.text_input("日時", value=default_date,
                                  placeholder="例：2024年1月15日 14:30")
        method = st.selectbox("照会方法", ["電話", "FAX", "直接"])
        pharmacist_name = st.text_input("照会者（自分の名前）",
                                        placeholder="例：昭薬 花子")
        doctor_name = st.text_input("照会先（医師名・医療機関）",
                                    placeholder="例：昭薬太郎医師（昭和薬科大学付属病院内科）")
        change_content = st.text_area("変更内容",
                                      placeholder="例：アムロジピン錠5mg　1日2回→1日1回朝食後に変更")
        submitted = st.form_submit_button("📝 記録する")

        if submitted:
            st.session_state["prescription_notes"] = {
                "date_time": date_time,
                "method": method,
                "pharmacist_name": pharmacist_name,
                "doctor_name": doctor_name,
                "change_content": change_content,
            }
            st.session_state["prescription_submitted"] = True
            st.rerun()



def render_chat_page(
    scenario,
    subscenario,
    chat_session,
    selected,
):
    # スマホ判定（毎回取得）
    IS_MOBILE = st.session_state.get("is_mobile", False)

    # ==================================================
    # タイトル（モバイル対応：コンパクトバッジ形式）
    # ==================================================
    if IS_MOBILE:
        st.markdown(
            f"""
            <div style="
                display: inline-flex;
                align-items: center;
                gap: 6px;
                background: rgba(124,58,237,0.15);
                border: 1px solid rgba(124,58,237,0.3);
                border-radius: 20px;
                padding: 4px 14px;
                margin-bottom: 8px;
                max-width: 100%;
                overflow: hidden;
            ">
                <span style="font-size:0.75rem; color:#a78bfa; font-weight:600;
                             white-space:nowrap; overflow:hidden;
                             text-overflow:ellipsis;">
                    📋 {scenario}
                </span>
                <span style="color:rgba(255,255,255,0.3); font-size:0.7rem;">｜</span>
                <span style="font-size:0.75rem; color:#93c5fd; font-weight:600;
                             white-space:nowrap; overflow:hidden;
                             text-overflow:ellipsis;">
                    {subscenario}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
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

    if IS_MOBILE:
        # モバイル：小さいボタンを左端に配置
        hint_col, _ = st.columns([2, 5])
        with hint_col:
            hint_clicked = st.button("💡 ヒント", disabled=not has_history, key="hint_btn")
    else:
        hint_clicked = st.button("💡 ヒントを見る", disabled=not has_history, key="hint_btn")
    if hint_clicked:
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
    # 疑義照会：処方箋備考欄フォーム
    # ==================================================
    if scenario == "疑義照会" and _detect_gigi_end(st.session_state.get("chat_history", [])):
        _render_prescription_form()

    # ==================================================
    # 評価実行
    # ==================================================
    if st.session_state.get("run_evaluation"):

        prescription_notes = (
            st.session_state.get("prescription_notes")
            if scenario == "疑義照会"
            else None
        )

        eval_prompt = build_evaluation_prompt(
            scenario,
            subscenario,
            st.session_state.chat_history,
            prescription_notes=prescription_notes,
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

            # 模範解答生成時に不足項目を参照できるよう保存
            st.session_state["last_evaluation_json"] = evaluation_json

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
            evaluation_text=evaluation_json,
            prescription_notes=prescription_notes,
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
    # 模範解答（評価結果を踏まえた補完版）
    # ==================================================
    if st.session_state.get("evaluation_done"):

        st.markdown("---")

        if st.button("📖 模範解答を見る"):
            import re as _re

            last_eval = st.session_state.get("last_evaluation_json", {})
            missing_items = last_eval.get("missing", [])

            # 既存会話を文字列化
            conv_lines = []
            for role, msg in st.session_state.chat_history:
                speaker = "薬剤師" if role == "user" else "患者"
                conv_lines.append(f"{speaker}：「{msg}」")
            existing_conv = "\n".join(conv_lines)

            # 不足項目テキスト
            if missing_items:
                missing_text = "\n".join(
                    f"- {m['item']}：{m['reason']}" for m in missing_items
                )
            else:
                missing_text = "（不足項目なし）"

            task_info_text = "\n".join(
                f"【{k}】\n{v}" for k, v in selected.get("task_info", {}).items()
            )

            model_answer_prompt = f"""
あなたは薬学実習の指導教員です。
以下の「既存の会話」をベースに、不足していた評価項目を自然に補完して完成した模範会話を作成してください。

【課題名】
{scenario} / {subscenario}

【シナリオ詳細情報】
{task_info_text}

【既存の会話（そのまま使うこと・変更・削除禁止）】
{existing_conv}

【不足していた評価項目（これらを補完すること）】
{missing_text}

【出力ルール】
- 既存の会話の各行はそのまま出力すること（一字一句変更・削除禁止）
- 不足項目を補うための発言を、会話の流れが最も自然な位置に挿入すること
- 補完した発言（新たに追加した行のみ）は必ず [補完] タグで囲むこと
  例：[補完]薬剤師：「副作用についてご説明します」[/補完]
- 既存の発言には [補完] タグを絶対に付けないこと
- 1行1発言の形式を厳守すること
- 会話形式のみ出力すること（説明文・前置き・見出し不要）
- 日本語で出力すること
"""

            with st.spinner("模範解答を生成中..."):
                try:
                    model_answer_session = start_chat(
                        client=st.session_state.gemini_client,
                        model_name=MODEL_NAME,
                        system_prompt="あなたは薬学実習の指導教員です。既存の会話を活かしながら不足部分を自然に補完します。"
                    )
                    st.session_state["model_answer_text"] = model_answer_session.send_message(
                        model_answer_prompt
                    ).text
                except Exception:
                    st.session_state["model_answer_text"] = "模範解答の生成に失敗しました。"

        if st.session_state.get("model_answer_text"):
            import re as _re

            with st.expander("📖 模範的な会話例（補完版）を見る", expanded=True):
                raw_text = st.session_state["model_answer_text"]

                # [補完]...[/補完] ブロックで分割
                segments = _re.split(r'(\[補完\].*?\[/補完\])', raw_text, flags=_re.DOTALL)

                html_parts = []
                for seg in segments:
                    m = _re.match(r'^\[補完\](.*?)\[/補完\]$', seg.strip(), _re.DOTALL)
                    if m:
                        # 補完部分：青色ハイライト
                        inner_lines = [
                            l.strip() for l in m.group(1).splitlines() if l.strip()
                        ]
                        for line in inner_lines:
                            safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                            html_parts.append(
                                f'<div style="'
                                f'color: #60a5fa; '
                                f'background: rgba(96,165,250,0.13); '
                                f'border-left: 3px solid #60a5fa; '
                                f'padding: 6px 10px; '
                                f'border-radius: 0 8px 8px 0; '
                                f'margin: 4px 0; '
                                f'font-weight: 500;'
                                f'">✦ {safe}</div>'
                            )
                    else:
                        # 既存発言：通常表示
                        for line in seg.splitlines():
                            line = line.strip()
                            if not line:
                                continue
                            # 念のため残留タグを除去
                            clean = _re.sub(r'\[/?補完\]', '', line)
                            safe = clean.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                            html_parts.append(
                                f'<div style="padding: 4px 0; margin: 2px 0;">{safe}</div>'
                            )

                st.markdown(
                    '<div style="line-height: 1.9; font-size: 0.93rem;">'
                    + "".join(html_parts)
                    + "</div>",
                    unsafe_allow_html=True,
                )

                # 凡例
                st.markdown(
                    '<div style="margin-top: 10px; font-size: 0.78rem; '
                    'color: rgba(255,255,255,0.45);">'
                    "✦ 青色ハイライト：AIによって補完された発言</div>",
                    unsafe_allow_html=True,
                )


