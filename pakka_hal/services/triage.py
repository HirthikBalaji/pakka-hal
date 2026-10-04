import logging
import base64
import re
from typing import Dict, Any, Optional
from pakka_hal.models.incident import TriageResult
from pakka_hal.services.llm import get_llm_provider
from pakka_hal.config import city_config

logger = logging.getLogger(__name__)

# Mandatory safety net: Non-negotiable emergency keywords across English, Hindi, and Punjabi (Gurmukhi)
CRITICAL_EMERGENCY_TERMS = [
    # English
    "fire", "accident", "ambulance", "blood", "police", "cylinder blast", "electrocution",
    "collapsed", "attack", "emergency", "112",
    # Hindi (Devanagari & Latin)
    "aag", "हादसा", "दुर्घटना", "आग", "खून", "एम्बुलेंस", "ब्लास्ट", "सिलेंडर",
    "करंट", "janleva", "bhaari aag", "current",
    # Punjabi (Gurmukhi & Latin)
    "ਅੱਗ", "ਹਾਦਸਾ", "ਐਂਬੂਲੈਂਸ", "ਪੁਲਿਸ", "ਬਲਾਸਟ", "ਸਿਲੰਡਰ", "ਖੂਨ", "ਜਾਨਲੇਵਾ",
    "agg", "hadsa", "khoon"
]

def check_emergency_safety_net(text: str) -> Optional[str]:
    """Deterministic keyword scanner that never depends on LLM inference."""
    lowered = text.lower()
    for term in CRITICAL_EMERGENCY_TERMS:
        if term in lowered:
            return f"Emergency condition triggered by keyword '{term}'. Immediate 112 redirect."
    return None

class TriageService:
    def __init__(self, provider_type: Optional[str] = None):
        self.llm = get_llm_provider(provider_type)

    async def process_report(
        self,
        description: str,
        image_bytes: Optional[bytes] = None,
        audio_transcript: Optional[str] = None,
        sector_hint: Optional[str] = None
    ) -> TriageResult:
        full_text = f"{description} {audio_transcript or ''}".strip()

        # Step 1: Run deterministic safety net
        safety_net_hit = check_emergency_safety_net(full_text)

        # Step 2: Run LLM provider triage
        result = await self.llm.triage_report(
            text=description,
            image_bytes=image_bytes,
            audio_transcript=audio_transcript,
            hint_sector=sector_hint
        )

        # Step 3: Override if safety net triggered
        if safety_net_hit:
            result.emergency = True
            result.emergency_details = safety_net_hit
            result.severity = "high"
            result.category = "EMERGENCY_REDIRECT"

        return result
