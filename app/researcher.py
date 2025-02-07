import asyncio
import aiohttp
from typing import List, Tuple, Dict, Optional
import json
import logging
import os
from .llm_providers import get_llm_provider, LLMProvider
from .search_providers import get_search_provider

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResearchEngine:
    def __init__(
        self,
        jina_api_key: str,
        config
    ):
        self.jina_api_key = jina_api_key
        
        # Initialize providers
        self.llm_provider = get_llm_provider(config)
        self.search_provider = get_search_provider(config)
        
        # API endpoints
        self.jina_base_url = "https://r.jina.ai/"
        
        logger.info(f"ResearchEngine initialized with LLM provider: {config.llm_provider}")
        logger.info(f"Using search provider: {config.search_provider}")
        
    async def call_llm(self, session: aiohttp.ClientSession, messages: List[Dict[str, str]]) -> Optional[str]:
        """Call the LLM provider with the given messages."""
        try:
            logger.debug(f"Calling LLM provider with messages: {messages}")
            response = await self.llm_provider.generate_completion(session, messages)
            if response:
                logger.debug(f"LLM response: {response}")
                return response
            else:
                logger.error("LLM provider returned None")
                return None
        except Exception as e:
            logger.error(f"Error calling LLM provider: {str(e)}", exc_info=True)
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
            "You are an expert research assistant. Given the user's query, generate up to four distinct, "
            "precise search queries that would help gather comprehensive information on the topic. "
            "Return only a Python list of strings, for example: ['query1', 'query2', 'query3']."
        )
        messages = [
            {"role": "system", "content": "You are a helpful and precise research assistant."},
            {"role": "user", "content": f"User Query: {user_query}\n\n{prompt}"}
        ]
        
        logger.info(f"Generating search queries for: {user_query}")
        response = await self.call_llm(session, messages)
        if response:
            try:
                cleaned_response = self._clean_llm_response(response)
                start = cleaned_response.find('[')
                end = cleaned_response.rfind(']') + 1
                if start != -1 and end != 0:
                    list_str = cleaned_response[start:end]
                    logger.debug(f"Extracted list string: {list_str}")
                    queries = eval(list_str)
                    if isinstance(queries, list):
                        if len(queries) > 0 and all(isinstance(q, str) for q in queries):
                            logger.info(f"Generated queries: {queries}")
                            return queries[:4]
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
        return await self.search_provider.search(session, query)

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
            "You are a critical research evaluator. Given the user's query and the content of a webpage, "
            "determine if the webpage contains information relevant and useful for addressing the query. "
            "Respond with exactly one word: 'Yes' if the page is useful, or 'No' if it is not. Do not include any extra text."
        )
        messages = [
            {"role": "system", "content": "You are a strict and concise evaluator of research relevance."},
            {"role": "user", "content": f"User Query: {user_query}\n\nWebpage Content (first 20000 characters):\n{page_text[:20000]}\n\n{prompt}"}
        ]
        
        logger.info("Evaluating page usefulness")
        response = await self.call_llm(session, messages)
        if response:
            answer = self._clean_llm_response(response).strip()
            logger.info(f"Page usefulness evaluation result: {response}")
            
            if answer in ["Yes", "No"]:
                return answer
            elif "yes" in answer.lower():
                return "Yes"
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
            "You are an expert information extractor. Given the user's query, the search query that led to this page, "
            "and the webpage content, extract all pieces of information that are relevant to answering the user's query. "
            "Return only the relevant context as plain text without commentary."
        )
        messages = [
            {"role": "system", "content": "You are an expert in extracting and summarizing relevant information."},
            {
                "role": "user",
                "content": f"User Query: {user_query}\nSearch Query: {search_query}\n\n"
                          f"Webpage Content (first 20000 characters):\n{page_text[:20000]}\n\n{prompt}"
            }
        ]
        
        logger.info("Extracting relevant context from webpage")
        response = await self.call_llm(session, messages)
        if response:
            context = response.strip()
            if context:
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
            "You are an analytical research assistant. Based on the original query, the search queries performed so far, "
            "and the extracted contexts from webpages, determine if further research is needed. "
            "If further research is needed, provide up to four new search queries as a Python list (for example, "
            "['new query1', 'new query2']). If you believe no further research is needed, respond with exactly ."
            "\nOutput only a Python list or the token  without any additional text."
        )
        messages = [
            {"role": "system", "content": "You are a systematic research planner."},
            {
                "role": "user",
                "content": f"User Query: {user_query}\nPrevious Search Queries: {previous_queries}\n\n"
                          f"Extracted Relevant Contexts:\n{context_combined}\n\n{prompt}"
            }
        ]
        
        logger.info("Checking if more research queries are needed")
        response = await self.call_llm(session, messages)
        if response:
            cleaned = self._clean_llm_response(response)
            logger.debug(f"Response for new queries: {cleaned}")
            if cleaned == "":
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
        if not contexts or not any(ctx.strip() for ctx in contexts):
            return "I couldn't find enough relevant information to answer your question. Please try rephrasing or being more specific."

        context_combined = "\n".join(contexts)
        prompt = (
            "You are an expert researcher and report writer. Based on the gathered contexts below and the original query, "
            "write a comprehensive, well-structured, and detailed report that addresses the query thoroughly. "
            "Include all relevant insights and conclusions without extraneous commentary."
        )
        messages = [
            {"role": "system", "content": "You are a skilled report writer."},
            {
                "role": "user",
                "content": f"User Query: {user_query}\n\nGathered Relevant Contexts:\n{context_combined}\n\n{prompt}"
            }
        ]
        
        response = await self.call_llm(session, messages)
        if not response:
            return "Error analyzing research data. Please try again."
            
        # Add methodology note
        methodology = f"\n\nMethodology: Research conducted to answer '{user_query}' using systematic search and synthesis of findings."
        
        return response + methodology

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

*This report was automatically generated using OpenDeepResearcher-API.*
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

    async def research(
        self,
        user_query: str,
        max_iterations: int = 10,
        status_queue: Optional[asyncio.Queue] = None
    ) -> Tuple[str, List[str]]:
        logs = []
        contexts = []
        all_queries = []
        
        async def send_status(status_type: str, message: str, **kwargs):
            if status_queue:
                await status_queue.put({
                    "type": status_type,
                    "message": message,
                    **kwargs
                })
            logs.append(message)
            logger.info(message)
        
        logger.info(f"Starting research for query: {user_query} (max iterations: {max_iterations})")
        await send_status("start", f"Starting research: {user_query}")
        
        async with aiohttp.ClientSession() as session:
            # Generate initial queries
            await send_status("progress", "Generating initial search queries...")
            queries = await self.generate_search_queries(session, user_query)
            if not queries:
                message = "LLM provider rate limit exceeded. Please try again later or upgrade to a paid plan."
                await send_status("error", message)
                return f"Research failed: {message}", logs
            
            all_queries.extend(queries)
            await send_status("queries", "Generated initial queries", queries=queries)
            
            # Iterative research loop
            for iteration in range(max_iterations):
                iteration_message = f"\n=== Iteration {iteration + 1} ==="
                await send_status("iteration", iteration_message, iteration=iteration + 1)
                
                # Perform searches
                await send_status("progress", "Executing search queries in parallel")
                search_tasks = [self.perform_search(session, q) for q in queries]
                search_results = await asyncio.gather(*search_tasks)
                
                # Process unique links
                unique_links = {}
                for idx, links in enumerate(search_results):
                    query_used = queries[idx]
                    for link in links:
                        if link not in unique_links:
                            unique_links[link] = query_used
                
                await send_status("links", f"Found {len(unique_links)} unique links", count=len(unique_links))
                
                # Process each link
                iteration_contexts = []
                for link, search_query in unique_links.items():
                    await send_status("processing", f"Processing: {link}", url=link)
                    
                    # Fetch and evaluate content
                    content = await self.fetch_webpage_text(session, link)
                    if not content:
                        await send_status("warning", f"No content retrieved from {link}")
                        continue
                    
                    usefulness = await self.is_page_useful(session, user_query, content)
                    await send_status("evaluation", f"Page usefulness: {usefulness}", url=link, useful=usefulness=="Yes")
                    
                    if usefulness == "Yes":
                        if context := await self.extract_relevant_context(session, user_query, search_query, content):
                            iteration_contexts.append(context)
                            preview = f"Extracted context (preview): {context[:100]}..."
                            await send_status("context", preview, url=link)
                
                if iteration_contexts:
                    contexts.extend(iteration_contexts)
                    await send_status("progress", f"Added {len(iteration_contexts)} new contexts", count=len(iteration_contexts))
                else:
                    await send_status("warning", "No useful contexts found in this iteration")
                
                # Check if more research is needed
                queries = await self.get_new_search_queries(session, user_query, all_queries, contexts)
                if not queries:
                    await send_status("progress", "No more queries needed. Generating report...")
                    break
                
                all_queries.extend(queries)
                await send_status("queries", "New queries for next iteration", queries=queries)
            
            # Generate final report
            await send_status("progress", "Generating final research report")
            report = await self.generate_final_report(session, user_query, contexts)
            
            # Save research to markdown
            await self.save_research_to_markdown(user_query, report, logs)
            
            logger.info("Research completed successfully")
            if status_queue:
                await status_queue.put({
                    "type": "complete",
                    "message": "Research completed successfully",
                    "report": report,
                    "logs": logs
                })
            
            return report, logs 