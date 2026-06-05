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
    "1回", "1日", "注意", "【現在の処方】", "発作", "包装", "使用",
    "血圧", "血糖", "鎮痛", "抗炎", "胃酸", "利尿", "（",
    "処方提案", "理由", "現在の処方", "変更後", "最新検査値",
    "トラフ濃度", "目標血中",
)

# 薬品名キーワード → PMDA添付文書直接URL（後発品優先・動作確認済み）
# URL形式: {code}/{code}?view=body&lang=ja （フレームセット親のみだと404の場合があるため）
def _pack(code: str) -> str:
    return f"https://www.info.pmda.go.jp/go/pack/{code}/{code}?view=body&lang=ja"

_DRUG_URL_MAP = {
    # ── 鎮痛・解熱 ──
    "ロキソプロフェン":  _pack("1149019F1706_1_07"),   # 後発「TCK」
    "ロキソニン":        _pack("1149019F1706_1_07"),
    "アセトアミノフェン": _pack("1141007F1195_1_13"),  # 後発「マルイシ」
    "アスピリン":        _pack("3399007H1137_1_08"),   # 後発「ZE」腸溶錠
    # ── 循環器 ──
    "アムロジピン":      _pack("2171022F1282_1_21"),   # 後発「サワイ」
    "カンデサルタン":    _pack("2149040F1093_1_11"),   # 後発「JG」
    "バルサルタン":      _pack("2149041F1292_1_08"),   # 後発「日新」
    "エナラプリル":      _pack("2144002F1210_1_14"),   # 後発「JG」
    "カルベジロール":    _pack("2149032F1099_1_15"),   # 後発「サワイ」
    "ビソプロロール":    _pack("2123016F1174_1_06"),   # 後発「JG」
    "フロセミド":        _pack("2139005F1060_4_14"),   # 後発「NP」
    "スピロノラクトン":  _pack("2133001F1476_1_17"),   # 後発「トーワ」
    "エプレレノン":      _pack("2149045F1037_1_06"),   # 後発「杏林」
    "ワーファリン":      _pack("3332001F1083_1_22"),   # 後発「トーワ」
    "ワルファリン":      _pack("3332001F1083_1_22"),
    "クロピドグレル":    _pack("3399008F1203_1_12"),   # 後発「サワイ」
    # ── 消化器 ──
    "ランソプラゾール":  _pack("2329023F1101_1_16"),   # 後発「サワイ」
    "トラネキサム酸":    _pack("3327002F1169_1_07"),   # 後発「YD」
    "酸化マグネシウム":  _pack("2344009F1086_1_10"),   # 後発「ケンエー」
    # ── 糖尿病・代謝 ──
    "メトホルミン":      _pack("3962002F2124_1_06"),   # 後発「DSPB」
    "グリメピリド":      _pack("3961008F1217_1_11"),   # 後発「サワイ」
    "インスリングラルギン": _pack("2492416G2024_1_16"), # ランタス
    "ランタス":          _pack("2492416G2024_1_16"),
    # ── 脂質異常 ──
    "アトルバスタチン":  _pack("2189015F1082_1_19"),   # 後発「DSEP」
    "ロスバスタチン":    _pack("2189017F1154_1_11"),   # 後発「サワイ」
    "フェノフィブラート": _pack("2183006F3040_1_06"),  # 後発「武田テバ」
    # ── 呼吸器 ──
    "ブデソニド":        _pack("2290801G1037_1_06"),   # ブデホル吸入粉末剤（後発品）
    "シムビコート":      _pack("2290801G1029_1_17"),  # 先発品
    "メプチン":          _pack("2259704G9033_1_09"),   # 先発品のみ
    "ツロブテロール":    _pack("2259707S1209_1_03"),   # 後発「トーワ」
    "ホクナリン":        _pack("2259707S1209_1_03"),
    "チオトロピウム":    _pack("2259709G1027_1_15"),   # スピリーバ
    "スピリーバ":        _pack("2259709G1027_1_15"),
    "フルチカゾン":      _pack("2290700G7032_1_11"),   # フルタイド
    "フルタイド":        _pack("2290700G7032_1_11"),
    # ── 抗菌 ──
    "クラリスロマイシン": _pack("6149003F2100_1_28"),  # 後発「サワイ」
    # ── アレルギー ──
    "フェキソフェナジン": _pack("4490023F1270_1_05"),  # 後発「サワイ」
    "アレグラ錠":        _pack("4490023F1270_1_05"),
    # ── 認知症 ──
    "ドネペジル":        _pack("1190012F1042_1_13"),   # 後発「DSEP」
    # ── 精神・神経 ──
    "アミトリプチリン":  _pack("1179002F1122_1_08"),   # 後発「サワイ」
    "デュロキセチン":    _pack("1179052M1111_1_03"),   # 後発「トーワ」
    "プレガバリン":      _pack("1190017F1185_1_03"),   # 後発「トーワ」
    "ゾルピデム":        _pack("1129009F1335_1_09"),   # 後発「明治」
    "クロナゼパム":      _pack("1139003C1052_2_15"),   # ランドセン
    # ── OTC ──
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
