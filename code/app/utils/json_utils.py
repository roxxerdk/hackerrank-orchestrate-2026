import json

def strip_markdown_fences(text: str) -> str:
    """
    Strips markdown code block fences (e.g., ```json ... ```) from a text string.
    """
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
        
    return cleaned.strip()

def safe_json_load(text: str) -> dict:
    """
    Clean markdown fences and safely parse a JSON string into a Python dictionary.
    """
    cleaned_text = strip_markdown_fences(text)
    return json.loads(cleaned_text)

def safe_json_dump(data: dict, indent: int = 4) -> str:
    """
    Safely serialize a dictionary into a clean, formatted JSON string.
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)

