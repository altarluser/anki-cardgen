from datetime import datetime
from tqdm import tqdm
import argparse

from utils.utils import read_words, read_prompt_template, response_lmstudio, parse_response, write_csv
from utils.anki import add_note_to_anki, create_model_if_missing, ensure_deck_exists
from utils.tts import generate_audio

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck", default="test", help="Name of your deck on Anki")
    parser.add_argument("--words", default="words.txt", help="Words list.txt")
    parser.add_argument("--template", default="prompt.template", help="LLM prompt for generating cards")
    parser.add_argument("--push-to-anki", action="store_true", help="Push the generated cards to your deck automatically")
    parser.add_argument("--audio", action="store_true", help="Generate TTS files")
    parser.add_argument("--audio-folder", default="audio", help="Folder path for audio files")
    args = parser.parse_args()
    
    words = read_words(args.words)
    prompt_template = read_prompt_template(args.template)
    results = []

    if args.push_to_anki:
        ensure_deck_exists(args.deck)
        create_model_if_missing("German")

    for word in tqdm(words, desc="Generating cards"):
        while True:
            response_text = response_lmstudio(word, prompt_template)
            parsed = parse_response(response_text)
            
            # Check that required fields are non-empty
            required_keys = ["German", "English", "Example 1 (DE)", "Example 1 (EN)", "Example 2 (DE)", "Example 2 (EN)"]
            if all(parsed[k] for k in required_keys):
                break
            print(f"Invalid output format for word '{word}', retrying...")
        
        audio_files = None
        if args.audio and args.audio_folder:
            audio_files = {}
            for idx in [1, 2]:
                key = f"Example {idx} (DE)"
                filename_base = f"{parsed['German'].replace(' ', '_')}_ex{idx}"
                audio_path = generate_audio(parsed[key], filename_base)
                audio_files[f"Audio Example {idx}"] = audio_path

        if args.push_to_anki:
            # Fields dictionary must include all fields used in your Anki model
            fields = {
                "German": parsed["German"],
                "English": parsed["English"],
                "Definition": parsed.get("Definition", ""),
                "Example 1 (DE)": parsed.get("Example 1 (DE)", ""),
                "Example 1 (EN)": parsed.get("Example 1 (EN)", ""),
                "Example 2 (DE)": parsed.get("Example 2 (DE)", ""),
                "Example 2 (EN)": parsed.get("Example 2 (EN)", ""),
            }

            res = add_note_to_anki(
                deck_name=args.deck,
                fields=fields,
                audio_files=audio_files,
                tags=["auto"],
                media_folder=args.audio_folder
            )

            if res.get("error"):
                print(f"Failed to add note: {res['error']}")

        results.append(parsed)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")   
    output_filename = f"anki_cards_{timestamp}.csv"
    write_csv(output_filename, results)
    print(f"CSV file '{output_filename}' has been created.")

if __name__ == "__main__":
    main()
