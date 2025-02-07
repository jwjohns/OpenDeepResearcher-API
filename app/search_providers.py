from abc import ABC, abstractmethod
import aiohttp
import logging
from typing import List, Optional
from bs4 import BeautifulSoup
import urllib.parse
import json

logger = logging.getLogger(__name__)

class SearchProvider(ABC):
    """Abstract base class for search providers."""
    
    @abstractmethod
    async def search(
        self,
        session: aiohttp.ClientSession,
        query: str,
        num_results: int = 10
    ) -> List[str]:
        """Perform a search and return a list of URLs."""
        pass

class SerpAPIProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://serpapi.com/search"
    
    async def search(
        self,
        session: aiohttp.ClientSession,
        query: str,
        num_results: int = 10
    ) -> List[str]:
        params = {
            "api_key": self.api_key,
            "q": query,
            "num": num_results
        }
        
        try:
            logger.info(f"Performing SERPAPI search for query: {query}")
            async with session.get(self.url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    organic_results = data.get("organic_results", [])
                    links = [result["link"] for result in organic_results if "link" in result]
                    logger.info(f"Found {len(links)} results from SERPAPI")
                    return links
                else:
                    logger.error(f"SERPAPI error: {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Error performing SERPAPI search: {str(e)}", exc_info=True)
            return []

class DDGProvider(SearchProvider):
    def __init__(self):
        self.url = "https://html.duckduckgo.com/html/"
    
    async def search(
        self,
        session: aiohttp.ClientSession,
        query: str,
        num_results: int = 10
    ) -> List[str]:
        params = {
            "q": query,
            "s": "0",  # offset
            "dc": "0",  # don't count
            "kl": "us-en",  # region/language
            "kp": "1"  # safe search
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            logger.info(f"Performing DuckDuckGo search for query: {query}")
            async with session.post(self.url, data=params, headers=headers) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    results = soup.find_all('a', class_='result__url')
                    links = []
                    
                    for result in results[:num_results]:
                        href = result.get('href', '')
                        if href.startswith('/'):
                            continue
                        if not href.startswith(('http://', 'https://')):
                            href = 'https://' + href
                        links.append(href)
                    
                    logger.info(f"Found {len(links)} results from DuckDuckGo")
                    return links
                else:
                    logger.error(f"DuckDuckGo error: {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Error performing DuckDuckGo search: {str(e)}", exc_info=True)
            return []

class BingProvider(SearchProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.url = "https://api.bing.microsoft.com/v7.0/search"
    
    async def search(
        self,
        session: aiohttp.ClientSession,
        query: str,
        num_results: int = 10
    ) -> List[str]:
        if not self.api_key:
            logger.error("Bing API key not provided")
            return []
            
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        params = {
            "q": query,
            "count": num_results,
            "responseFilter": "Webpages"
        }
        
        try:
            logger.info(f"Performing Bing search for query: {query}")
            async with session.get(self.url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    webpages = data.get("webPages", {}).get("value", [])
                    links = [page["url"] for page in webpages if "url" in page]
                    logger.info(f"Found {len(links)} results from Bing")
                    return links
                else:
                    logger.error(f"Bing API error: {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Error performing Bing search: {str(e)}", exc_info=True)
            return []

def get_search_provider(config) -> SearchProvider:
    """Factory function to create the appropriate search provider based on configuration."""
    provider = config.search_provider.lower()
    
    if provider == "serpapi" and config.serpapi_api_key:
        return SerpAPIProvider(config.serpapi_api_key)
    elif provider == "bing" and config.bing_api_key:
        return BingProvider(config.bing_api_key)
    elif provider == "ddg":
        return DDGProvider()
    elif provider == "serpapi":
        logger.warning("SerpAPI selected but no API key provided, falling back to DuckDuckGo")
        return DDGProvider()
    else:
        logger.warning(f"Unsupported search provider: {provider}, using DuckDuckGo")
        return DDGProvider() 