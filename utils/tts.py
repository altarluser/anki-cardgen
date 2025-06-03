from gtts import gTTS
from pathlib import Path

def generate_audio(text: str, filename_base: str, audio_folder: str = "audio", lang: str = "de") -> str:
    """
    Generate TTS audio file and return the full path
    
    Args:
        text: Text to convert to speech
        filename_base: Base filename without extension
        audio_folder: Folder to save audio files
        lang: Language code for TTS
    
    Returns:
        Full path to the generated audio file
    """
    filename = f"{filename_base}.mp3"
    audio_path = Path(audio_folder) / filename
    
    # Create directory if it doesn't exist
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(str(audio_path))
        return str(audio_path.resolve())  # Return absolute path
    except Exception as e:
        print(f"Error generating audio for '{text}': {e}")
        return None