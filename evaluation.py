#evaluation.py
import os
import json
from db import supabase
from datetime import datetime

EVAL_FILE = "data/evaluations.json"
os.makedirs("data", exist_ok=True)

# ==========================================================
# 評価チェックリスト（シナリオ別）
# ==========================================================

EVALUATION_CHECKLISTS = {

"薬局での患者応対": {
    "あいさつ": None,
    "自己紹介": None,
    "患者氏名確認": None,
    "来局目的確認": None,
    "インタビュー目的説明": None,
    "お薬手帳確認": None,
    "症状確認": None,
    "症状の程度確認": None,
    "症状の経過確認": None,
    "他症状確認": None,
    "患者不安確認": None,
    "既往歴確認": None,
    "アレルギー確認": None,
    "副作用歴確認": None,
    "他院受診確認": None,
    "使用薬確認": None,
    "サプリメント確認": None,
    "喫煙飲酒確認": None,
    "後発医薬品希望確認": None,
    "質問確認": None,
    "記録共有": "本日聞き取った内容は記録に残し、指導薬剤師に伝えます。",
    "終了挨拶": None,
},

"病棟での初回面談": {
    "入室挨拶": None,
    "入室許可確認": None,
    "自己紹介": None,
    "患者氏名確認": None,
    "来室目的説明": None,
    "お薬手帳確認": None,
    "症状確認": None,
    "症状の程度確認": None,
    "症状の経過確認": None,
    "他症状確認": None,
    "現在状態確認": None,
    "患者不安確認": None,
    "アレルギー確認": None,
    "副作用歴確認": None,
    "他院受診確認": None,
    "使用薬確認": None,
    "サプリメント確認": None,
    "喫煙飲酒確認": None,
    "質問確認": None,
    "記録共有": "本日聞き取った内容は記録に残し、指導薬剤師に伝えます。",
    "終了挨拶": None,
},

"来局者応対": {
    "あいさつ": None,
    "自己紹介": None,
    "来局目的確認": None,
    "インタビュー目的説明": None,
    "症状確認": None,
    "症状の程度確認": None,
    "症状の経過確認": None,
    "他症状確認": None,
    "来局者不安確認": None,
    "既往歴確認": None,
    "アレルギー確認": None,
    "副作用歴確認": None,
    "受診有無確認": None,
    "使用薬確認": None,
    "サプリメント確認": None,
    "喫煙飲酒確認": None,
    "質問確認": None,
    "薬剤希望確認": None,
    "記録共有": "本日聞き取った内容は記録に残し、指導薬剤師に伝えます。",
    "終了挨拶": None,
},

"在宅での薬学的管理": {
    "入室挨拶": None,
    "入室許可確認": None,
    "自己紹介": None,
    "患者氏名確認": None,
    "訪問目的説明": None,
    "体調確認": None,
    "薬効確認": None,
    "副作用確認": None,
    "観察所見共有": None,
    "患者不安確認": None,
    "食事確認": None,
    "排泄確認": None,
    "睡眠確認": None,
    "入浴確認": None,
    "生活不自由確認": None,
    "服薬状況確認": None,
    "服薬目的理解確認": None,
    "用法用量理解確認": None,
    "残薬確認": None,
    "質問確認": None,
    "記録共有": "本日聞き取った内容は記録に残し、指導薬剤師に伝えます。",
    "終了挨拶": None,
},

"薬局での薬剤交付": {
    "患者呼び入れ": None,
    "自己紹介": None,
    "患者氏名確認": None,
    "説明目的説明": None,
    "症状再確認": None,
    "患者不安確認": None,
    "薬剤名提示": None,
    "薬効説明": None,
    "数量確認": None,
    "使用方法説明": None,
    "薬剤情報文書提示": None,
    "アレルギー再確認": None,
    "副作用歴再確認": None,
    "副作用説明": None,
    "質問確認": None,
    "記録共有": "本日聞き取った内容は記録に残し、指導薬剤師に伝えます。",
    "終了挨拶": None,
},

"病棟での服薬指導": {
    "入室挨拶": None,
    "入室許可確認": None,
    "自己紹介": None,
    "患者氏名確認": None,
    "来室目的説明": None,
    "症状再確認": None,
    "現在状態確認": None,
    "患者不安確認": None,
    "薬剤名提示": None,
    "薬効説明": None,
    "数量確認": None,
    "使用方法説明": None,
    "薬剤情報文書提示": None,
    "アレルギー再確認": None,
    "副作用歴再確認": None,
    "副作用説明": None,
    "質問確認": None,
    "記録共有": "本日聞き取った内容は記録に残し、指導薬剤師に伝えます。",
    "終了挨拶": None,
},

"一般用医薬品の情報提供": {
    "来局者呼び入れ": None,
    "自己紹介": None,
    "説明目的説明": None,
    "症状再確認": None,
    "来局者不安確認": None,
    "薬剤提示": None,
    "薬効説明": None,
    "使用方法説明": None,
    "使用期限確認": None,
    "説明文書提示": None,
    "添付文書説明": None,
    "アレルギー再確認": None,
    "副作用歴再確認": None,
    "使用上注意説明": None,
    "受診目安説明": None,
    "質問確認": None,
    "記録共有": "本日聞き取った内容は記録に残し、指導薬剤師に伝えます。",
    "購入意思確認": None,
},

"疑義照会": {
    "相手医療機関確認": None,
    "薬局名名乗り": None,
    "自己紹介": None,
    "医師氏名確認": None,
    "疑義照会目的説明": None,
    "相手都合確認": None,
    "処方日患者名伝達": None,
    "疑義内容説明": None,
    "訂正内容復唱確認": None,
    "記録共有説明": None,
    "終了挨拶": None,
    "電話終了作法": None,
    "声量速度適切": None,
    "丁寧言葉遣い": None,
    "電話応対適切": None,
    "備考欄として記載": None,
    "日時記載": None,
    "照会方法記載": None,
    "自分の名前記載": None,
    "医師名記載": None,
    "変更内容適正": None,
},

"医療従事者への情報提供": {
    "医師挨拶": None,
    "医師氏名確認": None,
    "自己紹介": None,
    "指導薬剤師協議説明": None,
    "面談目的説明": None,
    "相手都合確認": None,
    "患者特定説明": None,
    "情報取得日説明": None,
    "服薬状況報告": None,
    "薬効報告": None,
    "副作用報告": None,
    "生活状況報告": None,
    "患者情報質問確認": None,
    "処方提案実施": None,
    "提案理由説明": None,
    "提案薬剤名説明": None,
    "提案用法用量説明": None,
    "医師処方復唱": None,
    "依頼質問確認": None,
    "医師依頼復唱": None,
    "姿勢態度適切": None,
    "声量速度適切": None,
    "丁寧言葉遣い": None,
    "傾聴姿勢": None,
    "会話流れ自然": None,
    "記録共有": "本日聞き取った内容は記録に残し、指導薬剤師に伝えます。",
    "終了挨拶": None,
},

}


# ==========================================================
# AI評価プロンプト作成
# ==========================================================

def build_evaluation_prompt(scenario, subscenario, chat_history):

    conversation = ""
    for role, msg in chat_history:
        speaker = "実習生" if role == "user" else "患者・医療者"
        conversation += f"{speaker}：{msg}\n"

    # 評価項目取得（辞書のキーを使用）
    checklist = EVALUATION_CHECKLISTS.get(scenario, {})

    checklist_text = "\n".join(
        f"- {item}" for item in checklist
    )

    prompt = f"""
あなたは薬学実習の評価者です。
以下の会話を客観的に評価してください。

【シナリオ】
{scenario} / {subscenario}

【会話ログ】
{conversation}

【評価項目】
{checklist_text}

【評価ルール】

1 = 達成  
0 = 未達成  
null = 会話から判断できない

重要ルール：

・scoresには必ず上記の評価項目のみ含める  
・新しい評価項目を追加しない  
・評価項目を省略しない  

【出力形式】

必ず以下のJSONのみ出力してください。

{{
  "scores": {{
    "評価項目": 1
  }},
  "achieved": [
    "達成できた項目"
  ],
  "missing": [
    {{
      "item": "不足項目",
      "reason": "理由"
    }}
  ],
  "advice": [
    "改善アドバイス"
  ],
  "comment": "総合評価"
}}

JSON以外の文章は絶対に出力しない。
"""

    return prompt


# ==========================================================
# 評価保存（Supabase版）
# ==========================================================
def save_evaluation(user_id, scenario, subscenario, chat_history, evaluation_text):

    try:
        supabase.table("evaluations").insert({
            "user_id": user_id,
            "scenario": scenario,
            "subscenario": subscenario,
            "evaluation": {
                "chat_history": chat_history,
                "result": evaluation_text
            }
        }).execute()

    except Exception as e:
        print(f"保存エラー: {e}")

# ==========================================================
# 個人評価取得
# ==========================================================

def load_user_evaluations(user_id):

    res = supabase.table("evaluations") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()

    return res.data


# ==========================================================
# 全学生評価取得（教員用）
# ==========================================================
def load_all_students_evaluations():

    res = supabase.table("evaluations") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()

    result = {}

    for row in res.data:
        uid = row["user_id"]

        if uid not in result:
            result[uid] = []

        eval_data = row.get("evaluation", {})

        result[uid].append({
            "timestamp": row["created_at"],
            "scenario": row.get("scenario"),
            "subscenario": row.get("subscenario"),
            "chat_history": eval_data.get("chat_history"),
            "evaluation": eval_data.get("result")
        })

    return result

