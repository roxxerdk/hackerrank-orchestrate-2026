import time
import logging
from pathlib import Path
from typing import Any, Type, TypeVar
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import (
    ROOT_DIR,
    IMAGE_MODEL,
    VOICE_MODEL,
    TEMPERATURE,
    TOP_P,
    TOP_K,
    IMAGE_PROMPT_VERSION,
    VOICE_PROMPT_VERSION,
    MAX_RETRIES,
)
from app.media.media_loader import MediaInfo, MediaType
from app.media.schemas import ImageAnalysis, VoiceAnalysis
from app.media.schema_validator import parse_image_analysis, parse_voice_analysis

# Setup logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("media_analyzer")

T = TypeVar('T', bound=BaseModel)

def _load_prompt(filename: str) -> str:
    """
    Loads prompt templates from the prompts directory.
    """
    prompt_path = ROOT_DIR / "code" / "prompts" / filename
    if not prompt_path.exists():
        prompt_path = ROOT_DIR / "prompts" / filename
    return prompt_path.read_text(encoding="utf-8")

def _analyze_media(
    media_info: MediaInfo,
    client: genai.Client,
    model_name: str,
    prompt_filename: str,
    prompt_version: str,
    schema_class: Type[T],
    validator_func: Any,
    default_prompt_query: str
) -> T:
    """
    Unified internal helper for loading prompt, executing Gemini API call with retries,
    resolving SDK parsed schema fields, and validating outputs.
    """
    prompt_text = _load_prompt(prompt_filename)
    media_bytes = media_info.file_path.read_bytes()
    
    media_part = types.Part.from_bytes(
        data=media_bytes,
        mime_type=media_info.mime_type
    )
    
    config = types.GenerateContentConfig(
        system_instruction=prompt_text,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        top_k=TOP_K,
        response_mime_type="application/json",
        response_schema=schema_class
    )
    
    retry_count = 0
    start_time = time.time()
    last_error = ""
    
    while retry_count < MAX_RETRIES:
        try:
            prompt_query = default_prompt_query
            if retry_count > 0:
                prompt_query = (
                    "Your previous response failed schema validation. "
                    "Return ONLY valid JSON adhering to the schema. "
                    "Do not include markdown code fences. Do not explain. "
                    + default_prompt_query
                )
            
            response = client.models.generate_content(
                model=model_name,
                contents=[media_part, prompt_query],
                config=config
            )
            
            # Check if SDK parsed structure is available natively
            if hasattr(response, "parsed") and response.parsed is not None:
                try:
                    # Coerce/Validate parsed response against Pydantic schema class
                    validated_data = schema_class.model_validate(response.parsed)
                    latency = time.time() - start_time
                    logger.info(f"Media {media_info.media_id} analyzed using SDK parser | Model: {model_name} | Prompt: {prompt_version} | Latency: {latency:.2f}s | Retries: {retry_count}")
                    return validated_data
                except ValidationError as ve:
                    logger.warning(f"SDK parsed content validation failed for {media_info.media_id}: {ve}")
                    last_error = str(ve)
                    retry_count += 1
                    continue
            
            # Fallback to validating the raw string response
            response_text = response.text or ""
            val_result = validator_func(response_text)
            if val_result.success and val_result.data is not None:
                latency = time.time() - start_time
                logger.info(f"Media {media_info.media_id} analyzed using fallback parser | Model: {model_name} | Prompt: {prompt_version} | Latency: {latency:.2f}s | Retries: {retry_count}")
                return val_result.data
            else:
                last_error = val_result.error or "Empty output text received"
                retry_count += 1
                
        except ValidationError as ve:
            logger.warning(f"Schema Validation Exception on attempt {retry_count + 1} for {media_info.media_id}: {ve}")
            last_error = str(ve)
            retry_count += 1
        except APIError as ae:
            logger.error(f"Gemini API Exception on attempt {retry_count + 1} for {media_info.media_id}: {ae}")
            last_error = f"APIError: {ae}"
            retry_count += 1
        except Exception as e:
            logger.error(f"Unexpected Exception on attempt {retry_count + 1} for {media_info.media_id}: {e}")
            last_error = str(e)
            retry_count += 1
            
    raise ValueError(f"Failed to analyze media {media_info.media_id} after {MAX_RETRIES} attempts. Details: {last_error}")

def analyze_image(media_info: MediaInfo, client: genai.Client) -> ImageAnalysis:
    """
    Analyzes an image using Gemini multimodal model and returns validated ImageAnalysis.
    """
    return _analyze_media(
        media_info=media_info,
        client=client,
        model_name=IMAGE_MODEL,
        prompt_filename="image_prompt_v1.md",
        prompt_version=IMAGE_PROMPT_VERSION,
        schema_class=ImageAnalysis,
        validator_func=parse_image_analysis,
        default_prompt_query="Analyze this image and return the structured schema extraction."
    )

def analyze_voice(media_info: MediaInfo, client: genai.Client) -> VoiceAnalysis:
    """
    Analyzes an audio file using Gemini audio capacity and returns validated VoiceAnalysis.
    """
    return _analyze_media(
        media_info=media_info,
        client=client,
        model_name=VOICE_MODEL,
        prompt_filename="voice_prompt_v1.md",
        prompt_version=VOICE_PROMPT_VERSION,
        schema_class=VoiceAnalysis,
        validator_func=parse_voice_analysis,
        default_prompt_query="Transcribe and extract facts from this audio file."
    )
