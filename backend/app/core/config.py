from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Database (Supabase)
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None

    # Neo4j
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    
    # Cohere — Vector Embeddings (1024-dim) for RAG
    COHERE_API_KEY: Optional[str] = None
    
    # AI Gateway (Portkey) — all LLM calls go through Portkey
    PORTKEY_API_KEY: Optional[str] = None
    PORTKEY_CONFIG_ID: Optional[str] = None

    model_config = SettingsConfigDict(extra="ignore")

settings = Settings()
