"""
Optimized configuration for TruthScope backend
Includes performance tuning and caching settings
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings with performance optimizations"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "TruthScope - AI Fact-Checking System"
    VERSION: str = "1.0.0"
    
    # Performance Settings
    MAX_WORKERS: int = Field(default=4, description="Maximum worker processes")
    MAX_CONCURRENT_REQUESTS: int = Field(default=20, description="Max concurrent API requests")
    REQUEST_TIMEOUT: int = Field(default=30, description="Request timeout in seconds")
    
    # Caching Configuration
    CACHE_TTL: int = Field(default=300, description="Cache TTL in seconds")
    CACHE_MAX_SIZE: int = Field(default=1000, description="Maximum cache entries")
    ENABLE_REDIS_CACHE: bool = Field(default=False, description="Enable Redis caching")
    REDIS_URL: Optional[str] = Field(default=None, description="Redis connection URL")
    
    # Database Configuration (if needed later)
    DATABASE_URL: Optional[str] = Field(default=None, description="Database connection string")
    
    # External API Keys
    GOOGLE_API_KEY: str = Field(default="", description="Google Custom Search API Key")
    GOOGLE_CSE_ID: str = Field(default="", description="Google Custom Search Engine ID")
    GOOGLE_API_KEY_2: str = Field(default="", description="Secondary Google API Key")
    GOOGLE_CSE_ID_2: str = Field(default="", description="Secondary Google CSE ID")
    GOOGLE_API_KEY_NEW: str = Field(default="", description="New Google API Key")
    
    NEWSAPI_KEY: str = Field(default="", description="NewsAPI.org API Key")
    GNEWS_API_KEY: str = Field(default="", description="GNews API Key")
    MEDIASTACK_API_KEY: str = Field(default="", description="MediaStack API Key")
    
    # Twitter API Keys
    TWITTER_API_KEY: str = Field(default="", description="Twitter API Key")
    TWITTER_API_SECRET: str = Field(default="", description="Twitter API Secret")
    TWITTER_BEARER_TOKEN: str = Field(default="", description="Twitter Bearer Token")
    TWITTER_ACCESS_TOKEN: str = Field(default="", description="Twitter Access Token")
    TWITTER_ACCESS_TOKEN_SECRET: str = Field(default="", description="Twitter Access Token Secret")
    
    # LLM Configuration
    ENABLE_LLM_PROCESSING: bool = Field(default=True, description="Enable LLM-based processing")
    LLM_MODEL_NAME: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Default LLM model")
    LLM_BATCH_SIZE: int = Field(default=32, description="LLM batch processing size")
    LLM_MAX_LENGTH: int = Field(default=512, description="Maximum text length for LLM processing")
    
    # News Processing
    MAX_ARTICLES_PER_SOURCE: int = Field(default=15, description="Maximum articles per news source")
    MAX_ARTICLES_TOTAL: int = Field(default=100, description="Maximum total articles to process")
    ARTICLE_PROCESSING_TIMEOUT: int = Field(default=10, description="Article processing timeout")
    
    # Security Settings
    CORS_ORIGINS: list = Field(default=["*"], description="Allowed CORS origins")
    API_KEY_HEADER: str = Field(default="X-API-Key", description="API key header name")
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Rate limit per minute per IP")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    ENABLE_STRUCTURED_LOGGING: bool = Field(default=True, description="Enable structured logging")
    
    # Monitoring and Metrics
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")
    METRICS_PORT: int = Field(default=9090, description="Metrics server port")
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Health check interval in seconds")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Performance optimization functions
def get_optimized_worker_count() -> int:
    """Get optimized worker count based on system resources"""
    import multiprocessing
    cpu_count = multiprocessing.cpu_count()
    return min(cpu_count * 2, settings.MAX_WORKERS)

def get_cache_config() -> dict:
    """Get cache configuration for optimal performance"""
    return {
        "ttl": settings.CACHE_TTL,
        "max_size": settings.CACHE_MAX_SIZE,
        "enable_redis": settings.ENABLE_REDIS_CACHE,
        "redis_url": settings.REDIS_URL
    }

def get_api_limits() -> dict:
    """Get API rate limiting configuration"""
    return {
        "max_concurrent": settings.MAX_CONCURRENT_REQUESTS,
        "timeout": settings.REQUEST_TIMEOUT,
        "rate_limit": settings.RATE_LIMIT_PER_MINUTE
    }
