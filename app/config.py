from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    openrouter_api_key: str
    serpapi_api_key: str
    jina_api_key: str
    default_model: str = "anthropic/claude-3.5-haiku"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8" 