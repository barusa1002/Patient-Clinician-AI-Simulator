# pdf_export.py
import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Streamlit Cloud (Debian) で fonts-ipafont-gothic をインストールした場合のパス
# ローカル開発用に fonts/ ディレクトリのフォントもフォールバックとして参照する
_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "fonts/ipaexg.ttf",
    "fonts/ipagp.ttf",
    "fonts/ipag.ttf",
]

_FONT_NAME = "IPAGothic"
_font_registered = False


def _register_font() -> bool:
    global _font_registered
    if _font_registered:
        return True
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(_FONT_NAME, path))
                _font_registered = True
                return True
            except Exception:
                continue
    return False


def _style(name: str, **kwargs) -> ParagraphStyle:
    return ParagraphStyle(name, fontName=_FONT_NAME, **kwargs)


def generate_evaluation_pdf(
    scenario: str,
    subscenario: str,
    chat_history: list,
    evaluation_json: dict,
    learning_mode: str = "スタンダードモード",
) -> bytes:
    """評価結果と会話履歴をまとめた PDF を生成して bytes で返す。"""

    if not _register_font():
        raise RuntimeError(
            "日本語フォントが見つかりません。"
            "packages.txt に fonts-ipafont-gothic を追加するか、"
            "fonts/ ディレクトリにフォントファイルを配置してください。"
        )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    C_PURPLE = colors.HexColor("#7c3aed")
    C_GRAY   = colors.HexColor("#6b7280")
    C_GREEN  = colors.HexColor("#065f46")
    C_RED    = colors.HexColor("#991b1b")
    C_BLUE   = colors.HexColor("#1d4ed8")
    C_DARK   = colors.HexColor("#1f2937")

    title_style   = _style("title",  fontSize=17, textColor=C_DARK,   spaceAfter=3)
    meta_style    = _style("meta",   fontSize=9,  textColor=C_GRAY,   spaceAfter=2)
    h1_style      = _style("h1",     fontSize=13, textColor=C_PURPLE, spaceBefore=10, spaceAfter=4, leading=18)
    body_style    = _style("body",   fontSize=10, textColor=C_DARK,   spaceAfter=3,   leading=16)
    small_style   = _style("small",  fontSize=9,  textColor=C_GRAY,   spaceAfter=2)
    user_style    = _style("user",   fontSize=10, textColor=C_BLUE,   spaceAfter=2,   leading=15, leftIndent=4)
    ai_style      = _style("ai",     fontSize=10, textColor=C_GREEN,  spaceAfter=2,   leading=15, leftIndent=4)

    def hr_thick():
        return HRFlowable(width="100%", thickness=2, color=C_PURPLE, spaceAfter=4)

    def hr_thin():
        return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb"), spaceAfter=4)

    elems = []
    now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    # ── タイトル ──────────────────────────────────────────────
    elems.append(Paragraph("シミュレーション 評価レポート", title_style))
    elems.append(hr_thick())
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(f"課題：{scenario}　／　{subscenario}", meta_style))
    elems.append(Paragraph(f"学習モード：{learning_mode}　　実施日時：{now_str}", meta_style))
    elems.append(Spacer(1, 4 * mm))
    elems.append(hr_thin())

    # ── 評価サマリー ─────────────────────────────────────────
    scores = evaluation_json.get("scores", {})
    achieved_cnt = sum(1 for v in scores.values() if v == 1)
    missing_cnt  = sum(1 for v in scores.values() if v == 0)
    total        = achieved_cnt + missing_cnt
    rate         = achieved_cnt / total if total > 0 else 0
    passed       = rate >= 0.7

    elems.append(Paragraph("📊 評価サマリー", h1_style))

    summary_data = [
        ["達成率", f"{achieved_cnt} / {total}　（{rate * 100:.1f}%）"],
        ["合否判定", "✔ 評価基準達成" if passed else "✘ 評価基準未達"],
    ]
    tbl = Table(summary_data, colWidths=[35 * mm, 120 * mm])
    tbl.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (-1, -1), _FONT_NAME),
        ("FONTSIZE",  (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), C_GRAY),
        ("TEXTCOLOR", (1, 1), (1, 1), C_GREEN if passed else C_RED),
        ("FONTNAME",  (1, 1), (1, 1), _FONT_NAME),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f9fafb"), colors.white]),
        ("BOX",       (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    elems.append(tbl)
    elems.append(Spacer(1, 4 * mm))

    # ── ① 達成できた項目 ────────────────────────────────────
    elems.append(Paragraph("① 達成できた項目", h1_style))
    achieved_items = evaluation_json.get("achieved", [])
    if achieved_items:
        for item in achieved_items:
            elems.append(Paragraph(f"✓　{item}", body_style))
    else:
        elems.append(Paragraph("（該当なし）", small_style))
    elems.append(Spacer(1, 3 * mm))

    # ── ② 不足・不十分な項目 ────────────────────────────────
    elems.append(Paragraph("② 不足・不十分な項目", h1_style))
    missing_items = evaluation_json.get("missing", [])
    if missing_items:
        for m in missing_items:
            elems.append(Paragraph(f"▶　{m.get('item', '')}", _style("mi", fontSize=10, textColor=C_DARK, spaceBefore=4, spaceAfter=1, leading=15)))
            elems.append(Paragraph(f"　理由：{m.get('reason', '')}", small_style))
    else:
        elems.append(Paragraph("（該当なし）", small_style))
    elems.append(Spacer(1, 3 * mm))

    # ── ③ 改善アドバイス ────────────────────────────────────
    elems.append(Paragraph("③ 改善アドバイス", h1_style))
    advice_list = evaluation_json.get("advice", [])
    if advice_list:
        for adv in advice_list:
            elems.append(Paragraph(f"•　{adv}", body_style))
    else:
        elems.append(Paragraph("（アドバイスなし）", small_style))
    elems.append(Spacer(1, 3 * mm))

    # ── ④ 総合評価 ──────────────────────────────────────────
    elems.append(Paragraph("④ 総合評価", h1_style))
    comment = evaluation_json.get("comment", "（総合評価なし）")
    elems.append(Paragraph(comment, body_style))
    elems.append(Spacer(1, 6 * mm))

    # ── 会話履歴 ────────────────────────────────────────────
    elems.append(hr_thin())
    elems.append(Paragraph("💬 会話履歴", h1_style))
    elems.append(Spacer(1, 2 * mm))

    for role, msg in chat_history:
        if role == "user":
            elems.append(Paragraph(f"【実習生】　{msg}", user_style))
        else:
            elems.append(Paragraph(f"【患者・医療者】　{msg}", ai_style))
        elems.append(Spacer(1, 1 * mm))

    doc.build(elems)
    return buf.getvalue()
