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

from datetime import datetime, timezone

def safe_json_dump(data: dict, indent: int = 4) -> str:
    """
    Safely serialize a dictionary into a clean, formatted JSON string.
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)

def utc_now_iso() -> str:
    """
    Returns current time in UTC formatted as an ISO-8601 string (with 'Z' suffix).
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


