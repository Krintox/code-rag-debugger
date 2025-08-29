from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from routers import projects, debug, history, references

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Code Evolution Tracker & Debugger with RAG",
    version="1.0.0",
    lifespan=lifespan
)

# FIXED CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rodeceview.vercel.app", "http://localhost:3000"],  # Your React frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(projects.router)
app.include_router(debug.router)
app.include_router(history.router)
app.include_router(references.router)

@app.get("/")
async def root():
    return {"message": "Code Evolution Tracker & Debugger API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)