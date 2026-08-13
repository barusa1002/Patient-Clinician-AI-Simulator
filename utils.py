# utils.py
# 共通ユーティリティ関数群


import re
import html as _html
import urllib.parse
import streamlit as st
from datetime import datetime, timedelta

import drug_info


# ==========================================================
# 日付テンプレート置換
# {{TODAY}} / {{TODAY+3D}} / {{TODAY-1Y}} などを実際の日付に変換する
# ==========================================================
_DATE_TEMPLATE_RE = re.compile(r"\{\{TODAY([+-]\d+)?([DY])?\}\}")


def replace_date_templates(text: str) -> str:
    today = datetime.now()

    def repl(match):
        number = match.group(1)
        unit = match.group(2)
        date = today

        if number and unit:
            value = int(number)
            if unit == "D":
                date = today + timedelta(days=value)
            elif unit == "Y":
                date = today + timedelta(days=365 * value)

        return date.strftime("%Y年%m月%d日")

    return _DATE_TEMPLATE_RE.sub(repl, text)

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
# 先頭ラベルのパターン：
# ・英字ラベル（RESPONSE: / PRESENTER: / SPEAKER: など任意の英単語＋コロン）
#   → Geminiが毎回違うラベルを付けてくるためブラックリストではなく汎用マッチ
# ・日本語ラベル（回答: / 発言: など）は既知のものだけ対象
_LEADING_LABEL = re.compile(
    r"^(?:[A-Za-z][A-Za-z0-9 _\-]{0,24}|回答|発言|セリフ|患者|返答|応答|出力)[:：]\s*"
)


def _strip_leading_label(text: str) -> str:
    """先頭の「ラベル＋コロン」を（多重に付いていても）すべて剥がす"""
    text = text.strip()
    while True:
        new_text = _LEADING_LABEL.sub("", text, count=1).strip()
        if new_text == text:
            return text
        text = new_text


def strip_thought(text: str) -> str:
    """
    LLM出力から思考部分を削除し、患者の発話だけを返す
    """

    if not text:
        return text

    # THOUGHT削除（明示ラベルあり）
    text = re.sub(r"THOUGHT.*?回答[:：]", "", text, flags=re.DOTALL)
    text = re.sub(r"THOUGHT.*", "", text)

    # 先頭のラベル削除（RESPONSE: / PRESENTER: / 回答: など）
    text = _strip_leading_label(text)

    # 発話ラベルがある場合はそこだけ残す
    if "発話：" in text:
        text = text.split("発話：")[-1]

    # Gemini 2.5の暗黙的思考対応（1）：
    # 空行区切りで複数段落がある場合は最後の段落のみ残す
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) > 1:
        text = paragraphs[-1]

    # 段落選択後に残ったラベルも剥がす
    # （思考段落の後ろにラベル付きセリフが来るパターン対策）
    text = _strip_leading_label(text)

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
    r'(錠|カプセル|カプセル剤|散|液|テープ|パッチ|OD|DS|エアー|坐剤|吸入'
    r'|点滴静注|静注|点滴|注射|バイアル|mg|μg|mL|mcg)'
)
_SKIP_PREFIXES = (
    "用法", "用量", "日数", "副作用", "効果", "残薬",
    "1回", "1日", "注意", "【現在の処方】", "発作", "包装", "使用",
    "血圧", "血糖", "鎮痛", "抗炎", "胃酸", "利尿",
    "処方提案", "理由", "現在の処方", "変更前", "変更後", "最新検査値",
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
    "アムロジピン":      _pack("2171022F1282_1_22"),   # 後発「サワイ」
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
    "アピキサバン":      _pack("3339004F1029_1_22"),   # エリキュース（先発）
    "エリキュース":      _pack("3339004F1029_1_22"),
    "クロピドグレル":    _pack("3399008F1203_1_12"),   # 後発「サワイ」
    # ── 消化器 ──
    # ランソプラゾール：旧品目コード(2329023F1101)は失効し添付文書が参照不可のため、
    # 直接リンクは持たせずPMDA医薬品検索へフォールバックさせる
    "トラネキサム酸":    _pack("3327002F1169_1_07"),   # 後発「YD」
    "酸化マグネシウム":  _pack("2344009F1086_1_10"),   # 後発「ケンエー」
    # ── 糖尿病・代謝 ──
    "メトホルミン":      _pack("3962002F2124_1_06"),   # 後発「DSPB」
    "グリメピリド":      _pack("3961008F1217_1_11"),   # 後発「サワイ」
    "エンパグリフロジン": _pack("3969023F1023_1_19"),  # ジャディアンス（先発）
    "ジャディアンス":    _pack("3969023F1023_1_19"),
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
# 処方内容を「薬剤情報提供文書」風のカードHTMLに変換
#   ・薬剤ごとにカード化し、用法用量／働き／注意 を項目立てで表示
#   ・薬品名は従来どおりPMDA添付文書へのリンクを保持
# ==========================================================

def _pmda_url_for(name: str) -> str:
    for key, url in _DRUG_URL_MAP.items():
        if key in name:
            return url
    return (
        "https://www.pmda.go.jp/PmdaSearch/iyakuSearch/"
        f"?name={urllib.parse.quote(name)}"
    )


# 処方区分バッジ（（新規）（減量）など行頭の括弧書き）。表示名は原文どおりとする。
_BADGE_STYLES = {
    "新規追加": "b-add",
    "新規":     "b-new",
    "追加":     "b-add",
    "継続":     "b-cont",
    "増量":     "b-up",
    "減量":     "b-down",
    "中止":     "b-stop",
    "変更":     "b-new",
    "推奨薬":   "b-add",
}
_BADGE_RE = re.compile(r'^[（(]\s*(' + "|".join(_BADGE_STYLES) + r')\s*[)）]\s*')

# 薬品名行に混在した用法用量を切り出すための目印
_INLINE_DOSE_RE = re.compile(r'(1日\d+回|1回\d|\d+日分|発作時|頓用|症状がある時)')

# 用法用量とみなす行
_DOSE_HEAD_RE = re.compile(r'^(1日|1回|\d+日分|発作時|頓用|毎食|就寝前|起床時|症状)')
_DOSE_WORD_RE = re.compile(r'(食後|食前|食間|就寝前|貼付|吸入|皮下注射|日分)')

# 全体の補足へ回すラベル
_GLOBAL_LABELS = ("降圧目標", "管理目標", "血糖管理目標", "目標", "重要", "変更理由", "減量理由")

# それ自体が節見出しになっている括弧行（例：「（副作用）」「（提案）」）
# 薬剤名を含まない短い括弧書きのみを対象にする
_SECTION_MARK_RE = re.compile(r'^[（(][^）)]{1,12}[)）]$')

# 「Rp1：」のような処方番号の接頭辞
_RP_PREFIX_RE = re.compile(r'^Rp\d*\s*[：:]\s*')

_LABEL_RE = re.compile(r'^([^：:]{1,14})[：:]\s*(.*)$')


def _new_drug(badge, name, remark="", dose=None):
    return {"badge": badge, "name": name, "remark": remark,
            "dose": list(dose or []), "effect": [], "side": [],
            "caution": [], "extra": [], "free": []}


def _classify_line(drug: dict, line: str) -> None:
    """薬剤カード内の1行を、用法・働き・副作用・注意に振り分ける"""
    m = _LABEL_RE.match(line)
    label, value = (m.group(1), m.group(2)) if m else (None, None)

    if label in ("効果", "作用", "働き"):
        drug["effect"].append(value)
        return
    if label in ("主な副作用", "副作用", "重大な副作用", "副作用例", "注意すべき副作用"):
        drug["side"].append(value)
        return
    if label in ("注意", "使用後", "使用上の注意"):
        drug["caution"].append(value)
        return
    if label in ("用法", "用量", "用法用量", "用法・用量", "使用方法"):
        drug["dose"].append(value)
        return
    if label:
        drug["extra"].append((label, value))
        return

    # ラベルなし行：用法用量らしければ用法へ、それ以外は補足へ
    if _DOSE_HEAD_RE.match(line) or _DOSE_WORD_RE.search(line):
        drug["dose"].append(line)
    else:
        drug["free"].append(line)


# 複数薬剤にまたがる説明を全体備考へ移すときのラベル
_MOVE_LABELS = {"effect": "効果", "side": "主な副作用", "caution": "注意"}


def _move_shared_notes(drugs, notes):
    """複数の薬剤名を含む説明文は、特定の1剤ではなく処方全体の補足として扱う"""
    # 説明文中では「アムロジピン錠」ではなく「アムロジピン」と書かれるため、
    # 剤形（錠・カプセル等）を取り除いた成分名で照合する
    bases = []
    for d in drugs:
        m = re.match(
            r'^([^\d\s（(]+?)(錠|カプセル|散|液|テープ|パッチ|坐剤|吸入|'
            r'点滴|注射|静注|OD|DS)',
            d["name"],
        )
        base = m.group(1) if m else re.split(r'[\d\s（(]', d["name"])[0]
        if len(base) >= 3:
            bases.append(base)

    moved = []
    for d in drugs:
        for key, label in _MOVE_LABELS.items():
            keep = []
            for text in d[key]:
                if sum(1 for b in bases if b in text) >= 2:
                    moved.append(f"{label}：{text}")
                else:
                    keep.append(text)
            d[key] = keep
    # 備考の先頭側（■見出しより前）に差し込む
    for i, text in enumerate(moved):
        notes.insert(i, ("body", text))


def parse_prescription(text: str):
    """
    処方テキストを (ブロック列, 薬剤リスト, 全体補足) に構造化する。

    ブロック列は出現順に ("text", 文字列) / ("drug", 薬剤dict) を並べたもの。
    「（現在処方）」「（提案）」のような節見出しが薬剤の間に挟まる書式でも、
    元の順序どおりに表示できるようにするための構造。
    """
    blocks, drugs, notes = [], [], []
    cur = None
    in_notes = False
    last_target = "preamble"   # 直前の行をどこへ入れたか（字下げ継続行の行き先）

    for raw in text.split("\n"):
        line = raw.strip("　 \t")
        if not line:
            continue

        # 「■ 見出し」以降はすべて全体補足として扱う
        if line.startswith("■"):
            in_notes = True
            last_target = "notes"
            notes.append(("head", line.lstrip("■ 　").strip()))
            continue
        if in_notes:
            notes.append(("body", line))
            continue

        # 目標値・注記は薬剤ではなく全体補足へ
        if line.startswith("※") or any(line.startswith(g) for g in _GLOBAL_LABELS):
            notes.append(("body", line))
            last_target = "notes"
            continue

        # 字下げされた行は直前ブロックの続きとして扱う
        # （「※…」の折り返しなどが薬剤として誤認識されるのを防ぐ）
        if raw[:1] in ("　", " ", "\t"):
            if last_target == "notes":
                notes.append(("body", line))
            elif cur is not None:
                _classify_line(cur, line)
            else:
                blocks.append(("text", line))
            continue

        # 「推奨薬：〇〇」は1剤として扱う
        if line.startswith("推奨薬："):
            cur = _new_drug(("推奨薬", "b-add"), line[4:].strip())
            drugs.append(cur)
            blocks.append(("drug", cur))
            last_target = "drug"
            continue

        # 「（副作用）」「（提案）」のような、それ自体が節見出しの括弧行は
        # 直前の薬剤にぶら下げず、以降を区切るセクション見出しとして扱う
        if _SECTION_MARK_RE.match(line):
            cur = None
            blocks.append(("head", line.strip("（）()")))
            last_target = "preamble"
            continue

        # 「Rp1：〇〇錠」のような処方番号の接頭辞を落とす
        line = _RP_PREFIX_RE.sub("", line)

        # 薬品名行かどうか
        body = _BADGE_RE.sub("", line)
        bm = _BADGE_RE.match(line)
        is_drug = (
            _DRUG_UNITS_RE.search(body)
            and not any(body.startswith(s) for s in _SKIP_PREFIXES)
            # 「（＝1日2吸入…）」のような括弧書きの補足は薬剤とみなさない
            and not (line[:1] in ("（", "(") and bm is None)
        )

        if is_drug:
            # 行末の「※〜」を注記として分離
            remark = ""
            if "※" in body:
                body, _, remark = body.partition("※")
                body, remark = body.strip(), remark.strip()

            # 同一行に用法が続く場合は分離（例：〇〇錠 500mg 1日2回 朝夕食後）
            dose_inline = ""
            dm = _INLINE_DOSE_RE.search(body)
            if dm and dm.start() > 0:
                dose_inline = body[dm.start():].strip()
                body = body[: dm.start()].strip()

            badge = (bm.group(1), _BADGE_STYLES[bm.group(1)]) if bm else None
            cur = _new_drug(badge, body, remark,
                            [dose_inline] if dose_inline else [])
            drugs.append(cur)
            blocks.append(("drug", cur))
            last_target = "drug"
            continue

        if cur is None:
            blocks.append(("text", line))
            last_target = "preamble"
        else:
            _classify_line(cur, line)
            last_target = "drug"

    _move_shared_notes(drugs, notes)
    return blocks, drugs, notes


def _row(label: str, value: str, cls: str = "", open_: bool = False) -> str:
    """項目名をクリックすると内容が開く折りたたみ行を返す。

    項目名は内容の上に置く（横並びにすると狭いサイドバーで
    内容の幅が潰れて読みにくくなるため）。
    """
    if not label:
        return f'<div class="rx-item {cls}"><div class="rx-v">{value}</div></div>'
    return (
        f'<details class="rx-item {cls}"{" open" if open_ else ""}>'
        f'<summary class="rx-k">{_html.escape(label)}</summary>'
        f'<div class="rx-v">{value}</div></details>'
    )


def make_prescription_leaflet(prescription_text: str) -> str:
    """処方内容を薬剤情報提供文書風のHTMLにして返す"""
    blocks, drugs, notes = parse_prescription(prescription_text)

    # 薬剤が1つも抽出できない場合は素のテキストとして表示（安全側）。
    # ただし既知の薬品名が含まれていれば添付文書リンクだけは維持する。
    if not drugs:
        lines_html = []
        for raw in prescription_text.split("\n"):
            esc = _html.escape(raw)
            hit = max(
                (k for k in _DRUG_URL_MAP if k in raw),
                key=len,
                default=None,
            )
            if hit:
                esc = esc.replace(
                    _html.escape(hit),
                    f'<a class="rx-name" href="{_html.escape(_DRUG_URL_MAP[hit])}" '
                    f'target="_blank" rel="noopener">{_html.escape(hit)}</a>',
                    1,
                )
            lines_html.append(esc)
        return (
            '<div class="rx-doc"><div class="rx-plain">'
            + "<br>".join(lines_html)
            + "</div></div>"
        )

    parts = ['<div class="rx-doc">']

    for kind, item in blocks:
        # ── 節見出し・説明文（出現順に描画する）──
        if kind == "head":
            parts.append(f'<div class="rx-sec">{_html.escape(item)}</div>')
            continue
        if kind == "text":
            parts.append(f'<div class="rx-pre">{_html.escape(item)}</div>')
            continue

        d = item
        parts.append('<div class="rx-card">')

        # ── 見出し（バッジ＋薬品名リンク）──
        head = ['<div class="rx-head">']
        if d["badge"]:
            text, cls = d["badge"]
            head.append(f'<span class="rx-badge {cls}">{text}</span>')
        name = d["name"]
        # 添付文書検索用に、規格を除いた薬品名を取り出す
        nm = re.match(r'^([^\d]+?)[\s]*[\d.]', name)
        lookup = nm.group(1).strip() if nm else name
        head.append(
            f'<a class="rx-name" href="{_html.escape(_pmda_url_for(lookup))}" '
            f'target="_blank" rel="noopener">{_html.escape(name)}</a>'
        )
        head.append("</div>")
        parts.append("".join(head))

        if d["remark"]:
            parts.append(f'<div class="rx-remark">※{_html.escape(d["remark"])}</div>')

        join = lambda xs: "<br>".join(_html.escape(x) for x in xs)

        # くすりのしおりの記載内容（該当薬剤のみ）
        info = drug_info.lookup(name)

        # ① 用法・用量
        # ここだけは必ず処方箋どおりの内容を出す。しおりの一般的な用法
        # （「通常、成人は1日1回…」）ではなく、この患者に出ている用法を
        # 見せる必要があるため、drug_info は参照しない。
        # 最も重要な項目なので、この行だけ最初から開いておく。
        if d["dose"]:
            parts.append(_row("用法・用量", join(d["dose"]), open_=True))

        # ② この薬の作用と効果（しおりを優先し、無ければシナリオ側の記載）
        effect = info["作用と効果"] if info else None
        if effect:
            parts.append(_row("この薬の作用と効果", _html.escape(effect)))
        elif d["effect"]:
            parts.append(_row("この薬の作用と効果", join(d["effect"])))

        for label, value in d["extra"]:
            parts.append(_row(label, _html.escape(value)))

        # ③ 注意事項（伝えること＋生活上の注意）
        caution_html = []
        for kind, text in drug_info.caution_lines(info):
            cls = "rx-cap" if kind == "head" else "rx-li"
            caution_html.append(f'<div class="{cls}">{_html.escape(text)}</div>')
        # シナリオ固有の注意（造影剤休薬など）も併せて載せる
        for text in d["caution"]:
            caution_html.append(f'<div class="rx-li">{_html.escape(text)}</div>')
        if caution_html:
            parts.append(_row("注意事項", "".join(caution_html)))

        # ④ 主な副作用
        side = info["主な副作用"] if info else None
        if side:
            parts.append(_row("主な副作用", _html.escape(side), cls="rx-side"))
        elif d["side"]:
            parts.append(_row("主な副作用", join(d["side"]), cls="rx-side"))

        if d["free"]:
            parts.append(_row("", join(d["free"])))

        parts.append("</div>")

    if notes:
        parts.append('<div class="rx-notes">')
        for kind, text in notes:
            if kind == "head":
                parts.append(f'<div class="rx-notes-head">{_html.escape(text)}</div>')
            else:
                parts.append(f'<div>{_html.escape(text)}</div>')
        parts.append("</div>")

    parts.append("</div>")
    return "".join(parts)


# ==========================================================
# セッションリセット関数
# ==========================================================
def reset_session():
    for key in [
        "chat_history", "chat_session", "current_scenario",
        "prescription_notes", "prescription_submitted",
        "soap_notes", "soap_submitted", "show_soap_form",
        "model_answer_text", "evaluation_done", "last_evaluation_json",
        "hint_text", "run_evaluation",
    ]:
        if key in st.session_state:
            del st.session_state[key]
