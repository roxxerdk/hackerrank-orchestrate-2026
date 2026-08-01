import mimetypes
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field
from app.config import DATASET_DIR

class MediaType(str, Enum):
    IMAGE = "image"
    VOICE = "voice"

class MediaInfo(BaseModel):
    """
    Model holding validated target file details.
    """
    media_id: str = Field(..., description="Unique media identifier")
    media_type: MediaType = Field(..., description="Type of the media (image or voice)")
    file_path: Path = Field(..., description="Absolute path resolving to target file")
    mime_type: str = Field(..., description="Detected MIME type format")
    file_size_bytes: int = Field(..., ge=0, description="Size of the media file in bytes")

def resolve_media(media_id: str, relative_path: str, media_type: MediaType) -> MediaInfo:
    """
    Resolves the physical media file details from the dataset directory and relative path.

    Raises:
        FileNotFoundError: If the media file does not exist.
        ValueError: If the media file is empty.
    """
    # The relative path from CSV (e.g. 'media/images/img_001.jpg') resolved against DATASET_DIR
    absolute_path = (DATASET_DIR / relative_path).resolve()
    
    # Validate physical presence and size
    if not absolute_path.exists() or not absolute_path.is_file():
        raise FileNotFoundError(f"Resolved path does not exist or is not a file: {absolute_path}")
        
    file_size = absolute_path.stat().st_size
    if file_size == 0:
        raise ValueError(f"Resolved media file is empty: {absolute_path}")
        
    # Detect mime type
    mime_type, _ = mimetypes.guess_type(str(absolute_path))
    if not mime_type:
        # Fallback mappings for standard hackathon media extensions
        if absolute_path.suffix.lower() == ".mp3":
            mime_type = "audio/mpeg"
        elif absolute_path.suffix.lower() in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        else:
            mime_type = "application/octet-stream"
    else:
        # Normalize MP3 mime-type to standard audio/mpeg
        if mime_type == "audio/mp3":
            mime_type = "audio/mpeg"
            
    return MediaInfo(
        media_id=media_id,
        media_type=media_type,
        file_path=absolute_path,
        mime_type=mime_type,
        file_size_bytes=file_size
    )
