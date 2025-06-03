import shutil
import os
import requests

def add_note_to_anki(deck_name, fields, audio_files=None, tags=None, media_folder=None):
    """
    fields: dict, örn:
      {
        "German": "...",
        "English": "...",
        "Definition": "...",
        "Example 1 (DE)": "...",
        "Example 1 (EN)": "...",
        "Example 2 (DE)": "...",
        "Example 2 (EN)": "..."
      }
    audio_files: dict, örn:
      {
        "Audio Example 1": "/path/to/example1.mp3",
        "Audio Example 2": "/path/to/example2.mp3"
      }
    media_folder: Anki media klasörünün tam path'i, örn:
      "/home/user/.local/share/Anki2/User 1/collection.media"
    """

    audio_list = []
    if audio_files and media_folder:
        for field_name, audio_path in audio_files.items():
            filename = os.path.basename(audio_path)
            dest_path = os.path.join(media_folder, filename)

            if not os.path.exists(dest_path):
                shutil.copy(audio_path, dest_path)

            audio_list.append({
                "filename": filename,
                "path": dest_path,
                "fields": [field_name]
            })

    payload = {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": {
                "deckName": deck_name,
                "modelName": "German",
                "fields": fields,
                "options": {
                    "allowDuplicate": False
                },
                "tags": tags or [],
                "audio": audio_list
            }
        }
    }

    res = requests.post("http://localhost:8765", json=payload).json()
    return res

def create_model_if_missing(model_name):
    # check if model exists
    res = requests.post("http://localhost:8765", json={
        "action": "modelNames",
        "version": 6
    }).json()

    if model_name in res["result"]:
        return

    # model does not exist, create it
    fields = ["German", "English", "Definition", "Example 1 (DE)", "Example 1 (EN)", "Example 2 (DE)", "Example 2 (EN)", "Audio Example 1", "Audio Example 2"]

    templates = [{
        "Name": "Card 1",
        "Front": "<b>German:</b> {{German}}<br><br><b>English:</b> {{English}}",
        "Back": """
        <b>English:</b> {{English}}<br>

        <b>Beispiel 1:</b><br>
        {{Example 1 (DE)}}<br>
        <audio controls>
        <source src="{{Audio Example 1}}" type="audio/mpeg">
        </audio>
        <i>{{Example 1 (EN)}}</i><br><br>

        <b>Beispiel 2:</b><br>
        {{Example 2 (DE)}}<br>
        <audio controls>
        <source src="{{Audio Example 2}}" type="audio/mpeg">
        </audio>
        <i>{{Example 2 (EN)}}</i><br><br>
                """
                }]

    model_payload = {
        "action": "createModel",
        "version": 6,
        "params": {
            "modelName": model_name,
            "inOrderFields": fields,
            "css": "",  # opsiyonel: stil eklenebilir
            "cardTemplates": templates
        }
    }

    res = requests.post("http://localhost:8765", json=model_payload).json()
    print("Deck format was created:", res)

def ensure_deck_exists(deck_name):
    response = requests.post("http://localhost:8765", json={"action": "deckNames", "version": 6}).json()
    if response.get("error"):
        print(f"Error fetching decks: {response['error']}")
        return
    decks = response.get("result", [])
    if deck_name not in decks:
        # Create deck if missing
        create_payload = {
            "action": "createDeck",
            "version": 6,
            "params": {"deck": deck_name}
        }
        create_response = requests.post("http://localhost:8765", json=create_payload).json()
        if create_response.get("error"):
            print(f"Error creating deck '{deck_name}': {create_response['error']}")
        else:
            print(f"Deck '{deck_name}' created.")