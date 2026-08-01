import json
from typing import Optional, Generic, TypeVar, Type, Any
from pydantic import BaseModel, ValidationError
from app.media.schemas import ImageAnalysis, VoiceAnalysis
from app.utils.json_utils import safe_json_load

T = TypeVar('T', bound=BaseModel)

class ValidationResult(BaseModel, Generic[T]):
    """
    Wrapper holding validation outcome.
    """
    success: bool
    data: Optional[T] = None
    raw_json: Optional[Any] = None
    error: Optional[str] = None

def parse_and_validate(raw_text: str, schema_class: Type[T]) -> ValidationResult[T]:
    """
    Parses a raw JSON string and validates it against the provided Pydantic schema class.
    """
    try:
        parsed_json = safe_json_load(raw_text)
        validated_data = schema_class.model_validate(parsed_json)
        return ValidationResult(success=True, data=validated_data, raw_json=parsed_json)
    except json.JSONDecodeError as e:
        return ValidationResult(success=False, error=f"JSON Decode Error: {e}")
    except ValidationError as e:
        return ValidationResult(success=False, error=f"Schema Validation Error: {e}")
    except Exception as e:
        return ValidationResult(success=False, error=f"Unexpected Validation Error: {e}")

def parse_image_analysis(raw_text: str) -> ValidationResult[ImageAnalysis]:
    """
    Parses a raw JSON string into an ImageAnalysis Pydantic model.
    """
    return parse_and_validate(raw_text, ImageAnalysis)

def parse_voice_analysis(raw_text: str) -> ValidationResult[VoiceAnalysis]:
    """
    Parses a raw JSON string into a VoiceAnalysis Pydantic model.
    """
    return parse_and_validate(raw_text, VoiceAnalysis)

