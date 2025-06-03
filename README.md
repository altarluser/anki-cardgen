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
    - Download the model to your local machine. 
    - Start the LMStudio API Server
        - You can start the server from the Developer tab. It runs on 'http://127.0.0.1:1234'
        - You do not need API keys since LMStudio runs locally.

## Usage
Prepare a plain text file containing German words or phrases, one per line. (an example is provided as words.txt)
Run the main script with options to generate cards and optionally push them to Anki:

    ```bash
    # Generate cards and push to Anki with audio
    python main.py --deck "German Vocabulary" --push-to-anki --audio

    # Generate cards only (only CSV output, no Anki push)
    python main.py --deck "German Vocabulary"

    # Use custom word list and template
    python main.py --words "my_words.txt" --template "my_template.template" --deck "Advanced German"

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--deck` | `test` | Name of your Anki deck (created automatically if missing) |
| `--words` | `words.txt` | Path to the file containing German words or phrases |
| `--template` | `prompt.template` | Path to your LLM prompt template file |
| `--push-to-anki` | `False` | Automatically add generated cards to your Anki deck |
| `--audio` | `False` | Generate TTS audio files for example sentences |
| `--audio-folder` | `audio` | Local folder to store generated audio files |
| `--anki-media-folder` | Auto-detected | Path to Anki's media folder (usually auto-detected) |