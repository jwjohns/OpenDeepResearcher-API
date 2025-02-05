from abc import ABC, abstractmethod
import aiohttp
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_completion(
        self,
        session: aiohttp.ClientSession,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Optional[str]:
        """Generate a completion from the LLM."""
        pass

class OpenRouterProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "meta-llama/llama-3-8b-instruct:free"):
        self.api_key = api_key
        self.model = model
        self.url = "https://openrouter.ai/api/v1/chat/completions"
    
    async def generate_completion(
        self,
        session: aiohttp.ClientSession,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/yourusername/OpenDeepResearcher-API",
            "X-Title": "OpenDeepResearcher API",
            "Content-Type": "application/json"
        }
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            async with session.post(self.url, headers=headers, json=payload) as resp:
                response_text = await resp.text()
                logger.debug(f"OpenRouter raw response: {response_text}")
                
                if resp.status == 200:
                    data = json.loads(response_text)
                    return data["choices"][0]["message"]["content"]
                elif resp.status == 429:
                    data = json.loads(response_text)
                    error_msg = data.get("error", {}).get("message", "Rate limit exceeded")
                    logger.error(f"OpenRouter rate limit error: {error_msg}")
                    return None
                else:
                    logger.error(f"OpenRouter API error: {resp.status}")
                    logger.error(f"Response: {response_text}")
                    return None
        except Exception as e:
            logger.error(f"Error calling OpenRouter: {str(e)}", exc_info=True)
            return None

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.openai.com/v1/chat/completions"
    
    async def generate_completion(
        self,
        session: aiohttp.ClientSession,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            async with session.post(self.url, headers=headers, json=payload) as resp:
                response_text = await resp.text()
                logger.debug(f"OpenAI raw response: {response_text}")
                
                if resp.status == 200:
                    data = json.loads(response_text)
                    return data["choices"][0]["message"]["content"]
                elif resp.status == 429:
                    logger.error("OpenAI rate limit exceeded")
                    return None
                else:
                    logger.error(f"OpenAI API error: {resp.status}")
                    logger.error(f"Response: {response_text}")
                    return None
        except Exception as e:
            logger.error(f"Error calling OpenAI: {str(e)}", exc_info=True)
            return None

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.anthropic.com/v1/messages"
    
    async def generate_completion(
        self,
        session: aiohttp.ClientSession,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Optional[str]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        
        try:
            # Convert chat format to Anthropic format
            system_message = next((m["content"] for m in messages if m["role"] == "system"), "")
            user_message = next((m["content"] for m in messages if m["role"] == "user"), "")
            
            if system_message:
                user_message = f"{system_message}\n\n{user_message}"
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": user_message}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            async with session.post(self.url, headers=headers, json=payload) as resp:
                response_text = await resp.text()
                logger.debug(f"Anthropic raw response: {response_text}")
                
                if resp.status == 200:
                    data = json.loads(response_text)
                    return data["content"][0]["text"]
                elif resp.status == 429:
                    logger.error("Anthropic rate limit exceeded")
                    return None
                else:
                    logger.error(f"Anthropic API error: {resp.status}")
                    logger.error(f"Response: {response_text}")
                    return None
        except Exception as e:
            logger.error(f"Error calling Anthropic: {str(e)}", exc_info=True)
            return None

class OllamaProvider(LLMProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama2"):
        self.host = host.rstrip('/')
        self.model = model
        self.url = f"{self.host}/api/chat"
    
    async def generate_completion(
        self,
        session: aiohttp.ClientSession,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Optional[str]:
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            async with session.post(self.url, json=payload) as resp:
                response_text = await resp.text()
                logger.debug(f"Ollama raw response: {response_text}")
                
                if resp.status == 200:
                    data = json.loads(response_text)
                    return data["message"]["content"]
                else:
                    logger.error(f"Ollama API error: {resp.status}")
                    logger.error(f"Response: {response_text}")
                    return None
        except Exception as e:
            logger.error(f"Error calling Ollama: {str(e)}", exc_info=True)
            return None

def get_llm_provider(config) -> LLMProvider:
    """Factory function to create the appropriate LLM provider based on configuration."""
    provider = config.llm_provider.lower()
    
    if provider == "openrouter":
        return OpenRouterProvider(config.openrouter_api_key, config.openrouter_model)
    elif provider == "openai":
        return OpenAIProvider(config.openai_api_key, config.openai_model)
    elif provider == "anthropic":
        return AnthropicProvider(config.anthropic_api_key, config.anthropic_model)
    elif provider == "ollama":
        return OllamaProvider(config.ollama_host, config.ollama_model)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}") 