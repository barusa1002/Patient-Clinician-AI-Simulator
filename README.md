# 患者・医療従事者役 AI シミュレーター

薬学生向けのコミュニケーション実習支援ツール。AIが患者・医師・薬剤師などの役を演じ、テキスト・音声で会話練習ができる。会話終了後にAIによる自動フィードバックを取得できる。

**本番URL**: https://patient-clinician-ai-simulator-showa-pharmaceutical-university.streamlit.app/

---

## 主な機能

| 機能 | 説明 |
|------|------|
| 会話シミュレーション | AI（Gemini 2.5 Flash）が患者・医師役を担い、リアルな会話練習 |
| 音声読み上げ | gTTSによるAI発話の音声合成 |
| 自動評価 | 会話終了後にAIが評価・フィードバックを生成 |
| 処方箋備考欄フォーム | 疑義照会シナリオ完了後に専用フォームを自動表示 |
| スタッフダッシュボード | 教員・指導者が全学生の評価結果を一覧確認 |
| 自動ログアウト | 30分無操作でセッション終了（Supabase DBと連携） |
| チュートリアル | 初回ログイン時にアプリの使い方をガイド |

---

## 学習モード

| モード | 対象 | 内容 |
|--------|------|------|
| OSCE対策 | 薬学4〜6年生 | 客観的臨床能力試験の模擬練習 |
| 実習前練習 | 薬学5年生 | 実務実習前の基礎コミュニケーション練習 |
| 初期研修 | 薬剤師研修生 | 研修期間中の実践的な対応練習 |

---

## シナリオ一覧（OSCE対策）

**患者・来局者応対**
- 薬局での患者応対
- 病棟での初回面談
- 来局者応対
- 在宅での薬学的管理

**情報提供**
- 薬局での薬剤交付
- 病棟での服薬指導
- 一般医薬品の情報提供
- 疑義照会
- 医療従事者への情報提供

---

## 技術スタック

| カテゴリ | 使用技術 |
|----------|----------|
| フロントエンド | Streamlit 1.41.1 |
| LLM | Google Gemini 2.5 Flash（`google-generativeai`） |
| 認証・DB | Supabase（Auth + PostgreSQL） |
| 音声合成 | gTTS 2.5.4 |
| ホスティング | Streamlit Community Cloud |

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
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_anon_key"
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
├── app.py                   # エントリーポイント・ページ制御
├── config.py                # 定数・設定値
├── auth.py                  # 認証（ログイン・パスワードリセット）
├── db.py                    # Supabase接続・ユーザー管理
├── session.py               # セッション初期化
├── llm.py                   # Gemini APIクライアント
├── prompts.py               # OSCE対策 シナリオ・プロンプト定義
├── prompts_jisshu.py        # 実習前練習 シナリオ・プロンプト定義
├── prompts_kenshu.py        # 初期研修 シナリオ・プロンプト定義
├── evaluation.py            # 評価プロンプト生成・Supabase保存
├── sidebar.py               # サイドバーUI
├── tutorial.py              # チュートリアル
├── audio.py                 # 音声合成・再生
├── utils.py                 # 共通ユーティリティ
├── ui_chat.py               # チャット画面
├── ui_mode_select.py        # 学習モード選択画面
├── ui_settings.py           # 設定画面
├── ui_staff_dashboard.py    # スタッフダッシュボード
├── ui_evaluation_viewer.py  # 評価結果表示
├── components/              # CSS等の静的ファイル
└── requirements.txt
```

---

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `GEMINI_API_KEY` | Google Gemini APIキー |
| `SUPABASE_URL` | SupabaseプロジェクトURL |
| `SUPABASE_KEY` | Supabase匿名キー（anon key） |

Streamlit Community Cloud にデプロイする場合は App Settings > Secrets に同様の内容を設定する。

---

## ロール

| ロール | 権限 |
|--------|------|
| `student` | 会話練習・評価閲覧 |
| `staff` | 上記 + 全学生の評価をスタッフダッシュボードで閲覧 |

ロールは Supabase の `profiles` テーブルの `role` カラムで管理する。

---

## バージョン

v1.0.0（2026-02-15リリース）

作成者: Kanta Takashima
