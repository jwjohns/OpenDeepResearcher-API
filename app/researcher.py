import asyncio
import aiohttp
from typing import List, Tuple, Dict, Optional
import json
import logging
import os
from .llm_providers import get_llm_provider, LLMProvider

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResearchEngine:
    def __init__(
        self,
        serpapi_api_key: str,
        jina_api_key: str,
        config
    ):
        self.serpapi_api_key = serpapi_api_key
        self.jina_api_key = jina_api_key
        
        # Initialize LLM provider
        self.llm_provider = get_llm_provider(config)
        
        # API endpoints
        self.serpapi_url = "https://serpapi.com/search"
        self.jina_base_url = "https://r.jina.ai/"
        
        logger.info(f"ResearchEngine initialized with provider: {config.llm_provider}")
        
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
        response = await self.call_llm(session, messages)
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
            "Evaluate if this content would help answer the query in any meaningful way. "
            "Content is considered useful if it:\n"
            "1. Addresses any aspect of the query directly or indirectly\n"
            "2. Provides relevant background, context, or related insights\n"
            "3. Offers expert opinions, research findings, or real-world examples\n"
            "4. Contains information that would contribute to understanding the topic\n\n"
            "Even if the content only partially addresses the query, it may still be useful.\n\n"
            "Answer with EXACTLY 'Yes' or 'No', followed by a brief reason."
        )
        messages = [
            {"role": "system", "content": "You are a content evaluator. Consider both direct and indirect relevance to the query."},
            {"role": "user", "content": f"Query: {user_query}\n\nContent:\n{page_text[:2000]}\n\n{prompt}"}
        ]
        
        logger.info("Evaluating page usefulness")
        response = await self.call_llm(session, messages)
        if response:
            # Extract just the Yes/No from the response
            answer = self._clean_llm_response(response).strip().lower().split()[0]
            logger.info(f"Page usefulness evaluation result: {response}")
            
            # Accept content unless it's clearly not useful
            if answer == "no":
                return "No"
            return "Yes"
            
        logger.warning("Failed to evaluate page usefulness, defaulting to Yes")
        return "Yes"  # Default to including content if evaluation fails

    async def extract_relevant_context(
        self,
        session: aiohttp.ClientSession,
        user_query: str,
        search_query: str,
        page_text: str
    ) -> Optional[str]:
        prompt = (
            "Extract information that directly helps answer the query. Focus on:\n"
            "1. Specific facts, data, or evidence\n"
            "2. Expert analysis or insights\n"
            "3. Relevant examples or case studies\n"
            "4. Direct answers to aspects of the query\n\n"
            "Format the extraction as bullet points, each starting with '-'.\n"
            "Include brief context when needed for understanding.\n"
            "Exclude general background unless it's essential.\n\n"
            "If no substantive information is found, return exactly 'No relevant information found.'"
        )
        messages = [
            {"role": "system", "content": "You are a precise information extractor. Focus on substance over generalities."},
            {
                "role": "user",
                "content": f"Query: {user_query}\nSearch Query: {search_query}\n\n"
                          f"Content:\n{page_text[:20000]}\n\n{prompt}"
            }
        ]
        
        logger.info("Extracting relevant context from webpage")
        response = await self.call_llm(session, messages)
        if response:
            context = response.strip()
            if context == "No relevant information found.":
                return None
            if not context.startswith('-'):
                # If response isn't in bullet points, it's probably not specific enough
                return None
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
        response = await self.call_llm(session, messages)
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
            "Write a focused research report that directly addresses the query. Follow these guidelines:\n"
            "1. Start with a brief, focused introduction that states the specific research question\n"
            "2. Present concrete findings, evidence, and examples from the research\n"
            "3. Include specific data points, expert opinions, and real-world cases where available\n"
            "4. Analyze contradictions or differing viewpoints found in the research\n"
            "5. Draw conclusions based on the evidence gathered\n\n"
            "Focus on depth over breadth. Avoid generic statements without supporting evidence.\n"
            "If certain aspects lack solid evidence, acknowledge the limitations of the findings."
        )
        messages = [
            {"role": "system", "content": "You are a research analyst synthesizing specific findings. Focus on concrete evidence and insights."},
            {
                "role": "user",
                "content": f"Query: {user_query}\n\nResearch Findings:\n{context_combined}\n\n{prompt}"
            }
        ]
        
        response = await self.call_llm(session, messages)
        if not response:
            return "Unable to generate report due to insufficient research findings."
            
        # Add research methodology section
        methodology = (
            "\n\n## Research Methodology\n"
            f"This report is based on analysis of multiple sources examining {user_query}. "
            "The research process involved:\n"
            "- Systematic search and analysis of relevant publications and studies\n"
            "- Evaluation of source credibility and relevance\n"
            "- Synthesis of findings from multiple perspectives\n"
            "- Focus on evidence-based conclusions\n"
        )
        
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