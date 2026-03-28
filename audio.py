#audio.py
import io
import base64
from gtts import gTTS
import streamlit.components.v1 as components

# ==========================================
# TTS（テキスト→音声）
# ==========================================
def speak_text(text):

    tts = gTTS(
        text=text,
        lang="ja"
    )

    mp3_fp = io.BytesIO()

    tts.write_to_fp(mp3_fp)

    mp3_fp.seek(0)

    return mp3_fp


# ==========================================
# 音声再生（スマホ完全対応版）
# ==========================================
def play_audio(
    audio_bytes,
    autoplay=True,
    speed="ふつう"
):

    # read()ではなくgetvalue()を使用（重要）
    audio_base64 = base64.b64encode(
        audio_bytes.getvalue()
    ).decode()

    playback_rate = 1.0

    if speed == "ゆっくり":
        playback_rate = 0.85

    elif speed == "はやい":
        playback_rate = 1.5

    autoplay_attr = "autoplay" if autoplay else ""

    audio_html = f"""
        <audio id="audio_player" {autoplay_attr} controls>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>

        <script>
            var audio = document.getElementById("audio_player");

            if (audio) {{
                audio.playbackRate = {playback_rate};
            }}
        </script>
    """

    components.html(
        audio_html,
        height=70
    )

