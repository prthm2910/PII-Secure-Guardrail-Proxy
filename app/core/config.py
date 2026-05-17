from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str
    DEBUG: bool
    HOST: str
    PORT: int
    APP_MODULE: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool

    # PII Settings
    TOKEN_TTL: int
    NORMALIZE_UNICODE: bool
    ENFORCE_STRICT_CHECKSUMS: bool

    # Postgres
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    POSTGRES_DB: str

    # Database URLs
    DATABASE_URL: str
    DIRECT_DATABASE_URL: str

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self.DATABASE_URL or f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # LLM
    LLM_API_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_API_KEY: str
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    
    # Provider selection
    LLM_PROVIDER: str = "groq" # "openai", "groq", "nvidia"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
