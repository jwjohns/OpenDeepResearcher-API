from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import nest_asyncio
import logging
from .researcher import ResearchEngine
from .config import Settings

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
    openrouter_api_key=settings.openrouter_api_key,
    serpapi_api_key=settings.serpapi_api_key,
    jina_api_key=settings.jina_api_key
)
logger.info("Initialized ResearchEngine")

class ResearchRequest(BaseModel):
    query: str
    max_iterations: Optional[int] = 10

class ResearchResponse(BaseModel):
    report: str
    logs: List[str]

@app.post("/api/research", response_model=ResearchResponse)
async def perform_research(request: ResearchRequest):
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