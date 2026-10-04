from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class LocationInfo(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    accuracy_m: Optional[float] = None
    sector: Optional[str] = None
    landmark_text: Optional[str] = None
    geo_confidence: float = 0.0

class EvidenceItem(BaseModel):
    type: str = "photo"  # photo, audio
    id: str
    url: Optional[str] = None
    quality: Literal["ok", "blurry", "dark", "poor"] = "ok"
    phash: Optional[str] = None

class TriageResult(BaseModel):
    report_id: str
    language_detected: str = "en"  # pa-Guru, pa-Latn, hi-Deva, hi-Latn, en
    summary_en: str
    category: str  # Aligned to service_code
    severity: Literal["low", "medium", "high"] = "medium"
    emergency: bool = False
    emergency_details: Optional[str] = None
    location: LocationInfo = Field(default_factory=LocationInfo)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    field_confidence: Dict[str, float] = Field(default_factory=dict)
    needs_clarification: Optional[str] = None

class RoutingDecision(BaseModel):
    department_id: str
    department_name: str
    confidence: float
    abstained: bool = False
    reason: str
    alternative_candidates: List[Dict[str, Any]] = Field(default_factory=list)

class ClosureAttempt(BaseModel):
    closure_id: str
    incident_id: str
    worker_id: str
    timestamp: str
    after_media_url: str
    worker_lat: float
    worker_lon: float
    distance_to_incident_m: float
    notes: Optional[str] = None

class VerificationResult(BaseModel):
    closure_id: str
    incident_id: str
    same_location_prob: float
    problem_resolved_prob: float
    evidence_quality: str = "ok"
    phash_duplicate_detected: bool = False
    geofence_passed: bool = True
    citizen_confirmation: Optional[Literal["fixed", "not_fixed", "cant_tell"]] = None
    final_posterior_score: float
    verified_state: Literal["fixed_verified", "fixed_unverified", "disputed", "reopened"]
    anomaly_flags: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)

class CanonicalIncident(BaseModel):
    incident_id: str
    service_code: str
    service_name: str
    title: str
    description: str
    status: Literal["open", "closed"] = "open"
    resolution_state: Literal[
        "open", "in_progress", "closure_pending", 
        "fixed_verified", "fixed_unverified", "disputed", "reopened"
    ] = "open"
    lat: float
    lon: float
    sector: str
    reports_count: int = 1
    child_report_ids: List[str] = Field(default_factory=list)
    assigned_department: Optional[str] = None
    routing_confidence: float = 0.0
    routing_abstained: bool = False
    verification_score: float = 0.0
    latest_ledger_hash: Optional[str] = None
    created_at: str
    updated_at: str
    before_media_url: Optional[str] = None
    after_media_url: Optional[str] = None
