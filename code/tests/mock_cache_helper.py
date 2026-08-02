import sys
import os
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.media.schemas import ImageAnalysis
from app.media.media_cache import store_analysis, CacheMetadata, MediaInfo, MediaType

def mock_media_cache():
    print("--- Creating Mocked Image Cache ---")
    
    # 1. We mock image img_005 cache metadata
    mock_analysis = ImageAnalysis(
        urgency={
            "level": "high",
            "score": 0.9
        },
        routing_evidence=["Urgent alert banner present"],
        facts={
            "description": "Objective description of the visual scene",
            "event": {
                "title": "Alert Event",
                "date": "2026-07-26",
                "time": "12:00",
                "location": "Online"
            },
            "payment": {
                "is_payment_request": False,
                "amount": None,
                "payee_phone_or_upiid": None
            },
            "QR": {
                "contains_qr": True,
                "embedded_url_or_data": "https://example.com/qr"
            },
            "phones": ["1234567890"],
            "links": ["https://example.com"]
        },
        detected_signals={
            "contains_qr": True,
            "contains_amount": False,
            "contains_payment_request": False,
            "contains_phone": True,
            "contains_link": True,
            "contains_date": True,
            "contains_time": True,
            "contains_deadline": True,
            "contains_urgency_phrase": True
        }
    )
    
    # Mock MediaInfo properties matching img_008 file
    from app.config import DATASET_DIR
    media_info = MediaInfo(
        media_id="img_008",
        media_type=MediaType.IMAGE,
        file_path=(DATASET_DIR / "media/images/img_008.jpg").resolve(),
        mime_type="image/jpeg",
        file_size_bytes=88042
    )
    
    # Store directly using cache writer logic
    store_analysis(media_info, mock_analysis.model_dump())
    print("[Success] Successfully stored mock media cache for img_008")

if __name__ == "__main__":
    mock_media_cache()
