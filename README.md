# 患者・医療従事者役 AI シミュレーター

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.41.1-FF4B4B?logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?logo=google&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Auth_+_DB-3ECF8E?logo=supabase&logoColor=white)
![Version](https://img.shields.io/badge/version-1.0.0-blue)

薬学生向けのコミュニケーション実習支援ツール。AI が患者・医師・看護師などの役を演じ、テキスト・音声で会話練習ができる。会話終了後に AI による自動フィードバックを取得できる。

**本番URL**: https://patient-clinician-ai-simulator-showa-pharmaceutical-university.streamlit.app/

---

## 主な機能

| 機能 | 説明 |
|------|------|
| 会話シミュレーション | AI（Gemini 2.5 Flash）が患者・医師・看護師役を担い、リアルな会話練習 |
| 音声読み上げ（TTS） | gTTS による AI 発話の音声合成（スマートフォン対応） |
| 音声入力（STT） | Whisper による音声認識（PC のみ） |
| 自動評価 | 会話終了後に AI がチェックリスト + SOAP 薬歴のフィードバックを生成 |
| 処方箋備考欄フォーム | 疑義照会シナリオ完了後に専用フォームを自動表示 |
| 参考資料リンク | シナリオに応じた添付文書・指導箋 PDF を画面内に提示 |
| スタッフダッシュボード | 教員・指導者が全学生の評価結果を一覧確認 |
| 自動ログアウト | 30 分無操作でセッション終了（Supabase DB と連携） |
| チュートリアル | 初回ログイン時にアプリの使い方をガイド |
| モバイル対応 | スマートフォンでも使えるレスポンシブ UI |

---

## 学習モード

| モード | 対象 | 概要 |
|--------|------|------|
| **OSCE 対策** | 薬学 4〜6 年生 | 客観的臨床能力試験の模擬練習（基本的なコミュニケーション全般） |
| **実習前練習** | 薬学 5 年生 | 薬局・病院実習に特化した疾患別シナリオ（服薬指導・吸入指導等） |
| **初期研修** | 薬剤師研修生 | 複雑事例・チーム医療・処方提案など実践的な対応練習 |

---

## シナリオ一覧

### OSCE 対策モード

**患者・来局者応対**（4 シナリオ × 各 3 サブシナリオ）

| シナリオ | 内容 |
|---------|------|
| 薬局での患者応対 | 初回面談（頭痛、喘息、アレルギー性鼻炎） |
| 病棟での初回面談 | 入院患者問診（脳梗塞、心不全、術後） |
| 来局者応対 | OTC 相談（胃症状、家族代理、受診勧奨） |
| 在宅での薬学的管理 | 訪問服薬確認（高血圧・脂質、糖尿病、認知症） |

**情報提供**（5 シナリオ）

| シナリオ | 内容 |
|---------|------|
| 薬局での薬剤交付 | 服薬指導（高血圧、糖尿病、急性咽頭炎） |
| 病棟での服薬指導 | 入院患者指導（脳梗塞・ワーファリン、心不全、術後疼痛） |
| 一般医薬品の情報提供 | OTC 説明（かぜ薬、花粉症、胃薬） |
| 疑義照会 | 電話による医師への疑義照会（受付→医師の 2 フェーズ）＋備考欄記載 |
| 医療従事者への情報提供 | 医師へのフィードバック・処方提案（降圧薬減量、NSAIDs 変更、抗ヒスタミン変更） |

---

### 実習前練習モード

**薬局実習**（5 シナリオ）

| シナリオ | サブシナリオ |
|---------|------------|
| 高血圧の服薬指導 | ①アムロジピン新規 ②継続フォローアップ ③合剤への変更 |
| 糖尿病の服薬指導 | ①メトホルミン新規 ②SGLT2 阻害薬追加 ③低血糖対処法確認 |
| 脂質異常症の服薬指導 | ①スタチン新規（グレープフルーツ相互作用含む） ②フィブラート系 |
| 喘息・COPD の吸入指導 | ①DPI（ブデソニド・ホルモテロール配合）＋参考資料リンク ②COPD（チオトロピウム） |
| OTC 相談・受診勧奨 | ①胸痛（受診勧奨必要ケース） ②妊婦への薬相談 |

**病院実習**（4 シナリオ）

| シナリオ | サブシナリオ |
|---------|------------|
| 心不全患者の初回面談 | ①急性増悪入院・初回面談 ②退院前セルフモニタリング指導 |
| 脳梗塞患者の退院時指導 | ①DOAC（アピキサバン）新規開始・退院時指導 |
| 持参薬確認（術前） | ①整形外科術前（アスピリン・NSAIDs 休薬確認） |
| 糖尿病患者の服薬指導（インスリン導入） | ①インスリン自己注射導入・教育入院 |

---

### 初期研修モード

**複雑事例対応**（4 シナリオ）

| シナリオ | 内容 |
|---------|------|
| ポリファーマシー患者への対応 | 11 剤服用高齢者、PIMs（ゾルピデム・ベンゾ）の特定・減薬提案 |
| 薬物相互作用が疑われる処方への対応 | 相互作用特定・疑義照会 |
| 腎機能低下患者の用量確認 | eGFR に基づく投与量評価・医師報告 |
| 抗菌薬 TDM（バンコマイシン） | トラフ値・AUC/MIC 報告・用量変更提案 |

**チーム医療・処方提案**（4 シナリオ）

| シナリオ | 内容 |
|---------|------|
| 医師への処方提案（副作用対応） | 副作用報告・代替薬提案 |
| 医師への処方提案（適応外使用確認） | エビデンス提示・インフォームドコンセント確認 |
| カンファレンスでの服薬情報提供 | 多職種連携・退院後支援計画 |
| 看護師への服薬管理支援依頼 | 与薬タイミング・モニタリング指標の共有 |

---

## 評価システム

各シナリオに対応したチェックリストを元に Gemini が会話ログを解析し、JSON 形式でフィードバックを返す。

```json
{
  "scores": { "挨拶": 1, "患者氏名確認": 1, "アレルギー確認": 0 },
  "achieved": ["達成できた項目"],
  "missing": [{ "item": "不足項目", "reason": "理由" }],
  "advice": ["改善アドバイス"],
  "comment": "総合評価"
}
```

SOAP 薬歴入力がある場合は S / O / A / P それぞれの評価（0〜2 点）と総合コメントも追加出力する。

---

## 技術スタック

| カテゴリ | 使用技術 |
|----------|----------|
| フロントエンド / アプリ | Streamlit 1.41.1 |
| LLM | Google Gemini 2.5 Flash（`google-generativeai`） |
| 認証・DB | Supabase（Auth + PostgreSQL） |
| 音声合成（TTS） | gTTS 2.5.4 |
| 音声認識（STT） | Whisper（PC 限定） |
| データ処理 | pandas / numpy / matplotlib |
| PDF 生成 | reportlab |
| ホスティング | Streamlit Community Cloud |

---

## アーキテクチャ

```
ユーザー
  ↓
Streamlit UI (app.py)
  ├── 認証 (auth.py / db.py / Supabase Auth)
  ├── シナリオ選択 (sidebar.py / prompts*.py)
  ├── チャット (ui_chat.py / llm.py)
  │     └── Gemini 2.5 Flash API
  ├── 音声合成 (audio.py / gTTS)
  ├── 音声認識 (audio.py / Whisper ※PC のみ)
  └── 評価 (evaluation.py)
        └── Supabase DB (evaluations テーブル)
```

---

## ローカル起動手順

### 1. リポジトリのクローン

```bash
git clone <リポジトリURL>
cd Patient-Clinician-AI-Simulator
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. シークレットの設定

`.streamlit/secrets.toml` を作成して以下を記述：

```toml
GEMINI_API_KEY = "your_gemini_api_key"
SUPABASE_URL   = "your_supabase_url"
SUPABASE_KEY   = "your_supabase_anon_key"
```

### 4. アプリの起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開く。

---

## ファイル構成

```
Patient-Clinician-AI-Simulator/
├── app.py                   # エントリーポイント・ページ制御・自動ログアウト
├── config.py                # モデル名・定数
├── auth.py                  # ログイン・パスワードリセット
├── db.py                    # Supabase 接続・ユーザー管理
├── session.py               # セッション初期化
├── llm.py                   # Gemini API クライアント
├── prompts.py               # OSCE 対策 シナリオ・プロンプト定義
├── prompts_jisshu.py        # 実習前練習 シナリオ・プロンプト定義
├── prompts_kenshu.py        # 初期研修 シナリオ・プロンプト定義
├── evaluation.py            # 評価チェックリスト・プロンプト生成・DB 保存
├── sidebar.py               # サイドバー UI
├── tutorial.py              # チュートリアル
├── audio.py                 # 音声合成（gTTS）・音声認識（Whisper）
├── utils.py                 # 共通ユーティリティ（モバイル判定・テキスト処理）
├── ui_chat.py               # チャット画面・疑義照会備考欄フォーム
├── ui_mode_select.py        # 学習モード選択画面
├── ui_settings.py           # 設定画面
├── ui_staff_dashboard.py    # スタッフダッシュボード
├── ui_evaluation_viewer.py  # 評価結果表示
├── components/              # highlight.css 等の静的ファイル
├── fonts/                   # フォントファイル
├── images/                  # 画像ファイル
├── VERSION.txt              # バージョン情報
└── requirements.txt
```

---

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `GEMINI_API_KEY` | Google Gemini API キー |
| `SUPABASE_URL` | Supabase プロジェクト URL |
| `SUPABASE_KEY` | Supabase 匿名キー（anon key） |

Streamlit Community Cloud にデプロイする場合は App Settings > Secrets に同様の内容を設定する。

---

## ロール

| ロール | 権限 |
|--------|------|
| `student` | 会話練習・自分の評価閲覧 |
| `staff` | 上記 ＋ 全学生の評価をスタッフダッシュボードで閲覧 |

ロールは Supabase の `profiles` テーブルの `role` カラムで管理する。

---

## 技術的な工夫点

### 1. LLM プロンプト設計
患者が「聞かれたことだけ答える」「全情報を一度に話さない」という制約をプロンプトで制御し、実際の診療場面に近い会話を再現。疑義照会シナリオでは受付→医師の 2 フェーズ切り替えを単一プロンプト内で制御している。

### 2. 自動評価の構造化
評価結果を JSON で出力させることで、チェックリスト・アドバイス・SOAP 薬歴評価をそれぞれ個別にパース・表示できる設計にした。

### 3. セッション管理
Supabase の `profiles` テーブルに `last_active_at` を記録し、サーバー再起動後もセッション継続・タイムアウト判定（30 分）が可能な構成にした。DB 書き込みは 1 分に 1 回に制限してパフォーマンスを確保。

### 4. 日付テンプレート置換
シナリオ内の `{{TODAY}}` `{{TODAY+3Y}}` などを起動時の実日付に動的置換し、処方箋の使用期限や処方日をリアルに表示。

### 5. モバイル対応
CSS メディアクエリと Streamlit の `stBottom` スタイル上書きでスマートフォンでも使いやすい UI を実現。音声再生もモバイルの自動再生制限に対応したボタン方式を採用。

---

## バージョン

v1.0.0（2026-02-15 リリース）

作者: Kanta Takashima
