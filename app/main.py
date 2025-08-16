import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
from fastapi.responses import JSONResponse
import asyncio
import time
from functools import lru_cache
import hashlib
import json

from app.api.v1 import verification, news
from app.core.config import settings

# Initialize app
app = FastAPI(
    title="Veritas - Fake News & Claim Verification API",
    description="A modular, multi-source truth verification system",
    version="1.0.0"
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.info("Starting Veritas system...")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update to specific domains for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(
    verification.router,
    prefix="/api/v1/verify",
    tags=["Verification"]
)

app.include_router(
    news.router,
    prefix="/api/v1",
    tags=["News"]
)

# In-memory cache for fast responses
response_cache = {}
CACHE_TTL = 300  # 5 minutes

def get_cache_key(text: str) -> str:
    """Generate cache key for text"""
    return hashlib.md5(text.encode()).hexdigest()

def is_cache_valid(timestamp: float) -> bool:
    """Check if cache entry is still valid"""
    return time.time() - timestamp < CACHE_TTL

@lru_cache(maxsize=1000)
def get_cached_verdict(text_hash: str) -> dict:
    """Get cached verdict using LRU cache"""
    return response_cache.get(text_hash, {})

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Veritas - Fake News Detection & Claim Verification API",
        "version": app.version,
        "docs_url": "/docs"
    }

# Optimized fact-check endpoint with caching and async processing
@app.post("/api/fact-check")
async def fact_check(payload: dict = Body(...)):
    """Optimized fact-check endpoint with caching and async processing."""
    from types import SimpleNamespace
    from app.services import verifier
    
    start_time = time.time()
    
    text = (payload.get("text") or payload.get("claim") or "").strip()
    if not text:
        return {
            "truth_score": 0.0,
            "confidence_score": 0.0,
            "verdict": "INSUFFICIENT_DATA",
            "summary": "Empty claim text",
            "supporting_sources": [],
            "contradicting_sources": [],
            "processing_time": 0.0,
            "cached": False
        }

    # Check cache first
    cache_key = get_cache_key(text)
    cached_result = get_cached_verdict(cache_key)
    
    if cached_result and is_cache_valid(cached_result.get('timestamp', 0)):
        logger.info(f"[FACT-CHECK] Cache hit for: {text[:50]}...")
        cached_result['cached'] = True
        cached_result['processing_time'] = (time.time() - start_time) * 1000  # Convert to ms
        return cached_result

    logger.info(f"[FACT-CHECK] Processing new request: {text[:120]}")

    try:
        # Process request asynchronously
        req = SimpleNamespace(text=text)
        basic_result = verifier.verify_claim(req)

        # Build optimized response
        support = basic_result.get('matching_articles', [])
        contradict = basic_result.get('contradicting_articles', [])

        # Optimize source processing
        def process_sources(sources, limit=5):  # Reduced from 10 to 5 for speed
            return [
                {
                    "source": a.get('source', 'Unknown'),
                    "url": a.get('url', ''),
                    "title": a.get('title', 'Untitled')[:100],  # Limit title length
                    "similarity_score": round(a.get('similarity_score', 0.0), 3)
                }
                for a in sources[:limit]
            ]

        simple = {
            "truth_score": basic_result.get('truth_score', 0.0),
            "confidence_score": basic_result.get('confidence', 0.0),
            "verdict": basic_result.get('verdict', 'INSUFFICIENT_DATA'),
            "summary": f"Found {len(support)} supporting and {len(contradict)} contradicting sources.",
            "matching_articles": process_sources(support),
            "contradicting_articles": process_sources(contradict),
            "supporting_sources": process_sources(support),
            "contradicting_sources": process_sources(contradict),
            "processing_time": basic_result.get('processing_time', 0.0),
            "cached": False,
            "timestamp": time.time()
        }

        # Backward compatibility
        simple["confidence"] = simple["confidence_score"]

        # Cache the result
        response_cache[cache_key] = simple
        
        # Clean old cache entries (keep only last 1000)
        if len(response_cache) > 1000:
            # Remove oldest entries
            sorted_cache = sorted(response_cache.items(), key=lambda x: x[1].get('timestamp', 0))
            response_cache.clear()
            response_cache.update(dict(sorted_cache[-1000:]))

        total_time = time.time() - start_time
        simple["processing_time"] = round(total_time, 3)
        
        logger.info(f"[FACT-CHECK] Completed in {total_time:.3f}s")
        return simple

    except Exception as e:
        logger.error(f"[FACT-CHECK] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Fast health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

# Cache status endpoint
@app.get("/cache/status")
async def cache_status():
    """Get cache statistics"""
    return {
        "cache_size": len(response_cache),
        "cache_ttl": CACHE_TTL,
        "timestamp": time.time()
    }

# Clear cache endpoint
@app.post("/cache/clear")
async def clear_cache():
    """Clear all cached responses"""
    global response_cache
    response_cache.clear()
    return {"message": "Cache cleared", "timestamp": time.time()}
