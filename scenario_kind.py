# scenario_kind.py
# 課題（シナリオ）とサブシナリオの名前から、「どの業務の練習か」を決める。
#
# スキルアップモードの疾患別の課題や、初期研修モードの「一生を追う課題」では、
# 1つの課題の中に服薬指導・疑義照会・退院時指導などが混ざる。
# そこでサブシナリオ名の先頭に業務名を書き、評価項目・記録フォーム・SOAPの出し分けに使う。
#
#   課題名「がん（病院）」               サブ「②服薬指導｜術後補助化学療法（S-1）の開始」 → 服薬指導（病院）
#   課題名「松田 一郎さんの40年（薬局）」 サブ「③68歳 疑義照会｜前立腺肥大の薬」         → 疑義照会（薬局）
#   課題名「疑義照会（薬局）」           サブ「①がん｜S-1の用量」                      → 疑義照会（薬局）
import re

SETTINGS = ("（薬局）", "（病院）")

# サブシナリオ名の先頭に書ける業務名
KINDS = (
    "服薬指導", "吸入指導", "OTC相談", "疑義照会", "薬事トリアージ",
    "相互作用", "腎機能確認", "ポリファーマシー", "服薬支援",
    "初回面談", "退院時指導", "情報提供",
    "処方提案", "TDM", "適応外確認", "カンファレンス", "看護師連携",
)

# 薬剤師が医師・看護師と話す業務（SOAP薬歴の対象にしない）
STAFF_KINDS = ("疑義照会", "情報提供", "処方提案", "TDM", "適応外確認", "カンファレンス", "看護師連携")

_CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
_AGE = re.compile(r"^\d+歳\s*")


def _setting(scenario):
    for s in SETTINGS:
        if scenario.endswith(s):
            return s
    return ""


def task_kind(scenario, subscenario):
    """業務名＋（薬局）/（病院）を返す。決められないときは課題名をそのまま返す。"""
    setting = _setting(scenario)
    if not setting:
        return scenario
    if scenario[: -len(setting)] in KINDS:  # 課題名そのものが業務名（疑義照会（薬局）など）
        return scenario
    head = subscenario.split("｜")[0].lstrip(_CIRCLED).strip()
    head = _AGE.sub("", head)
    if head in KINDS:
        return head + setting
    return scenario


def is_gigi(scenario, subscenario):
    return task_kind(scenario, subscenario).startswith("疑義照会")


def is_staff_talk(scenario, subscenario):
    return task_kind(scenario, subscenario).startswith(STAFF_KINDS)
