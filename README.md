# Anki-Cardgen: Vocabulary Flashcards Generator for Anki

Easily create vocabulary flashcards for Anki using a large language model (LLM) and optional text-to-speech (TTS) audio. This tool automatically manages deck creation and can push cards directly to your Anki deck, helping you focus on studying instead of repetitive card creation.

For now it only works for German because of strict Anki format-setup. Next update will allow flexibility

## Features

- Generate flashcards from a list of words or idioms  
- Uses customizable prompts to get precise flashcard content
- Optionally generate audio examples via TTS for better pronunciation practice
- Automatically create Anki decks and deck format if they don’t exist  
- Push generated cards directly to Anki via AnkiConnect  
- Outputs results as CSV for manual review or import manually  

## Requirements

- Anki with [AnkiConnect](https://ankiweb.net/shared/info/2055492159) installed and running  
- Establishing a local API (i.e. via LMStudio easily)

## Installation

1. Clone this repository:  
   ```bash
   git clone https://github.com/yourusername/anki-cardgen.git
   cd anki-cardgen

2. (Optional) Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. Install the required Python packages:
    ```bash
    pip install -r requirements.txt

4. Make sure Anki is installed and AnkiConnect add-on is enabled and running.

5. Set up a local API.
    - Download & Launch LMStudio and open the **Model Hub**.  
    - Search for the model named: `lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF`  
        - You can choose any versions, Q8 works fine.      
    - Download the model to your local machine. 
    - Start the LMStudio API Server
        - You can start the server from the Developer tab. It runs on 'http://127.0.0.1:1234'
        - You do not need API keys since LMStudio runs locally.

## Usage

You can provide words or phrases in two ways:

### Method 1: Direct Word Input
Provide words directly as command line arguments using `--words` or `--w`:
```bash
# Single word
python main.py --words Hund --deck "German Vocabulary"
python main.py --w Hund --d "German Vocabulary"

# Multiple words
python main.py --words Hund Katze Vogel --deck "German Vocabulary"

# Words with spaces (idioms/phrases) - use quotes
python main.py --words "das Haus" "auf Deutsch" "guten Morgen"

# Mix of single words and phrases
python main.py --words Hund "das Auto" Katze "zum Beispiel"
```

### Method 2: Text File Input
Prepare a plain text file containing German words or phrases, one per line (an example is provided as words.txt):
```bash
# Using file input
python main.py --vocab words.txt --deck "German Vocabulary"
python main.py --v words.txt --d "German Vocabulary"
```

### Common Usage Examples
```bash
# Default behavior: Generate cards with audio and push to Anki
python main.py --words Hund Katze Vogel --deck "German Vocabulary"
python main.py --w Hund Katze Vogel --d "German Vocabulary"

# Generate cards but don't push to Anki (CSV output only)
python main.py --words Hund Katze --no-anki

# Generate cards without audio files
python main.py --words Hund Katze --no-audio

# Generate only CSV (no Anki, no audio)
python main.py --words Hund Katze --no-anki --no-audio

# Use custom template
python main.py --words Hund Katze --template "my_template.template"
```

### Important Notes for Word Input
- **Single words**: Just list them separated by spaces: `--words Hund Katze Vogel`
- **Phrases/idioms with spaces**: Wrap each phrase in quotes: `--words "das Haus" "guten Morgen"`
- **File format**: When using `--vocab`, put one word/phrase per line in the text file

### Command Line Options
| Option | Default | Description |
|--------|---------|-------------|
| `--words`, `--w` | - | German words or phrases (space-separated, use quotes for phrases) |
| `--vocab`, `--v` | - | Path to file containing German words or phrases (one per line) |
| `--deck`, `--d` | `test` | Name of your Anki deck (created automatically if missing) |
| `--template` | `prompt.template` | Path to your LLM prompt template file |
| `--no-anki` | `False` | Don't push cards to Anki (default: cards are pushed) |
| `--no-audio` | `False` | Don't generate TTS audio files (default: audio is generated) |
| `--audio-folder` | `audio` | Local folder to store generated audio files |
| `--anki-media-folder` | Auto-detected | Path to Anki's media folder (usually auto-detected) |
| `--model` | `meta-llama-3.1-8b-instruct` | Path or identifier for LMStudio quantized model |