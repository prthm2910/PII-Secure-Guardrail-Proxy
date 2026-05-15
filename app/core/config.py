from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str
    DEBUG: bool
    HOST: str
    PORT: int
    APP_MODULE: str
    
    # PII Settings
    TOKEN_TTL: int
    NORMALIZE_UNICODE: bool
    ENFORCE_STRICT_CHECKSUMS: bool
    
    # Database
    DATABASE_URL: str
    DIRECT_DATABASE_URL: str
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: str
    REDIS_PASSWORD: str
    REDIS_SSL: bool
    
    # Postgres
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # LLM
    LLM_API_BASE_URL: str
    LLM_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
