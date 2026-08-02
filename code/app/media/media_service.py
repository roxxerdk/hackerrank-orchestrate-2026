import logging
from typing import Union
from google import genai

from app.media.media_loader import resolve_media, MediaType, MediaInfo
from app.media.media_cache import cache_exists, load_analysis, store_analysis
from app.media.media_analyzer import analyze_image, analyze_voice
from app.media.schemas import ImageAnalysis, VoiceAnalysis

logger = logging.getLogger("media_service")

# Type alias representing any valid media analysis output model
MediaAnalysis = Union[ImageAnalysis, VoiceAnalysis]

# Dispatcher mapping for schema validation classes
SCHEMAS = {
    MediaType.IMAGE: ImageAnalysis,
    MediaType.VOICE: VoiceAnalysis,
}

# Dispatcher mapping for model analyzer callers
ANALYZERS = {
    MediaType.IMAGE: analyze_image,
    MediaType.VOICE: analyze_voice,
}

def analyze_media(
    media_id: str,
    relative_path: str,
    media_type: MediaType,
    client: genai.Client
) -> MediaAnalysis:
    """
    Orchestrates the media processing pipeline:
      1. Resolves and validates the target media file metadata.
      2. Checks local disk cache for compatibility.
      3. Performs multimodal/audio analysis if cache miss occurs.
      4. Saves valid analysis to local cache (without failing query on cache error).

    Raises:
        FileNotFoundError: If the media file is missing.
        ValueError: If media properties are invalid or API parsing fails.
    """
    logger.info("Initiating analysis for media: %s (Type: %s)", media_id, media_type.value)
    
    # 1. Resolve media path and metadata
    media_info = resolve_media(media_id, relative_path, media_type)
    logger.info("Resolved media path: %s | Size: %s bytes | MIME: %s", 
                media_info.file_path, media_info.file_size_bytes, media_info.mime_type)
    
    # 2. Check local disk cache
    if cache_exists(media_info):
        cached_meta = load_analysis(media_info)
        if cached_meta is not None:
            logger.info("Cache hit for media: %s. Loading parsed analysis structure.", media_id)
            return SCHEMAS[media_type].model_validate(cached_meta.analysis)
                
    logger.info("Cache miss for media: %s. Ingesting media file to Gemini API.", media_id)
    
    # 3. Cache Miss: Run analysis using dispatcher mappings
    analysis_result = ANALYZERS[media_type](media_info, client)
    logger.info("Analysis successfully completed by model for media: %s", media_id)
    
    # 4. Save to Cache
    try:
        store_analysis(media_info, analysis_result.model_dump())
        logger.info("Successfully cached analysis result for media: %s", media_id)
    except Exception as e:
        logger.warning("Cache store failed for media %s (non-fatal): %s", media_id, e)
        
    return analysis_result
