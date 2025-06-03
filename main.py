from datetime import datetime
from tqdm import tqdm
import argparse
import os

from utils.utils import get_anki_media_folder, read_words, read_prompt_template, response_lmstudio, parse_response, write_csv
from utils.anki import add_note_to_anki, create_model_if_missing, ensure_deck_exists
from utils.tts import generate_audio

def get_words_from_args(words_args, vocab_file):
    """Get words from either command line arguments or file"""
    if words_args:
        print(f"Processing {len(words_args)} words from arguments: {', '.join(words_args)}")
        return words_args
    elif vocab_file and os.path.exists(vocab_file):
        words = read_words(vocab_file)
        print(f"Processing {len(words)} words from file: {vocab_file}")
        return words
    else:
        raise ValueError("Either provide --words or use --vocab")

def main():
    parser = argparse.ArgumentParser(description="Generate Anki cards from words")
    parser.add_argument("--deck", "-d", default="test", help="Name of your deck on Anki")

    # Word input options - mutually exclusive group
    word_group = parser.add_mutually_exclusive_group(required=True)
    word_group.add_argument("--words", "-w", nargs="+", help="Words to generate cards for")
    word_group.add_argument("--vocab", "-v", help="Path to vocabulary file")

    parser.add_argument("--template", default="prompt.template", help="LLM prompt for generating cards")
    parser.add_argument("--no-anki", action="store_true", help="Don't push the generated cards to Anki (default: cards are pushed)")
    parser.add_argument("--no-audio", action="store_true", help="Don't generate TTS files (default: audio is generated)")
    parser.add_argument("--audio-folder", default="audio", help="Folder path for audio files")
    parser.add_argument("--anki-media-folder", help="Path to Anki media folder (auto-detected if not provided)")
    parser.add_argument("--model", default="meta-llama-3.1-8b-instruct", help="Path or identifier for LMStudio model")
    args = parser.parse_args()

    # Get words from arguments or file
    try:
        words = get_words_from_args(args.words, args.vocab)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    push_to_anki = not args.no_anki
    generate_tts = not args.no_audio
    prompt_template = read_prompt_template(args.template)

    results = []

    # Get Anki media folder
    anki_media_folder = None
    if push_to_anki and generate_tts:
        if args.anki_media_folder:
            anki_media_folder = args.anki_media_folder
        else:
            anki_media_folder = get_anki_media_folder()
            
        if not anki_media_folder or not os.path.exists(anki_media_folder):
            print("Warning: Could not find Anki media folder. Audio files will not be copied to Anki.")
            print("Please specify --anki-media-folder manually or ensure Anki is installed.")
            anki_media_folder = None

    if push_to_anki:
        ensure_deck_exists(args.deck)
        create_model_if_missing("AnkiCardGen")

    for word in tqdm(words, desc="Generating cards"):
        while True:
            response_text = response_lmstudio(word, prompt_template, model=args.model)
            parsed = parse_response(response_text)
            
            # Check that required fields are non-empty
            #required_keys = ["Word", "Meaning", "Example_1", "Translation_1", "Example_2", "Translation_2"]
            required_keys = ["German", "English", "Example 1 (DE)", "Example 1 (EN)", "Example 2 (DE)", "Example 2 (EN)"]
            if all(parsed.get(k) for k in required_keys):
                break
            print(f"Invalid output format for word '{word}', retrying...")

        audio_files = None
        if generate_tts and args.audio_folder:
            audio_files = {}

            # Clean filename - remove special characters    
            clean_word = parsed['German'].replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
            # Generate audio for the main word
            word_for_pronunciation = parsed['German'].split('(')[0].strip() # Clean word for pronunciation - remove parenthetical parts
            word_audio_path = generate_audio(word_for_pronunciation, clean_word, args.audio_folder)
            audio_files["Audio_Word"] = word_audio_path

            # Generate audio for the examples
            for idx in [1, 2]:
                key = f"Example {idx} (DE)"
                filename_base = f"{clean_word}_ex{idx}"
                audio_path = generate_audio(parsed[key], filename_base, args.audio_folder)
                audio_files[f"Audio_Example_{idx}"] = audio_path

        if push_to_anki:
            # Fields dictionary must include all fields used in your Anki model
            fields = {
                "Word": parsed["German"],
                "Meaning": parsed["English"],
                "Example_1": parsed.get("Example 1 (DE)", ""),
                "Translation_1": parsed.get("Example 1 (EN)", ""),
                "Example_2": parsed.get("Example 2 (DE)", ""),
                "Translation_2": parsed.get("Example 2 (EN)", ""),
                "Audio_Word": "", # These will be filled by Anki
                "Audio_Example_1": "",  
                "Audio_Example_2": ""
            }

            res = add_note_to_anki(
                deck_name=args.deck,
                model_name="AnkiCardGen",
                fields=fields,
                audio_files=audio_files,
                tags=["auto"],
                media_folder=anki_media_folder 
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