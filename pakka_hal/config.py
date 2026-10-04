import os
from pathlib import Path
from typing import Any, Dict, List
import yaml
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
CITY_CONFIG_PATH = os.getenv("CITY_CONFIG_PATH", str(BASE_DIR / "config" / "city.yaml"))

def load_city_config() -> Dict[str, Any]:
    config_path = Path(CITY_CONFIG_PATH)
    if not config_path.is_absolute():
        config_path = BASE_DIR / config_path
    if not config_path.exists():
        raise FileNotFoundError(f"City configuration not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

city_config = load_city_config()

PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPEN_WEIGHTS_MODEL = os.getenv("OPEN_WEIGHTS_MODEL", "gemma2:9b")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pakka_hal.db")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
HASH_CHAIN_SEED = os.getenv("HASH_CHAIN_SEED", "pakka_hal_chandigarh_genesis_2026")
