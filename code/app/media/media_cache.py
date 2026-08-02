from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel, Field, ValidationError

from app.config import CACHE_DIR, IMAGE_MODEL, VOICE_MODEL, IMAGE_PROMPT_VERSION, VOICE_PROMPT_VERSION, CACHE_VERSION
from app.media.media_loader import MediaInfo, MediaType
from app.utils.json_utils import safe_json_load, safe_json_dump, utc_now_iso

class CacheMetadata(BaseModel):
    """
    Standard schema for media analysis cache files.
    """
    version: str = Field(..., description="Cache format version")
    model: str = Field(..., description="Gemini model identifier used for analysis")
    prompt_version: str = Field(..., description="Prompt version used for analysis")
    created_at: str = Field(..., description="UTC ISO-8601 creation timestamp")
    media_id: str = Field(..., description="Unique media identifier")
    media_type: MediaType = Field(..., description="Type of the media (image or voice)")
    analysis: dict[str, Any] = Field(..., description="The validated structured analysis output payload")

def _get_cache_path(media_info: MediaInfo) -> Path:
    """
    Resolves the nested path for a media cache file.
    """
    # Map MediaType to subfolder (e.g. image -> 'image', voice -> 'voice')
    folder = "image" if media_info.media_type == MediaType.IMAGE else "voice"
    return CACHE_DIR / "media" / folder / f"{media_info.media_id}.json"

def cache_exists(media_info: MediaInfo) -> bool:
    """
    Verifies if a valid cache file exists for the media, checking version compatibility.
    """
    return load_analysis(media_info) is not None

def load_analysis(media_info: MediaInfo) -> Optional[CacheMetadata]:
    """
    Loads and returns the validated CacheMetadata model for the target media file.
    Returns None if cache is missing, corrupt, or outdated.
    """
    cache_path = _get_cache_path(media_info)
    if not cache_path.exists():
        return None
        
    try:
        raw_content = cache_path.read_text(encoding="utf-8")
        parsed = safe_json_load(raw_content)
        metadata = CacheMetadata.model_validate(parsed)
        
        # Invalidate if model configuration or prompt versions have changed
        expected_model = IMAGE_MODEL if metadata.media_type == MediaType.IMAGE else VOICE_MODEL
        expected_prompt_ver = IMAGE_PROMPT_VERSION if metadata.media_type == MediaType.IMAGE else VOICE_PROMPT_VERSION
        if (metadata.version != CACHE_VERSION or 
            metadata.model != expected_model or 
            metadata.prompt_version != expected_prompt_ver):
            return None
            
        return metadata
    except ValidationError as e:
        print(f"[Warning] Cache Validation failed for {media_info.media_id}: {e}")
        return None
    except Exception as e:
        print(f"[Warning] Cache Load failed for {media_info.media_id}: {e}")
        return None

def store_analysis(media_info: MediaInfo, analysis: dict[str, Any]) -> None:
    """
    Safely stores analysis data to the cache using atomic write sequences.
    """
    cache_path = _get_cache_path(media_info)
    
    # Ensure cache folder exists
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    expected_model = IMAGE_MODEL if media_info.media_type == MediaType.IMAGE else VOICE_MODEL
    expected_prompt_ver = IMAGE_PROMPT_VERSION if media_info.media_type == MediaType.IMAGE else VOICE_PROMPT_VERSION
    
    # Construct CacheMetadata payload
    metadata = CacheMetadata(
        version=CACHE_VERSION,
        model=expected_model,
        prompt_version=expected_prompt_ver,
        created_at=utc_now_iso(),
        media_id=media_info.media_id,
        media_type=media_info.media_type,
        analysis=analysis
    )
    
    serialized_str = safe_json_dump(metadata.model_dump())
    
    # Perform atomic write sequence via temp file rename
    temp_path = cache_path.with_suffix(".tmp")
    try:
        temp_path.write_text(serialized_str, encoding="utf-8")
        # Overwrite destination file atomically using pathlib replace
        temp_path.replace(cache_path)
    except Exception as e:
        # Cleanup temporary files if failure occurs
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise e

def invalidate_cache(media_info: MediaInfo) -> None:
    """
    Invalidates (deletes) the cache entry for the media file.
    """
    cache_path = _get_cache_path(media_info)
    if cache_path.exists():
        try:
            cache_path.unlink()
        except OSError:
            pass
