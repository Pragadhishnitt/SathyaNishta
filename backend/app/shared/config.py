import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    _repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(dotenv_path=_repo_root / ".env", override=False)
    load_dotenv(dotenv_path=_repo_root / "backend" / ".env", override=False)
except Exception:
    # If python-dotenv isn't available or paths can't be resolved, fall back to OS env only.
    pass

class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
    # Portkey Virtual Key (recommended): points to the provider key stored in Portkey vault
    PORTKEY_VIRTUAL_KEY = os.getenv("PORTKEY_VIRTUAL_KEY")
    # Portkey Config: either a config id like "pc-***" or a JSON string (e.g. to enable semantic cache)
    PORTKEY_CONFIG = os.getenv("PORTKEY_CONFIG")
    # Default model used for chat completions routed via Portkey
    PORTKEY_MODEL = os.getenv("PORTKEY_MODEL") or "gemini-1.5-flash"
    GRAFANA_URL = os.getenv("GRAFANA_URL")

config = Config()
