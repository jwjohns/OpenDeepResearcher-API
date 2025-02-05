import asyncio
import aiohttp
from typing import List, Tuple, Dict, Optional
import json
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResearchEngine:
    def __init__(
        self,
        openrouter_api_key: str,
        serpapi_api_key: str,
        jina_api_key: str,
        model: str = "meta-llama/llama-3-8b-instruct:free"
    ):
        self.openrouter_api_key = openrouter_api_key
        self.serpapi_api_key = serpapi_api_key
        self.jina_api_key = jina_api_key
        self.model = model
        
        # API endpoints
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.serpapi_url = "https://serpapi.com/search"
        self.jina_base_url = "https://r.jina.ai/"
        
        logger.info(f"ResearchEngine initialized with model: {model}")
        
    async def call_openrouter(self, session: aiohttp.ClientSession, messages: List[Dict[str, str]]) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": "https://github.com/yourusername/OpenDeepResearcher",
            "X-Title": "OpenDeepResearcher API",
            "Content-Type": "application/json"
        }
        
        try:
            logger.debug(f"Calling OpenRouter with model {self.model}")
            logger.debug(f"Request messages: {messages}")
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            async with session.post(
                self.openrouter_url,
                headers=headers,
                json=payload
            ) as resp:
                response_text = await resp.text()
                logger.debug(f"OpenRouter raw response: {response_text}")
                
                if resp.status == 200:
                    data = json.loads(response_text)
                    content = data["choices"][0]["message"]["content"]
                    logger.debug(f"OpenRouter API call successful, content: {content}")
                    return content
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

    def _clean_llm_response(self, response: str) -> str:
        """Clean the LLM response by removing code blocks and other formatting."""
        if response is None:
            return ""
        # Remove code block markers
        response = response.replace("```python", "").replace("```", "")
        # Remove leading/trailing whitespace
        response = response.strip()
        return response

    async def generate_search_queries(self, session: aiohttp.ClientSession, user_query: str) -> List[str]:
        prompt = (
            "Generate exactly 4 search queries as a Python list of strings.\n"
            "RESPOND WITH ONLY THE LIST, NO OTHER TEXT.\n"
            "Each query should focus on a different aspect.\n"
            "Format: ['query 1', 'query 2', 'query 3', 'query 4']\n"
            f"Topic: {user_query}"
        )
        messages = [
            {
                "role": "system", 
                "content": "You are a search query generator. Respond with ONLY a Python list of strings, no other text."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        logger.info(f"Generating search queries for: {user_query}")
        response = await self.call_openrouter(session, messages)
        if response:
            try:
                # More aggressive cleaning to remove any explanatory text
                cleaned_response = self._clean_llm_response(response)
                # Find the first [ and last ] to extract just the list
                start = cleaned_response.find('[')
                end = cleaned_response.rfind(']') + 1
                if start != -1 and end != 0:
                    list_str = cleaned_response[start:end]
                    logger.debug(f"Extracted list string: {list_str}")
                    queries = eval(list_str)
                    if isinstance(queries, list):
                        if len(queries) > 0 and all(isinstance(q, str) for q in queries):
                            logger.info(f"Generated queries: {queries}")
                            return queries[:4]  # Ensure we only return 4 queries
                        else:
                            logger.warning("Generated empty list or invalid query types")
                    else:
                        logger.warning(f"Response was not a list: {type(queries)}")
                else:
                    logger.warning("Could not find list brackets in response")
            except Exception as e:
                logger.error(f"Error parsing search queries: {str(e)}", exc_info=True)
        logger.warning("Failed to generate search queries")
        return []

    async def perform_search(self, session: aiohttp.ClientSession, query: str) -> List[str]:
        params = {
            "api_key": self.serpapi_api_key,
            "q": query,
            "num": 10
        }
        
        try:
            logger.info(f"Performing SERPAPI search for query: {query}")
            async with session.get(self.serpapi_url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    organic_results = data.get("organic_results", [])
                    links = [result["link"] for result in organic_results if "link" in result]
                    logger.info(f"Found {len(links)} results from SERPAPI")
                    logger.debug(f"Search results: {links}")
                    return links
                else:
                    logger.error(f"SERPAPI error: {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Error performing SERPAPI search: {str(e)}", exc_info=True)
            return []

    async def fetch_webpage_text(self, session: aiohttp.ClientSession, url: str) -> str:
        headers = {"Authorization": f"Bearer {self.jina_api_key}"}
        try:
            logger.info(f"Fetching webpage content from: {url}")
            async with session.get(f"{self.jina_base_url}{url}", headers=headers) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    logger.debug(f"Successfully fetched content from {url} (first 100 chars): {content[:100]}")
                    return content
                else:
                    logger.error(f"Jina fetch error for {url}: {resp.status}")
                    return ""
        except Exception as e:
            logger.error(f"Error fetching webpage text from {url}: {str(e)}", exc_info=True)
            return ""

    async def is_page_useful(self, session: aiohttp.ClientSession, user_query: str, page_text: str) -> str:
        prompt = (
            "Is this content relevant to the topic? "
            "Answer with exactly 'Yes' or 'No'."
        )
        messages = [
            {"role": "system", "content": "You are a content relevance evaluator. Be direct."},
            {"role": "user", "content": f"Topic: {user_query}\n\nContent:\n{page_text[:2000]}\n\n{prompt}"}
        ]
        
        logger.info("Evaluating page usefulness")
        response = await self.call_openrouter(session, messages)
        if response:
            answer = self._clean_llm_response(response)
            logger.info(f"Page usefulness evaluation result: {answer}")
            if answer in ["Yes", "No"]:
                return answer
            elif "Yes" in answer.upper():
                return "Yes"
            elif "No" in answer.upper():
                return "No"
        logger.warning("Failed to evaluate page usefulness, defaulting to No")
        return "No"

    async def extract_relevant_context(
        self,
        session: aiohttp.ClientSession,
        user_query: str,
        search_query: str,
        page_text: str
    ) -> Optional[str]:
        prompt = (
            "Extract all information relevant to answering the user's query. "
            "Return only the relevant context as plain text without commentary."
        )
        messages = [
            {"role": "system", "content": "You are an expert information extractor."},
            {
                "role": "user",
                "content": f"Query: {user_query}\nSearch Query: {search_query}\n\n"
                          f"Content:\n{page_text[:20000]}\n\n{prompt}"
            }
        ]
        
        logger.info("Extracting relevant context from webpage")
        response = await self.call_openrouter(session, messages)
        if response:
            context = response.strip()
            logger.debug(f"Extracted context (first 100 chars): {context[:100]}")
            return context
        logger.warning("Failed to extract context")
        return None

    async def get_new_search_queries(
        self,
        session: aiohttp.ClientSession,
        user_query: str,
        previous_queries: List[str],
        contexts: List[str]
    ) -> Optional[List[str]]:
        context_combined = "\n".join(contexts)
        prompt = (
            "Based on the gathered information, either:\n"
            "1. Return a Python list of new search queries if more research is needed\n"
            "2. Return exactly '<done>' if enough information is gathered\n"
            "Format: ['query1', 'query2'] or '<done>'"
        )
        messages = [
            {"role": "system", "content": "You are a research planner. Be concise and direct."},
            {
                "role": "user",
                "content": f"Topic: {user_query}\nPrevious Searches: {previous_queries}\n\n"
                          f"Current Information:\n{context_combined}\n\n{prompt}"
            }
        ]
        
        logger.info("Checking if more research queries are needed")
        response = await self.call_openrouter(session, messages)
        if response:
            cleaned = self._clean_llm_response(response)
            logger.debug(f"Response for new queries: {cleaned}")
            if cleaned == "<done>":
                logger.info("Research complete signal received")
                return None
            try:
                queries = eval(cleaned)
                if isinstance(queries, list) and len(queries) > 0:
                    logger.info(f"Generated new queries: {queries}")
                    return queries
                else:
                    logger.warning("Invalid queries format or empty list")
            except Exception as e:
                logger.error(f"Error parsing new search queries: {str(e)}", exc_info=True)
        logger.warning("Failed to generate new search queries")
        return []

    async def generate_final_report(
        self,
        session: aiohttp.ClientSession,
        user_query: str,
        contexts: List[str]
    ) -> str:
        context_combined = "\n".join(contexts)
        prompt = (
            "Write a complete, well-structured, and detailed report that addresses "
            "the query thoroughly. Include all useful insights without commentary."
        )
        messages = [
            {"role": "system", "content": "You are an expert report writer."},
            {
                "role": "user",
                "content": f"Query: {user_query}\n\nContexts:\n{context_combined}\n\n{prompt}"
            }
        ]
        
        response = await self.call_openrouter(session, messages)
        return response if response else "Unable to generate report."

    async def save_research_to_markdown(self, query: str, report: str, logs: List[str], filename: str = None) -> str:
        """Save the research results to a markdown file."""
        if filename is None:
            # Create filename from query
            safe_query = "".join(c if c.isalnum() else "_" for c in query[:30]).lower()
            filename = f"research_{safe_query}_{int(asyncio.get_event_loop().time())}.md"
        
        # Create logs section
        logs_section = ""
        for log in logs:
            logs_section += f"{log}\n"
        
        content = f"""# Research Results

## Query
"{query}"

## Research Report
{report}

## Process Logs
```
{logs_section}```

## Generated On
{asyncio.get_event_loop().time()}

*This report was automatically generated using OpenDeepResearcher.*
"""
        
        try:
            # Ensure the research_outputs directory exists
            os.makedirs("research_outputs", exist_ok=True)
            filepath = os.path.join("research_outputs", filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"Research saved to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving research to markdown: {str(e)}", exc_info=True)
            return ""

    async def research(self, user_query: str, max_iterations: int = 10) -> Tuple[str, List[str]]:
        logs = []
        contexts = []
        all_queries = []
        
        logger.info(f"Starting research for query: {user_query} (max iterations: {max_iterations})")
        async with aiohttp.ClientSession() as session:
            # Generate initial queries
            logs.append("Generating initial search queries...")
            queries = await self.generate_search_queries(session, user_query)
            if not queries:
                message = "OpenRouter API rate limit exceeded. Please try again later or upgrade to a paid plan."
                logger.error(message)
                logs.append(message)
                return f"Research failed: {message}", logs
            
            all_queries.extend(queries)
            logs.append(f"Initial queries: {queries}")
            logger.info(f"Generated {len(queries)} initial queries")
            
            # Iterative research loop
            for iteration in range(max_iterations):
                iteration_message = f"\n=== Iteration {iteration + 1} ==="
                logs.append(iteration_message)
                logger.info(iteration_message)
                
                # Perform searches
                logger.info("Executing search queries in parallel")
                search_tasks = [self.perform_search(session, q) for q in queries]
                search_results = await asyncio.gather(*search_tasks)
                
                # Process unique links
                unique_links = {}
                for idx, links in enumerate(search_results):
                    query_used = queries[idx]
                    for link in links:
                        if link not in unique_links:
                            unique_links[link] = query_used
                
                log_message = f"Found {len(unique_links)} unique links."
                logs.append(log_message)
                logger.info(log_message)
                
                # Process each link
                iteration_contexts = []
                for link, search_query in unique_links.items():
                    logs.append(f"Processing: {link}")
                    logger.info(f"Processing link: {link}")
                    
                    # Fetch and evaluate content
                    content = await self.fetch_webpage_text(session, link)
                    if not content:
                        logger.warning(f"No content retrieved from {link}")
                        continue
                    
                    usefulness = await self.is_page_useful(session, user_query, content)
                    logs.append(f"Page usefulness: {usefulness}")
                    
                    if usefulness == "Yes":
                        if context := await self.extract_relevant_context(session, user_query, search_query, content):
                            iteration_contexts.append(context)
                            preview = f"Extracted context (preview): {context[:100]}..."
                            logs.append(preview)
                            logger.debug(preview)
                
                if iteration_contexts:
                    contexts.extend(iteration_contexts)
                    log_message = f"Added {len(iteration_contexts)} new contexts."
                    logs.append(log_message)
                    logger.info(log_message)
                else:
                    log_message = "No useful contexts found in this iteration."
                    logs.append(log_message)
                    logger.warning(log_message)
                
                # Check if more research is needed
                queries = await self.get_new_search_queries(session, user_query, all_queries, contexts)
                if not queries:
                    log_message = "No more queries needed. Generating report..."
                    logs.append(log_message)
                    logger.info(log_message)
                    break
                
                all_queries.extend(queries)
                log_message = f"New queries for next iteration: {queries}"
                logs.append(log_message)
                logger.info(log_message)
            
            # Generate final report
            logger.info("Generating final research report")
            report = await self.generate_final_report(session, user_query, contexts)
            
            # Save research to markdown
            await self.save_research_to_markdown(user_query, report, logs)
            
            logger.info("Research completed successfully")
            return report, logs 