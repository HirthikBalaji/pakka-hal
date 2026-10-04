from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class LedgerEntry(BaseModel):
    entry_id: str
    timestamp: str
    incident_id: str
    event_type: str  # report_received, merged, routed, closure_attempt, verification_result, citizen_confirmation
    payload_hash: str
    prev_hash: str
    entry_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class LedgerChainStatus(BaseModel):
    total_entries: int
    genesis_hash: str
    latest_hash: str
    is_valid: bool
    tampered_entry_id: Optional[str] = None
