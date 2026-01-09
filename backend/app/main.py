"""FastAPI main application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.database import init_db
from app.api import upload, status, result
from app.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting AI Exam Evaluator Backend")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Log configuration
    logger.info(f"OCR API configured")
    logger.info(f"Ollama host: {Config.get_ollama_host()}")
    logger.info(f"Mapping model: {Config.get_model('mapping')}")
    logger.info(f"Evaluation model: {Config.get_model('evaluation')}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Exam Evaluator Backend")

# Create FastAPI app
app = FastAPI(
    title="AI Exam Evaluator",
    description="Production-ready AI-based exam evaluation system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(status.router)
app.include_router(result.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Exam Evaluator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "upload": "/api/upload",
            "status": "/api/status/{job_id}",
            "result": "/api/result/{job_id}",
            "download": "/api/result/{job_id}/download"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ollama_host": Config.get_ollama_host(),
        "models": {
            "mapping": Config.get_model('mapping'),
            "evaluation": Config.get_model('evaluation')
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    host = Config.get('server.host', '0.0.0.0')
    port = Config.get('server.port', 8000)
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True
    )
