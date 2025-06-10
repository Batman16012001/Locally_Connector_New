from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.routers import ingest, jobs
from app.config.database import Database
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.connect_db()
    yield
    await Database.close_db()

app = FastAPI(
    title="Locally Data Connector",
    description="API for ingesting data from various sources into MongoDB",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
limiter = Limiter(key_func=lambda: "global")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(ingest.router, prefix="/api/v1", tags=["ingestion"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])


@app.get("/")
async def root():
    return {"message": "Welcome to Locally Data Connector API"} 