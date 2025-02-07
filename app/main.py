from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import nest_asyncio
import logging
import json
from .researcher import ResearchEngine
from .config import Settings
import aiohttp
from .llm_providers import OpenAIProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Initialize FastAPI app
app = FastAPI(
    title="OpenDeepResearcher API",
    description="An AI-powered research assistant that performs deep research on any topic",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load settings
settings = Settings()
logger.info("Loaded application settings")

# Initialize research engine
research_engine = ResearchEngine(
    jina_api_key=settings.jina_api_key,
    config=settings
)
logger.info("Initialized ResearchEngine")

class ResearchRequest(BaseModel):
    query: str
    max_iterations: Optional[int] = 10

class ResearchResponse(BaseModel):
    report: str
    logs: List[str]

class LLMConfig(BaseModel):
    provider: str
    model: Optional[str] = None

class LLMConfigResponse(BaseModel):
    current_provider: str
    current_model: str
    available_providers: List[dict]
    available_models: dict

async def research_status_generator(request: ResearchRequest):
    """Generate SSE events for research status updates."""
    try:
        # Create a queue for status updates
        status_queue = asyncio.Queue()
        
        # Start research process in background
        research_task = asyncio.create_task(
            research_engine.research(
                request.query,
                request.max_iterations,
                status_queue=status_queue
            )
        )
        
        # Stream status updates
        while True:
            try:
                # Get status update from queue
                status = await status_queue.get()
                
                # Check if research is complete
                if status.get("type") == "complete":
                    report = status.get("report", "")
                    logs = status.get("logs", [])
                    yield f"data: {json.dumps({'type': 'complete', 'report': report, 'logs': logs})}\n\n"
                    break
                
                # Send status update
                yield f"data: {json.dumps(status)}\n\n"
                
            except asyncio.CancelledError:
                research_task.cancel()
                yield f"data: {json.dumps({'type': 'error', 'message': 'Research cancelled'})}\n\n"
                break
            
    except Exception as e:
        logger.error(f"Error during research: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@app.post("/api/research/stream")
async def stream_research(request: ResearchRequest):
    """Stream research progress using Server-Sent Events."""
    return StreamingResponse(
        research_status_generator(request),
        media_type="text/event-stream"
    )

@app.post("/api/research", response_model=ResearchResponse)
async def perform_research(request: ResearchRequest):
    """Traditional synchronous research endpoint."""
    logger.info(f"Received research request: {request.query} (max_iterations: {request.max_iterations})")
    try:
        report, logs = await research_engine.research(
            request.query,
            request.max_iterations
        )
        logger.info("Research completed successfully")
        logger.debug(f"Research logs: {logs}")
        return ResearchResponse(report=report, logs=logs)
    except Exception as e:
        logger.error(f"Error during research: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    logger.debug("Health check requested")
    return {"status": "healthy"}

@app.get("/api/config/llm", response_model=LLMConfigResponse)
async def get_llm_config():
    """Get current LLM configuration and available options."""
    available_providers = [
        {"id": "openai", "name": "OpenAI", "available": bool(settings.openai_api_key)},
        {"id": "anthropic", "name": "Anthropic", "available": bool(settings.anthropic_api_key)},
        {"id": "openrouter", "name": "OpenRouter", "available": bool(settings.openrouter_api_key)},
        {"id": "ollama", "name": "Ollama", "available": True}  # Always available locally
    ]
    
    # Initialize default models
    available_models = {
        "anthropic": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"],
        "openrouter": ["meta-llama/llama-3-8b-instruct:free", "anthropic/claude-3-haiku", "google/gemini-pro"],
        "ollama": ["llama2", "mistral", "gemma"]
    }
    
    # Fetch OpenAI models if API key is available
    if settings.openai_api_key:
        async with aiohttp.ClientSession() as session:
            openai_provider = research_engine.llm_provider
            if isinstance(openai_provider, OpenAIProvider):
                available_models["openai"] = await openai_provider.list_available_models(session)
            else:
                available_models["openai"] = []  # Empty list if not using OpenAI
    else:
        available_models["openai"] = []
    
    return LLMConfigResponse(
        current_provider=settings.llm_provider,
        current_model=getattr(settings, f"{settings.llm_provider}_model", None),
        available_providers=available_providers,
        available_models=available_models
    )

@app.post("/api/config/llm")
async def update_llm_config(config: LLMConfig):
    """Update LLM configuration."""
    # Validate provider is available
    if config.provider == "openai" and not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
    elif config.provider == "anthropic" and not settings.anthropic_api_key:
        raise HTTPException(status_code=400, detail="Anthropic API key not configured")
    elif config.provider == "openrouter" and not settings.openrouter_api_key:
        raise HTTPException(status_code=400, detail="OpenRouter API key not configured")
    
    # Update the configuration
    settings.llm_provider = config.provider
    if config.model:
        setattr(settings, f"{config.provider}_model", config.model)
    
    # Reinitialize the research engine with new settings
    global research_engine
    research_engine = ResearchEngine(
        jina_api_key=settings.jina_api_key,
        config=settings
    )
    
    return {"status": "success", "message": "LLM configuration updated"} 