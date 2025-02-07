import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

load_dotenv()

# Required API keys
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")

class Settings(BaseSettings):
    # Required API Keys
    serpapi_api_key: Optional[str] = None
    jina_api_key: str
    
    # Search Provider Configuration
    search_provider: str = "ddg"  # Options: serpapi, ddg, bing
    bing_api_key: Optional[str] = None
    
    # LLM Provider Configuration
    llm_provider: str = "openrouter"
    
    # OpenRouter Configuration
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "meta-llama/llama-3-8b-instruct:free"
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "o1"  # Using O1 as default model
    
    # Anthropic Configuration
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-haiku-20240307"
    
    # Ollama Configuration
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    ) 