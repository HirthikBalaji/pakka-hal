from pakka_hal.config import LLM_PROVIDER
from pakka_hal.services.llm.base import LLMProvider
from pakka_hal.services.llm.mock_provider import MockLLMProvider
from pakka_hal.services.llm.gemini_provider import GeminiProvider
from pakka_hal.services.llm.open_weights import OpenWeightsProvider

def get_llm_provider(provider_type: str = None) -> LLMProvider:
    ptype = (provider_type or LLM_PROVIDER).lower()
    if ptype == "gemini":
        return GeminiProvider()
    elif ptype == "ollama" or ptype == "open_weights":
        return OpenWeightsProvider()
    else:
        return MockLLMProvider()
