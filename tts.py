from gtts import gTTS
from pathlib import Path

def generate_audio(text: str, filename_base: str, lang: str = "de") -> str:
    filename = f"{filename_base}.mp3"
    audio_path = Path("audio") / filename
    audio_path.parent.mkdir(exist_ok=True)
    tts = gTTS(text=text, lang=lang)
    tts.save(audio_path)
    return str(audio_path)
