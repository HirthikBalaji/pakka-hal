from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Open311Service(BaseModel):
    service_code: str
    service_name: str
    description: Optional[str] = None
    metadata: bool = False
    type: str = "realtime"  # realtime or batch
    keywords: Optional[List[str]] = None
    group: Optional[str] = "Civic Infrastructure"

class Open311RequestCreate(BaseModel):
    service_code: Optional[str] = None
    lat: Optional[float] = None
    long: Optional[float] = None
    address_string: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    description: str
    media_url: Optional[str] = None
    # Pakka Hal extended intake fields
    language: Optional[str] = None
    voice_note_url: Optional[str] = None
    raw_audio_base64: Optional[str] = None
    sector: Optional[str] = None

class Open311RequestResponse(BaseModel):
    service_request_id: str
    token: Optional[str] = None
    service_notice: Optional[str] = None
    account_id: Optional[str] = None

class Open311RequestDetail(BaseModel):
    service_request_id: str
    status: str  # "open" or "closed" (Open311 base standard)
    status_notes: Optional[str] = None
    service_name: str
    service_code: str
    description: str
    agency_responsible: Optional[str] = None
    service_notice: Optional[str] = None
    requested_datetime: str
    updated_datetime: Optional[str] = None
    expected_datetime: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    long: Optional[float] = None
    media_url: Optional[str] = None
    # Pakka Hal Extensions for Verified Resolution & Public Transparency
    extended_attributes: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Pakka Hal DPI Extensions: resolution_state, verification_score, ledger_hash, etc."
    )
