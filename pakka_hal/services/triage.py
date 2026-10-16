import logging
import base64
import re
from typing import Dict, Any, Optional
from pakka_hal.models.incident import TriageResult
from pakka_hal.services.llm import get_llm_provider
from pakka_hal.config import city_config

logger = logging.getLogger(__name__)

from pakka_hal.services.emergency import check_emergency_safety_net

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
