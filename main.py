from datetime import datetime
from tqdm import tqdm
import argparse
import os
from utils.utils import read_words, read_prompt_template, response_lmstudio, parse_response, write_csv
from utils.anki import add_note_to_anki, create_model_if_missing, ensure_deck_exists
from utils.tts import generate_audio

def get_anki_media_folder():
    """Get the Anki media folder path by scanning for available profiles"""
    import platform
    
    if platform.system() == "Windows":
        base_path = os.path.expanduser("~/AppData/Roaming/Anki2")
    elif platform.system() == "Darwin":  # macOS
        base_path = os.path.expanduser("~/Library/Application Support/Anki2")
    else:  # Linux
        base_path = os.path.expanduser("~/.local/share/Anki2")
    
    if not os.path.exists(base_path):
        print(f"Anki folder not found at: {base_path}")
        return None
    
    # Scan for all profile folders
    try:
        profile_folders = [d for d in os.listdir(base_path) 
                          if os.path.isdir(os.path.join(base_path, d))]
        
        if not profile_folders:
            print(f"No profile folders found in: {base_path}")
            return None
        
        # Look for media folders in each profile
        available_profiles = []
        for profile in profile_folders:
            media_path = os.path.join(base_path, profile, "collection.media")
            if os.path.exists(media_path):
                available_profiles.append((profile, media_path))
        
        if not available_profiles:
            print(f"No collection.media folders found in profiles: {profile_folders}")
            return None
        
        # If multiple profiles exist, prefer "User 1" or take the first one
        for profile_name, media_path in available_profiles:
            if profile_name == "User 1":
                print(f"Using Anki profile: {profile_name}")
                return media_path
        
        # If "User 1" not found, use the first available profile
        profile_name, media_path = available_profiles[0]
        if len(available_profiles) > 1:
            print(f"Multiple Anki profiles found: {[p[0] for p in available_profiles]}")
            print(f"Using profile: {profile_name}")
        else:
            print(f"Using Anki profile: {profile_name}")
        
        return media_path
        
    except PermissionError:
        print(f"Permission denied accessing: {base_path}")
        return None
    except Exception as e:
        print(f"Error scanning Anki profiles: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", default="test", help="Name of your deck on Anki")
    parser.add_argument("--words", default="words.txt", help="Words list.txt")
    parser.add_argument("--template", default="prompt.template", help="LLM prompt for generating cards")
    parser.add_argument("--push-to-anki", action="store_true", help="Push the generated cards to your deck automatically")
    parser.add_argument("--audio", action="store_true", help="Generate TTS files")
    parser.add_argument("--audio-folder", default="audio", help="Folder path for audio files")
    parser.add_argument("--anki-media-folder", help="Path to Anki media folder (auto-detected if not provided)")
    args = parser.parse_args()

    words = read_words(args.words)
    prompt_template = read_prompt_template(args.template)
    results = []

    # Get Anki media folder
    anki_media_folder = None
    if args.push_to_anki and args.audio:
        if args.anki_media_folder:
            anki_media_folder = args.anki_media_folder
        else:
            anki_media_folder = get_anki_media_folder()
            
        if not anki_media_folder or not os.path.exists(anki_media_folder):
            print("Warning: Could not find Anki media folder. Audio files will not be copied to Anki.")
            print("Please specify --anki-media-folder manually or ensure Anki is installed.")
            anki_media_folder = None

    if args.push_to_anki:
        ensure_deck_exists(args.deck)
        create_model_if_missing("AnkiCardGen")

    for word in tqdm(words, desc="Generating cards"):
        while True:
            response_text = response_lmstudio(word, prompt_template)
            parsed = parse_response(response_text)
            
            # Check that required fields are non-empty
            required_keys = ["German", "English", "Example 1 (DE)", "Example 1 (EN)", "Example 2 (DE)", "Example 2 (EN)"]
            if all(parsed.get(k) for k in required_keys):
                break
            print(f"Invalid output format for word '{word}', retrying...")

        audio_files = None
        if args.audio and args.audio_folder:
            audio_files = {}
            for idx in [1, 2]:
                key = f"Example {idx} (DE)"
                # Clean filename - remove special characters
                clean_german = parsed['German'].replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
                filename_base = f"{clean_german}_ex{idx}"
                audio_path = generate_audio(parsed[key], filename_base, args.audio_folder)
                audio_files[f"Audio Example {idx}"] = audio_path

        if args.push_to_anki:
            # Fields dictionary must include all fields used in your Anki model
            fields = {
                "German": parsed["German"],
                "English": parsed["English"],
                "Example 1 (DE)": parsed.get("Example 1 (DE)", ""),
                "Example 1 (EN)": parsed.get("Example 1 (EN)", ""),
                "Example 2 (DE)": parsed.get("Example 2 (DE)", ""),
                "Example 2 (EN)": parsed.get("Example 2 (EN)", ""),
                "Audio Example 1": "",  # These will be filled by Anki
                "Audio Example 2": ""
            }

            res = add_note_to_anki(
                deck_name=args.deck,
                model_name="AnkiCardGen",
                fields=fields,
                audio_files=audio_files,
                tags=["auto"],
                media_folder=anki_media_folder  # Pass the actual Anki media folder
            )
            
            if res.get("error"):
                print(f"Failed to add note: {res['error']}")
            else:
                print(f"Successfully added note for: {parsed['German']}")

        results.append(parsed)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_filename = f"anki_cards_{timestamp}.csv"
    write_csv(output_filename, results)
    print(f"CSV file '{output_filename}' has been created.")

if __name__ == "__main__":
    main()