# ============================
# アプリ共通設定
# ============================

import os
import subprocess
from datetime import datetime, timedelta, timezone

# LLM
MODEL_NAME = "gemini-2.5-flash"


# ============================
# バージョン情報
#   デプロイした変更が本番へ反映されているかを画面上で判定するために使う。
#   BOOT_TIME はモジュール読み込み時＝プロセス起動時に確定するため、
#   「いつ取り込まれたコードが動いているか」をそのまま表す。
# ============================
APP_VERSION = "1.0"

_JST = timezone(timedelta(hours=9))
BOOT_TIME = datetime.now(_JST)

_ROOT = os.path.dirname(os.path.abspath(__file__))


def _sha_from_git_dir() -> str:
    """.git を直接読んでコミットIDを取得する（subprocess不要）"""
    git_dir = os.path.join(_ROOT, ".git")
    with open(os.path.join(git_dir, "HEAD"), encoding="utf-8") as f:
        head = f.read().strip()

    # detached HEAD の場合は HEAD にSHAが直接書かれている
    if not head.startswith("ref:"):
        return head

    ref_name = head[4:].strip()

    ref_path = os.path.join(git_dir, *ref_name.split("/"))
    if os.path.exists(ref_path):
        with open(ref_path, encoding="utf-8") as f:
            return f.read().strip()

    # ルーズなrefが無い場合は packed-refs を探す
    packed = os.path.join(git_dir, "packed-refs")
    if os.path.exists(packed):
        with open(packed, encoding="utf-8") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) == 2 and parts[1] == ref_name:
                    return parts[0]

    return ""


def _sha_from_git_command() -> str:
    """git コマンドでコミットIDを取得する（.git を読めなかった場合の代替）"""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        timeout=3,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _detect_git_sha() -> str:
    """実行中コードのコミットIDを短縮形で返す。取得できなければ空文字。"""
    for getter in (_sha_from_git_dir, _sha_from_git_command):
        try:
            sha = getter()
            if sha:
                return sha[:7]
        except Exception:
            # .git が無い環境でも起動を妨げない
            continue
    return ""


GIT_SHA = _detect_git_sha()


def version_label() -> str:
    """サイドバーに表示するバージョン文字列を組み立てる"""
    parts = [f"Version {APP_VERSION}"]
    if GIT_SHA:
        parts.append(GIT_SHA)
    parts.append(f"起動 {BOOT_TIME.strftime('%m/%d %H:%M')}")
    return " ・ ".join(parts)
