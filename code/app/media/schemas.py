from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class UrgencyLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class VoiceIntent(str, Enum):
    PAYMENT_REQUEST = "payment_request"
    EVENT = "event"
    PROMOTION = "promotion"
    CASUAL = "casual"
    GREETING = "greeting"
    ALERT = "alert"
    SPAM = "spam"
    UNKNOWN = "unknown"

class UrgencyInfo(BaseModel):
    level: UrgencyLevel = Field(..., description="The urgency classification level (high, medium, or low)")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the urgency level [0.0 - 1.0]")

class BaseMediaAnalysis(BaseModel):
    urgency: UrgencyInfo = Field(..., description="Urgency analysis results")
    routing_evidence: List[str] = Field(default_factory=list, description="Factual criteria matching reasons")

class EventInfo(BaseModel):
    title: Optional[str] = Field(None, description="Title/Name of the event")
    date: Optional[str] = Field(None, description="Event date in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Event time in HH:MM format")
    location: Optional[str] = Field(None, description="Venue/Location name")
    entry_fee: Optional[float] = Field(None, description="Fee/Cost of entry if present")

class PaymentInfo(BaseModel):
    is_payment_request: bool = Field(False, description="True if requesting or reminding about payment")
    amount: Optional[float] = Field(None, description="The payment request amount")
    payee_phone_or_upiid: Optional[str] = Field(None, description="UPI address or payee handle")

class QRInfo(BaseModel):
    contains_qr: bool = Field(False, description="True if a QR code is visible")
    embedded_url_or_data: Optional[str] = Field(None, description="Embedded decoded QR code URL/data")

class ImageFacts(BaseModel):
    description: str = Field(..., description="Objective description of the visual scene")
    event: EventInfo = Field(default_factory=EventInfo)
    payment: PaymentInfo = Field(default_factory=lambda: PaymentInfo(is_payment_request=False))
    QR: QRInfo = Field(default_factory=lambda: QRInfo(contains_qr=False))
    phones: List[str] = Field(default_factory=list, description="All visible phone numbers")
    links: List[str] = Field(default_factory=list, description="All visible URLs/Links")

class ImageSignals(BaseModel):
    contains_qr: bool = False
    contains_amount: bool = False
    contains_payment_request: bool = False
    contains_phone: bool = False
    contains_link: bool = False
    contains_date: bool = False
    contains_time: bool = False
    contains_deadline: bool = False
    contains_urgency_phrase: bool = False

class ImageAnalysis(BaseMediaAnalysis):
    facts: ImageFacts = Field(..., description="Factual extracted data from image")
    detected_signals: ImageSignals = Field(default_factory=ImageSignals, description="Signals flags detected in the visual content")

class KeyEntities(BaseModel):
    amount: Optional[float] = Field(None, description="Payment amount referenced")
    due_date: Optional[str] = Field(None, description="Payment or event deadline date")
    phone_numbers: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)
    names: List[str] = Field(default_factory=list)

class VoiceFacts(BaseModel):
    transcript: str = Field(..., description="Raw speech-to-text transcript")
    summary: str = Field(..., description="Objective description of the request")
    intent: VoiceIntent = Field(..., description="Direct intent of the voice message")
    key_entities: KeyEntities = Field(default_factory=KeyEntities)

class VoiceSignals(BaseModel):
    contains_amount: bool = False
    contains_payment_request: bool = False
    contains_deadline: bool = False
    contains_urgency_phrase: bool = False
    contains_names: bool = False

class VoiceAnalysis(BaseMediaAnalysis):
    facts: VoiceFacts = Field(..., description="Factual extracted data from audio transcript")
    detected_signals: VoiceSignals = Field(default_factory=VoiceSignals, description="Signals flags detected in audio transcription")
