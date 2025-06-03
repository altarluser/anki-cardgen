import os
import csv
from openai import OpenAI

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

def read_words(filename: str) -> list[str]:
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def read_prompt_template(filename: str) -> str:
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()

def response_lmstudio(
    word: str,
    prompt: str,
    model: str="lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/Meta-Llama-3.1-8B-Instruct-Q8_0.gguf"
) -> str:
    """Get the response from the lmstudio backend."""
    
    system_prompt = """You are a German language tutor creating Anki flashcards. You must respond ONLY in the exact format requested with NO extra text, explanations, or additional content."""
    
    user_prompt = prompt.format(word)
    
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=400,
        stop=[
            "\n\nGerman:",      # Exactly what the model generates
            "\nGerman:",        # Alternative without double newline
            "\n\nWord:",        # Other potential continuations
            "\nNext word:",
            "\n\n---",
            "---"
        ],
        top_p=0.9,
        frequency_penalty=0.1,
    ).choices[0].message.content
    
    return response.strip()

def parse_response(text: str) -> dict:
    """Parse the LM output into a dictionary with keys:
    German, English, Example 1 (DE), Example 1 (EN), Example 2 (DE), Example 2 (EN)
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    data = {
        "German": "",
        "English": "",
        "Example 1 (DE)": "",
        "Example 1 (EN)": "",
        "Example 2 (DE)": "",
        "Example 2 (EN)": "",
    }
    for line in lines:
        for key in data.keys():
            prefix = key + ":"
            if line.startswith(prefix):
                data[key] = line[len(prefix):].strip()
                break
    return data

def write_csv(filename: str, rows: list[dict]):
    #fieldnames = ["Word", "Meaning", "Example_1", "Translation_1", "Example_2", "Translation_2"]
    fieldnames = ["German", "English", "Example 1 (DE)", "Example 1 (EN)", "Example 2 (DE)", "Example 2 (EN)"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)