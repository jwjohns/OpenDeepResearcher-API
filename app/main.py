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
    serpapi_api_key=settings.serpapi_api_key,
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