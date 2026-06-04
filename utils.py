# utils.py
# 共通ユーティリティ関数群


import re
import urllib.parse
import streamlit as st

# Gemini 2.5が思考プロセスを出力するときに現れるキーワード一覧
# （患者の実際のセリフには絶対に現れない語句のみ登録する）
_THINKING_INDICATORS = [
    "ユーザーは",
    "私は患者役",
    "患者役として",
    "前の回答で",
    "と答えるのが適切",
    "と返答するのが適切",
    "と答えるのが自然",
    "と答えるべき",
    "質問されたことに答える",
    "のみを返す",
    "のみ答える",
    "のみ出力する",
    "患者情報に",
    "課題は",
    "最も無難",
    "受け答えが良い",
    "説明を促す",
    "避けるべき",
]

# ==========================================================
# フィルタ関数
# ==========================================================
def strip_thought(text: str) -> str:
    """
    LLM出力から思考部分を削除し、患者の発話だけを返す
    """

    if not text:
        return text

    # THOUGHT削除（明示ラベルあり）
    text = re.sub(r"THOUGHT.*?回答[:：]", "", text, flags=re.DOTALL)
    text = re.sub(r"THOUGHT.*", "", text)

    # 先頭のラベル削除（Response: / 回答: / 発言: など）
    text = re.sub(r"^(Response|回答|発言|セリフ|患者|返答)[:：]\s*", "", text, flags=re.IGNORECASE)

    # 発話ラベルがある場合はそこだけ残す
    if "発話：" in text:
        text = text.split("発話：")[-1]

    # Gemini 2.5の暗黙的思考対応（1）：
    # 空行区切りで複数段落がある場合は最後の段落のみ残す
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) > 1:
        text = paragraphs[-1]

    # Gemini 2.5の暗黙的思考対応（2）：
    # 思考キーワードが含まれる場合、「。」で分割して最後の文だけを返す
    # （最後の文がメタ言語でない場合のみ採用）
    if any(kw in text for kw in _THINKING_INDICATORS):
        sentences = [s.strip() for s in text.split("。") if s.strip()]
        if sentences:
            last = sentences[-1]
            if not any(kw in last for kw in _THINKING_INDICATORS):
                if not last.endswith(("。", "？", "！")):
                    last += "。"
                text = last

    return text.strip()


# ==========================================================
# モバイル判定関数
# ==========================================================
MOBILE_KEYWORDS = ["iphone", "android", "ipad", "mobile", "blackberry", "windows phone"]

def detect_mobile() -> bool:
    """
    User-Agentを解析してモバイル端末かどうか判定する
    """
    try:
        user_agent = st.context.headers.get("user-agent", "").lower()
        return any(keyword in user_agent for keyword in MOBILE_KEYWORDS)
    except Exception:
        return False


# ==========================================================
# 処方内容HTML生成（薬品名にPMDA添付文書リンクを付与）
# ==========================================================
_DRUG_UNITS_RE = re.compile(
    r'(錠|カプセル|カプセル剤|散|液|テープ|パッチ|OD|DS|エアー|坐剤|吸入|mg|μg|mL|mcg)'
)
_SKIP_PREFIXES = (
    "用法", "用量", "日数", "副作用", "効果", "残薬",
    "1回", "1日", "注意", "【", "発作", "包装", "使用",
    "血圧", "血糖", "鎮痛", "抗炎", "胃酸", "利尿", "（",
    "処方提案", "理由", "現在の処方",
)

# 薬品名キーワード → PMDA添付文書直接URL（後発品優先・動作確認済み）
# URL形式: {code}/{code}?view=body&lang=ja が安定して動作する
_DRUG_URL_MAP = {
    "ロキソプロフェン":  "https://www.info.pmda.go.jp/go/pack/1149019F1706_1_07/1149019F1706_1_07?view=body&lang=ja",
    "ロキソニン":        "https://www.info.pmda.go.jp/go/pack/1149019F1706_1_07/1149019F1706_1_07?view=body&lang=ja",
    "アムロジピン":      "https://www.info.pmda.go.jp/go/pack/2171022F1282_1_21/2171022F1282_1_21?view=body&lang=ja",
    "フロセミド":        "https://www.info.pmda.go.jp/go/pack/2139005F1060_4_14/2139005F1060_4_14?view=body&lang=ja",
    "ドネペジル":        "https://www.info.pmda.go.jp/go/pack/1190012F1042_1_13/1190012F1042_1_13?view=body&lang=ja",
    "カンデサルタン":    "https://www.info.pmda.go.jp/go/pack/2149040F1093_1_11/2149040F1093_1_11?view=body&lang=ja",
    "ランソプラゾール":  "https://www.info.pmda.go.jp/go/pack/2329023F1101_1_16/2329023F1101_1_16?view=body&lang=ja",
    "ワーファリン":      "https://www.info.pmda.go.jp/go/pack/3332001F1083_1_22/3332001F1083_1_22?view=body&lang=ja",
    "ワルファリン":      "https://www.info.pmda.go.jp/go/pack/3332001F1083_1_22/3332001F1083_1_22?view=body&lang=ja",
    "エナラプリル":      "https://www.info.pmda.go.jp/go/pack/2144002F1210_1_14/2144002F1210_1_14?view=body&lang=ja",
    "アセトアミノフェン": "https://www.info.pmda.go.jp/go/pack/1141007F1195_1_13/1141007F1195_1_13?view=body&lang=ja",
    "トラネキサム酸":    "https://www.info.pmda.go.jp/go/pack/3327002F1169_1_07/3327002F1169_1_07?view=body&lang=ja",
    "フェキソフェナジン": "https://www.info.pmda.go.jp/go/pack/4490023F1270_1_05/4490023F1270_1_05?view=body&lang=ja",
    "アレグラ錠":        "https://www.info.pmda.go.jp/go/pack/4490023F1270_1_05/4490023F1270_1_05?view=body&lang=ja",
    "メトホルミン":      "https://www.info.pmda.go.jp/go/pack/3962002F2124_1_06/3962002F2124_1_06?view=body&lang=ja",
    "ツロブテロール":    "https://www.info.pmda.go.jp/go/pack/2259707S1209_1_03/2259707S1209_1_03?view=body&lang=ja",
    "ホクナリン":        "https://www.info.pmda.go.jp/go/pack/2259707S1209_1_03/2259707S1209_1_03?view=body&lang=ja",
    "メプチン":          "https://www.info.pmda.go.jp/go/pack/2259704G9033_1_09/2259704G9033_1_09?view=body&lang=ja",
    "パブロンゴールドA": "https://www.info.pmda.go.jp/ogo/K1506000007_06_01",
    "アレグラFX":        "https://www.info.pmda.go.jp/ogo/J1201000287_06_03",
    "ガスター10":        "https://www.info.pmda.go.jp/ogo/K1103000023_05_01",
}


def make_prescription_html(prescription_text: str) -> str:
    """処方テキストの薬品名行にPMDA添付文書リンクを付けてMarkdown文字列で返す。"""

    def pmda_url(name: str) -> str:
        for key, url in _DRUG_URL_MAP.items():
            if key in name:
                return url
        return (
            "https://www.pmda.go.jp/PmdaSearch/iyakuSearch/"
            f"?name={urllib.parse.quote(name)}"
        )

    lines_md = []
    for raw in prescription_text.split('\n'):
        line = raw.strip()
        if not line:
            lines_md.append('')
            continue

        # 「推奨薬：薬品名」形式の行
        if line.startswith('推奨薬：'):
            drug_name = line[4:]
            lines_md.append(f'推奨薬：[{drug_name}]({pmda_url(drug_name)})')
            continue

        # スキップ行（用法・副作用説明など）
        if any(line.startswith(s) for s in _SKIP_PREFIXES):
            lines_md.append(line)
            continue

        # 薬品名行の判定（mg・錠などの単位を含む行）
        if _DRUG_UNITS_RE.search(line):
            # "Rp1：" などのプレフィックスを除去
            clean = re.sub(r'^Rp\d+[：:]\s*', '', line)
            prefix = line[: len(line) - len(clean)]

            # 最初の数字の直前までを薬品名とする
            m = re.match(r'^([^\d]+?)[\s]*[\d.]', clean)
            if m:
                drug_name = m.group(1).strip()
            else:
                drug_name = clean.split()[0] if clean.split() else clean

            lines_md.append(f'{prefix}[{clean}]({pmda_url(drug_name)})')
        else:
            lines_md.append(line)

    return '  \n'.join(lines_md)


# ==========================================================
# セッションリセット関数
# ==========================================================
def reset_session():
    for key in [
        "chat_history", "chat_session", "current_scenario",
        "prescription_notes", "prescription_submitted",
        "model_answer_text", "evaluation_done", "last_evaluation_json",
        "hint_text", "run_evaluation",
    ]:
        if key in st.session_state:
            del st.session_state[key]
