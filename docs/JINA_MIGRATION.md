# Migration Plan: Replacing Jina.ai Content Extraction

## Current Usage

Jina.ai is currently used for:
- Webpage content extraction via their API endpoint (`https://r.jina.ai/`)
- Converting HTML content to clean, readable text
- Handling various webpage formats and encodings
- Managing request headers and authentication

## Migration Strategy

### Phase 1: Setup Content Extraction Stack

1. **Core Dependencies**
```python
# Add to requirements.txt
beautifulsoup4==4.12.3
requests==2.31.0
trafilatura==1.6.4
newspaper3k==0.2.8
html2text==2020.1.16
```

2. **Create Content Extractor Module**
- Create `app/content_extractor.py`
- Implement multiple extraction methods for redundancy
- Handle various content types and encodings

### Phase 2: Implementation

1. **Base Extractor Class**
```python
from abc import ABC, abstractmethod
from typing import Optional
import aiohttp
import trafilatura
from bs4 import BeautifulSoup
from newspaper import Article
import html2text

class ContentExtractor(ABC):
    @abstractmethod
    async def extract(self, url: str) -> Optional[str]:
        pass

class TrafilaturaExtractor(ContentExtractor):
    async def extract(self, url: str) -> Optional[str]:
        try:
            downloaded = trafilatura.fetch_url(url)
            return trafilatura.extract(downloaded)
        except Exception:
            return None

class NewspaperExtractor(ContentExtractor):
    async def extract(self, url: str) -> Optional[str]:
        try:
            article = Article(url)
            article.download()
            article.parse()
            return article.text
        except Exception:
            return None

class BeautifulSoupExtractor(ContentExtractor):
    async def extract(self, url: str) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    # Remove unwanted elements
                    for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()
                    return soup.get_text(separator='\n', strip=True)
        except Exception:
            return None
```

2. **Main Extractor Service**
```python
class ContentExtractorService:
    def __init__(self):
        self.extractors = [
            TrafilaturaExtractor(),
            NewspaperExtractor(),
            BeautifulSoupExtractor()
        ]
    
    async def extract_content(self, url: str) -> Optional[str]:
        """Try multiple extractors in sequence until successful."""
        for extractor in self.extractors:
            try:
                if content := await extractor.extract(url):
                    return self._clean_content(content)
            except Exception:
                continue
        return None
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize extracted content."""
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = ' '.join(content.split())
        
        # Remove very short lines
        lines = [line for line in content.split('\n') if len(line.strip()) > 30]
        
        # Rejoin with proper spacing
        return '\n\n'.join(lines)
```

### Phase 3: Integration

1. **Update ResearchEngine**
```python
class ResearchEngine:
    def __init__(self, config):
        self.content_extractor = ContentExtractorService()
    
    async def fetch_webpage_text(self, session: aiohttp.ClientSession, url: str) -> str:
        try:
            content = await self.content_extractor.extract_content(url)
            if content:
                return content
            logger.warning(f"No content extracted from {url}")
            return ""
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return ""
```

2. **Update Configuration**
- Remove Jina.ai related settings and environment variables
- Add any new configuration options for content extraction

### Phase 4: Testing

1. **Unit Tests**
- Test each extractor individually
- Test fallback behavior
- Test content cleaning and normalization
- Test various webpage formats

2. **Integration Tests**
- Test the complete research flow
- Compare results with Jina.ai
- Measure performance and reliability

3. **Performance Tests**
- Benchmark extraction speed
- Monitor memory usage
- Test concurrent extractions

### Phase 5: Deployment

1. **Gradual Rollout**
- Deploy to staging environment
- Run both systems in parallel
- Compare results and performance
- Monitor error rates

2. **Monitoring Setup**
- Add metrics for extraction success rates
- Track extraction times
- Monitor memory usage
- Set up alerts for failures

3. **Documentation**
- Update API documentation
- Document new configuration options
- Add troubleshooting guides
- Update architecture diagrams

## Benefits

1. **Independence**
- No reliance on external service
- Full control over extraction logic
- Customizable content processing

2. **Cost Savings**
- Eliminate Jina.ai API costs
- Scale based on our needs

3. **Performance**
- Reduce network latency
- Optimize for our use cases
- Better error handling

4. **Features**
- Custom content cleaning rules
- Better handling of specific sites
- Flexible extraction strategies

## Timeline

1. Phase 1: 1 week
2. Phase 2: 2 weeks
3. Phase 3: 1 week
4. Phase 4: 2 weeks
5. Phase 5: 1 week

Total estimated time: 7 weeks

## Risks and Mitigation

1. **Content Quality**
- Risk: Lower quality extraction compared to Jina.ai
- Mitigation: Multiple extraction methods, extensive testing

2. **Performance**
- Risk: Slower extraction times
- Mitigation: Caching, optimization, parallel processing

3. **Maintenance**
- Risk: Increased maintenance burden
- Mitigation: Good documentation, monitoring, automated tests

4. **Site Compatibility**
- Risk: Some sites may be harder to extract
- Mitigation: Multiple fallback methods, site-specific handlers

## Success Metrics

1. **Extraction Quality**
- Content completeness
- Text cleaning accuracy
- Format preservation

2. **Performance**
- Extraction speed
- Success rate
- Error rate

3. **Resource Usage**
- CPU utilization
- Memory consumption
- Network bandwidth

## Rollback Plan

1. Keep Jina.ai integration in codebase
2. Maintain ability to switch providers
3. Monitor error rates for automatic rollback
4. Keep old configuration options 