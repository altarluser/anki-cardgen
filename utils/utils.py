import csv
import ast
import json
from openai import OpenAI

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