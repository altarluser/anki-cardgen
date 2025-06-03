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
) -> dict | str:
    """Get the response from the lmstudio backend.
    """
    
    prompt = prompt.format(word)
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=512,
    ).choices[0].message.content

    try:
        response = ast.literal_eval(response)
    except Exception:
        response = str(response)
    return response

def parse_response(text: str) -> dict | None:
    try:
        data = json.loads(text)
        keys = ["German", "English", "Example 1 (DE)", "Example 1 (EN)", "Example 2 (DE)", "Example 2 (EN)"]
        if all(k in data for k in keys):
            return {k: data[k] for k in keys}
    except json.JSONDecodeError:
        return None

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
    fieldnames = ["German", "English", "Example 1 (DE)", "Example 1 (EN)", "Example 2 (DE)", "Example 2 (EN)"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)