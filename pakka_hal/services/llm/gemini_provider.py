import base64
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
import httpx
from pakka_hal.services.llm.base import LLMProvider
from pakka_hal.models.incident import TriageResult, LocationInfo, EvidenceItem
from pakka_hal.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    """
    Google Gemini 1.5 Flash / Pro Provider via official REST API.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    async def triage_report(
        self,
        text: str,
        image_bytes: Optional[bytes] = None,
        audio_transcript: Optional[str] = None,
        hint_sector: Optional[str] = None
    ) -> TriageResult:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured. Set GEMINI_API_KEY or use LLM_PROVIDER=mock.")

        system_instruction = """
        You are Pakka Hal's Civic Triage Engine for Chandigarh (UT, India).
        Taxonomy of service_codes:
        - STREETLIGHT_OUT: Streetlight broken, wire exposed, dark spot
        - POTHOLE: Road damage, crater, broken asphalt
        - GARBAGE_OVERFLOW: Trash dump, bin overflow, litter
        - DRAIN_BLOCKED: Clogged drain, waterlogging
        - MANHOLE_COVER: Open or broken manhole cover (HIGH SEVERITY)
        - SIGNAL_FAULT: Traffic light not working
        - DAMAGED_SIGNAGE: Broken or missing sector board
        - WATER_LEAK: Burst drinking water pipe
        - EMERGENCY_REDIRECT: Urgent threat to life/fire/blood/collapse (NEVER QUEUE AS CIVIC ISSUE)
        - OTHER: None of the above

        Respond STRICTLY with valid JSON following this schema:
        {
          "language_detected": "pa-Guru | pa-Latn | hi-Deva | hi-Latn | en",
          "summary_en": "One sentence summary in English",
          "category": "SERVICE_CODE",
          "severity": "low | medium | high",
          "emergency": false,
          "emergency_details": "Reason if emergency is true",
          "sector": "Sector name e.g. SEC-22 or null",
          "landmark_text": "Extracted landmark",
          "category_confidence": 0.0 to 1.0,
          "location_confidence": 0.0 to 1.0
        }
        """

        prompt = f"Citizen Report Input:\nText: {text}\nAudio Transcript: {audio_transcript or 'N/A'}\nHint Sector: {hint_sector or 'N/A'}"
        parts = [{"text": prompt}]

        if image_bytes:
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_bytes).decode("utf-8")
                }
            })

        payload = {
            "contents": [{"parts": parts}],
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "generation_config": {
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}?key={self.api_key}",
                json=payload
            )
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)

        import uuid
        return TriageResult(
            report_id=f"rep_{uuid.uuid4().hex[:8]}",
            language_detected=parsed.get("language_detected", "en"),
            summary_en=parsed.get("summary_en", text[:100]),
            category=parsed.get("category", "OTHER"),
            severity=parsed.get("severity", "medium"),
            emergency=parsed.get("emergency", False),
            emergency_details=parsed.get("emergency_details"),
            location=LocationInfo(
                sector=parsed.get("sector", "SEC-17"),
                landmark_text=parsed.get("landmark_text", ""),
                geo_confidence=parsed.get("location_confidence", 0.7)
            ),
            field_confidence={
                "category": parsed.get("category_confidence", 0.8),
                "location": parsed.get("location_confidence", 0.7)
            }
        )

    async def verify_closure(
        self,
        before_image_bytes: Optional[bytes],
        after_image_bytes: bytes,
        category: str,
        context: Dict[str, Any]
    ) -> Tuple[float, float, str, List[str]]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured.")

        parts = [{
            "text": f"""
            Compare these two civic photos for Chandigarh Municipal Corporation.
            Image 1: BEFORE defect was reported ({category}).
            Image 2: AFTER municipal crew claims repair.
            Evaluate:
            1. same_location: probability (0.0 to 1.0) that both photos depict the exact same street/background/landmarks.
            2. problem_resolved: probability (0.0 to 1.0) that the specific defect is verifiably resolved in Image 2.
            3. reasons: array of concise observations.
            Return JSON:
            {{"same_location_prob": 0.0, "problem_resolved_prob": 0.0, "evidence_quality": "ok", "reasons": ["..."]}}
            """
        }]

        if before_image_bytes:
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(before_image_bytes).decode("utf-8")
                }
            })
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(after_image_bytes).decode("utf-8")
            }
        })

        payload = {
            "contents": [{"parts": parts}],
            "generation_config": {
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}?key={self.api_key}", json=payload)
            resp.raise_for_status()
            data = resp.json()
            parsed = json.loads(data["candidates"][0]["content"]["parts"][0]["text"])

        return (
            float(parsed.get("same_location_prob", 0.5)),
            float(parsed.get("problem_resolved_prob", 0.5)),
            parsed.get("evidence_quality", "ok"),
            parsed.get("reasons", ["Verified via Gemini Vision"])
        )

    async def get_embedding(self, text: str) -> List[float]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured.")
        embed_url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.api_key}"
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]}
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(embed_url, json=payload)
            resp.raise_for_status()
            return resp.json()["embedding"]["values"]
