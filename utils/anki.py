import shutil
import os
import requests
import textwrap

def add_note_to_anki(deck_name, model_name, fields, audio_files=None, tags=None, media_folder=None, allow_duplicates=False):
    """
    Add a note to Anki with optional audio files
    
    Args:
        deck_name: Name of the Anki deck
        model_name: Name of the note type/model
        fields: Dict of field names to values
        audio_files: Dict mapping field names to audio file paths
        tags: List of tags to add to the note
        media_folder: Path to Anki's media folder
        allow_duplicates: Whether to allow duplicate notes
    """
    
    # First check if note already exists (if duplicates not allowed)
    if not allow_duplicates:
        try:
            # Search for existing notes with the same German word
            search_query = f'"deck:{deck_name}" "German:{fields.get("German", "")}"'
            search_res = requests.post("http://localhost:8765", json={
                "action": "findNotes",
                "version": 6,
                "params": {"query": search_query}
            }, timeout=10).json()
            
            if search_res.get("result") and len(search_res["result"]) > 0:
                print(f"Note for '{fields.get('German', '')}' already exists, skipping...")
                return {"result": "skipped", "reason": "duplicate"}
                
        except Exception as e:
            print(f"Warning: Could not check for duplicates: {e}")
    
    audio_list = []
    
    if audio_files and media_folder and os.path.exists(media_folder):
        for field_name, audio_path in audio_files.items():
            if audio_path and os.path.exists(audio_path):
                filename = os.path.basename(audio_path)
                dest_path = os.path.join(media_folder, filename)

                try:
                    # Copy file to Anki media folder if it doesn't exist
                    if not os.path.exists(dest_path):
                        shutil.copy2(audio_path, dest_path)

                    # Add to audio list for Anki
                    audio_list.append({
                        "filename": filename,
                        "path": dest_path,
                        "fields": [field_name]
                    })
                except Exception as e:
                    print(f"Error copying audio file {audio_path}: {e}")
            else:
                print(f"Audio file not found: {audio_path}")
    elif audio_files and not media_folder:
        print("Warning: Audio files provided but no media folder specified")

    payload = {
        "action": "addNote",
        "version": 6,
        "params": {
            "note": {
                "deckName": deck_name,
                "modelName": model_name,
                "fields": fields,
                "options": {
                    "allowDuplicate": allow_duplicates
                },
                "tags": tags or [],
                "audio": audio_list
            }
        }
    }

    try:
        res = requests.post("http://localhost:8765", json=payload, timeout=10).json()
        return res
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to AnkiConnect: {e}"}

def create_model_if_missing(model_name):
    """Create Anki note type if it doesn't exist"""
    try:
        # Check if model exists
        res = requests.post("http://localhost:8765", json={
            "action": "modelNames",
            "version": 6
        }, timeout=10).json()

        if res.get("error"):
            print(f"Error fetching model names: {res['error']}")
            return

        expected_fields = [
            "German", "English",
            "Example 1 (DE)", "Example 1 (EN)",
            "Example 2 (DE)", "Example 2 (EN)",
            "Audio Example 1", "Audio Example 2"
        ]
        
        if model_name in res.get("result", []):
            # Model exists, check if fields match
            fields_res = requests.post("http://localhost:8765", json={
                "action": "modelFieldNames",
                "version": 6,
                "params": {"modelName": model_name}
            }, timeout=10).json()

            if fields_res.get("error") is None:
                current_fields = fields_res.get("result", []) 
                if current_fields == expected_fields:
                    print(f"Note type '{model_name}' already exists with correct fields")
                    return
                else:
                    print(f"Note type '{model_name}' exists but fields differ.")
                    print(f"Expected: {expected_fields}")
                    print(f"Current: {current_fields}")
                    print("Please rename your current note type or delete it manually.")
                    return
            else:
                print(f"Error fetching fields for model '{model_name}': {fields_res.get('error')}")
                return    

        # Create the model since it doesn't exist
        templates = [
            {
                "Name": "German to English",
                "Front": "{{German}}",
                "Back": textwrap.dedent("""\
                    <b>English:</b> {{English}}<br><br>

                    <b>Beispiel 1:</b><br>
                    {{Example 1 (DE)}}<br>
                    {{#Audio Example 1}}
                    <audio controls>
                        <source src="{{Audio Example 1}}" type="audio/mpeg">
                    </audio>
                    {{/Audio Example 1}}<br>
                    <i>{{Example 1 (EN)}}</i><br><br>

                    <b>Beispiel 2:</b><br>
                    {{Example 2 (DE)}}<br>
                    {{#Audio Example 2}}
                    <audio controls>
                        <source src="{{Audio Example 2}}" type="audio/mpeg">
                    </audio>
                    {{/Audio Example 2}}<br>
                    <i>{{Example 2 (EN)}}</i><br><br>
                """),
            },
            {
                "Name": "English to German",
                "Front": "{{English}}",
                "Back": textwrap.dedent("""\
                    <b>German:</b> {{German}}<br><br>

                    <b>Beispiel 1:</b><br>
                    {{Example 1 (DE)}}<br>
                    {{#Audio Example 1}}
                    <audio controls>
                        <source src="{{Audio Example 1}}" type="audio/mpeg">
                    </audio>
                    {{/Audio Example 1}}<br>
                    <i>{{Example 1 (EN)}}</i><br><br>

                    <b>Beispiel 2:</b><br>
                    {{Example 2 (DE)}}<br>
                    {{#Audio Example 2}}
                    <audio controls>
                        <source src="{{Audio Example 2}}" type="audio/mpeg">
                    </audio>
                    {{/Audio Example 2}}<br>
                    <i>{{Example 2 (EN)}}</i><br><br>
                """),
            }
        ]
        
        css_style = """
        .card {
            font-family: arial;
            font-size: 20px;
            text-align: center;
            color: black;
            background-color: white;
        }
        
        audio {
            width: 100%;
            max-width: 300px;
            margin: 5px 0;
        }
        """

        model_payload = {
            "action": "createModel",
            "version": 6,
            "params": {
                "modelName": model_name,
                "inOrderFields": expected_fields,
                "css": css_style,  
                "cardTemplates": templates
            }
        }

        res = requests.post("http://localhost:8765", json=model_payload, timeout=10).json()
        
        if res.get("error"):
            print(f"Error creating model: {res['error']}")
        else:
            print(f"Note type '{model_name}' created successfully")
            
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to AnkiConnect: {e}")

def ensure_deck_exists(deck_name):
    """Create deck if it doesn't exist"""
    try:
        response = requests.post("http://localhost:8765", json={
            "action": "deckNames", 
            "version": 6
        }, timeout=10).json()
        
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
            create_response = requests.post("http://localhost:8765", json=create_payload, timeout=10).json()
            if create_response.get("error"):
                print(f"Error creating deck '{deck_name}': {create_response['error']}")
            else:
                print(f"Deck '{deck_name}' created successfully")
        else:
            print(f"Deck '{deck_name}' already exists")
            
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to AnkiConnect: {e}")