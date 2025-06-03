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
            # Search for existing notes with the same word
            search_query = f'"deck:{deck_name}" "Word:{fields.get("Word", "")}"'
            search_res = requests.post("http://localhost:8765", json={
                "action": "findNotes",
                "version": 6,
                "params": {"query": search_query}
            }, timeout=10).json()
            
            if search_res.get("result") and len(search_res["result"]) > 0:
                print(f"Note for '{fields.get('Word', '')}' already exists, skipping...")
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
            "Word", "Meaning",
            "Example_1", "Translation_1",
            "Example_2", "Translation_2",
            "Audio_Word", "Audio_Example_1",
            "Audio_Example_2"
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
                "Name": "Target to Native",
                "Front": "{{Word}}{{Audio_Word}}",
                "Back": textwrap.dedent("""\
                    {{Meaning}}
                                        
                    <hr id=answer>

                    {{Example_1}}{{Audio_Example_1}} 
                    <button onclick="this.nextElementSibling.style.display='block'; this.style.display='none';">
                        Show Translation
                    </button>
                    <div style="display:none;">
                        <i>{{Translation_1}}</i>
                    </div><br><br>

                    {{Example_2}}{{Audio_Example_2}}
                    <button onclick="this.nextElementSibling.style.display='block'; this.style.display='none';">
                        Show Translation
                    </button>
                    <div style="display:none;">
                        <i>{{Translation_2}}</i>
                    </div><br><br>
                """),
            },
            {
                "Name": "Native to Target",
                "Front": "{{Meaning}}",
                "Back": textwrap.dedent("""\
                    {{Word}}{{Audio_Word}}
                                        
                    <hr id=answer>

                    {{Example_1}}{{Audio_Example_1}} 
                    <button onclick="this.nextElementSibling.style.display='block'; this.style.display='none';">
                        Show Translation
                    </button>
                    <div style="display:none;">
                        <i>{{Translation_1}}</i>
                    </div><br><br>

                    {{Example_2}}{{Audio_Example_2}}
                    <button onclick="this.nextElementSibling.style.display='block'; this.style.display='none';">
                        Show Translation
                    </button>
                    <div style="display:none;">
                        <i>{{Translation_2}}</i>
                    </div><br><br>
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