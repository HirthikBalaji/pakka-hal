from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from pakka_hal.models.incident import TriageResult, VerificationResult

class LLMProvider(ABC):
    """
    Abstract Base Class for swappable LLM backends:
    - Hosted: Google Gemini 1.5 Flash / Pro
    - Open-Weights: Gemma 2 (9B / 27B) via Ollama / vLLM
    - Mock / Offline: Deterministic fixtures for CI/CD and testing
    """

    @abstractmethod
    async def triage_report(
        self,
        text: str,
        image_bytes: Optional[bytes] = None,
        audio_transcript: Optional[str] = None,
        hint_sector: Optional[str] = None
    ) -> TriageResult:
        """
        Parses multilingual, unstructured civic report text + media into structured TriageResult.
        """
        pass

    @abstractmethod
    async def verify_closure(
        self,
        before_image_bytes: Optional[bytes],
        after_image_bytes: bytes,
        category: str,
        context: Dict[str, Any]
    ) -> Tuple[float, float, str, List[str]]:
        """
        Cross-examines before & after evidence photos.
        Returns:
            same_location_prob: float (0.0 to 1.0)
            problem_resolved_prob: float (0.0 to 1.0)
            evidence_quality: str ('ok', 'blurry', 'dark')
            reasons: list of explanatory strings
        """
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        Returns dense vector embedding for semantic similarity / deduplication.
        """
        pass
