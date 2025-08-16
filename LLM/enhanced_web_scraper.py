"""
Enhanced Multi-Source Web Scraper
Sophisticated web scraping from multiple sources with full content extraction
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import newspaper
from newspaper import Article as NewsArticle
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
from urllib.parse import urlparse, urljoin
import json
import time
from concurrent.futures import ThreadPoolExecutor
import hashlib

from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedArticle:
    """Enhanced article with full content and metadata"""
    title: str
    content: str
    url: str
    source: str
    published_date: Optional[datetime] = None
    author: Optional[str] = None
    snippet: str = ""
    full_text: str = ""
    keywords: List[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None
    credibility_score: float = 0.5
    region: Optional[str] = None
    language: str = "en"
    content_hash: str = ""
    
    def __post_init__(self):
        """Generate content hash for deduplication"""
        if not self.content_hash:
            content_for_hash = f"{self.title}{self.content}".lower()
            self.content_hash = hashlib.md5(content_for_hash.encode()).hexdigest()

class EnhancedWebScraper:
    """Sophisticated multi-source web scraper"""
    
    def __init__(self):
        self.session = None
        self.trusted_sources = set(config.TRUSTED_SOURCES)
        self.max_articles = config.MAX_ARTICLES
        self.timeout = config.REQUEST_TIMEOUT
        
    async def scrape_multiple_queries(self, search_queries: List[str]) -> List[EnhancedArticle]:
        """
        Scrape articles using multiple search queries
        
        Args:
            search_queries: List of search queries to use
            
        Returns:
            List of enhanced articles with full content
        """
        logger.info(f"🌐 Starting enhanced scraping with {len(search_queries)} queries")
        
        all_articles = []
        
        # Create aiohttp session
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers=config.HEADERS
        ) as session:
            self.session = session
            
            # Scrape from multiple sources concurrently
            tasks = []
            
            for query in search_queries[:10]:  # Limit to 10 queries to avoid rate limits
                # Google Custom Search
                if config.GOOGLE_API_KEY and config.GOOGLE_CSE_ID:
                    tasks.append(self._scrape_google_cse(query))
                
                # NewsAPI
                if config.NEWSAPI_KEY:
                    tasks.append(self._scrape_newsapi(query))
                
                # Reddit (for social verification)
                if config.REDDIT_CLIENT_ID:
                    tasks.append(self._scrape_reddit(query))
            
            # Execute all scraping tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect all articles
            for result in results:
                if isinstance(result, list):
                    all_articles.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"⚠️ Scraping task failed: {result}")
        
        # Early filter: remove low-content and very low-credibility items before heavy extraction
        filtered_initial: List[EnhancedArticle] = []
        seen_urls: Set[str] = set()
        for a in all_articles:
            if not a.url or a.url in seen_urls:
                continue
            seen_urls.add(a.url)
            if len((a.content or a.snippet or "")) < config.CONTENT_MIN_LENGTH:
                continue
            if a.credibility_score < 0.35:
                continue
            filtered_initial.append(a)
        
        # Post-process articles
        enhanced_articles = await self._enhance_articles(filtered_initial)
        
        # Remove duplicates and filter
        unique_articles = self._deduplicate_articles(enhanced_articles)
        
        # Sort by credibility and relevance
        sorted_articles = self._sort_articles(unique_articles)
        
        final_articles = sorted_articles[:self.max_articles]
        logger.info(f"✅ Enhanced scraping complete: {len(final_articles)} articles")
        
        return final_articles
    
    async def _scrape_google_cse(self, query: str) -> List[EnhancedArticle]:
        """Scrape using Google Custom Search Engine"""
        try:
            logger.info(f"🔍 [Google CSE] Searching: {query}")
            
            params = {
                'key': config.GOOGLE_API_KEY,
                'cx': config.GOOGLE_CSE_ID,
                'q': query,
                'num': min(10, config.MAX_ARTICLES_PER_SOURCE),
                'dateRestrict': f'd{config.MAX_ARTICLE_AGE_DAYS}'
            }
            
            async with self.session.get(
                'https://www.googleapis.com/customsearch/v1',
                params=params
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    articles = []
                    
                    for item in data.get('items', []):
                        article = EnhancedArticle(
                            title=item.get('title', ''),
                            content=item.get('snippet', ''),
                            url=item.get('link', ''),
                            source=self._extract_source(item.get('link', '')),
                            snippet=item.get('snippet', ''),
                            credibility_score=self._calculate_source_credibility(item.get('link', ''))
                        )
                        articles.append(article)
                    
                    logger.info(f"✅ [Google CSE] Found {len(articles)} articles")
                    return articles
                else:
                    logger.error(f"❌ [Google CSE] HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ [Google CSE] Error: {e}")
            return []
    
    async def _scrape_newsapi(self, query: str) -> List[EnhancedArticle]:
        """Scrape using NewsAPI"""
        try:
            logger.info(f"📰 [NewsAPI] Searching: {query}")
            
            params = {
                'q': query,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': min(20, config.MAX_ARTICLES_PER_SOURCE),
                'from': (datetime.now() - timedelta(days=config.MAX_ARTICLE_AGE_DAYS)).isoformat()
            }
            
            headers = {
                'X-Api-Key': config.NEWSAPI_KEY,
                **config.HEADERS
            }
            
            async with self.session.get(
                'https://newsapi.org/v2/everything',
                params=params,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    articles = []
                    
                    for item in data.get('articles', []):
                        # Parse published date
                        published_date = None
                        if item.get('publishedAt'):
                            try:
                                published_date = datetime.fromisoformat(
                                    item['publishedAt'].replace('Z', '+00:00')
                                )
                            except:
                                pass
                        
                        article = EnhancedArticle(
                            title=item.get('title', ''),
                            content=item.get('description', ''),
                            url=item.get('url', ''),
                            source=self._extract_source(item.get('url', '')),
                            published_date=published_date,
                            author=item.get('author'),
                            snippet=item.get('description', ''),
                            credibility_score=self._calculate_source_credibility(item.get('url', ''))
                        )
                        articles.append(article)
                    
                    logger.info(f"✅ [NewsAPI] Found {len(articles)} articles")
                    return articles
                else:
                    logger.error(f"❌ [NewsAPI] HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ [NewsAPI] Error: {e}")
            return []
    
    async def _scrape_reddit(self, query: str) -> List[EnhancedArticle]:
        """Scrape Reddit for social verification (simplified)"""
        try:
            logger.info(f"🔴 [Reddit] Searching: {query}")
            
            # Use Reddit's JSON API (no authentication required for public posts)
            search_url = f"https://www.reddit.com/search.json"
            params = {
                'q': query,
                'sort': 'relevance',
                'limit': 10,
                't': 'month'  # Last month
            }
            
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = []
                    
                    for post in data.get('data', {}).get('children', []):
                        post_data = post.get('data', {})
                        
                        # Only include posts with external URLs
                        if post_data.get('url') and not post_data.get('url').startswith('https://www.reddit.com'):
                            article = EnhancedArticle(
                                title=post_data.get('title', ''),
                                content=post_data.get('selftext', '')[:500],
                                url=post_data.get('url', ''),
                                source='reddit.com',
                                snippet=post_data.get('selftext', '')[:200],
                                credibility_score=0.3  # Lower credibility for social media
                            )
                            articles.append(article)
                    
                    logger.info(f"✅ [Reddit] Found {len(articles)} posts")
                    return articles
                else:
                    logger.error(f"❌ [Reddit] HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ [Reddit] Error: {e}")
            return []
    
    async def _enhance_articles(self, articles: List[EnhancedArticle]) -> List[EnhancedArticle]:
        """Enhance articles with full content extraction"""
        logger.info(f"🔧 Enhancing {len(articles)} articles with full content...")
        
        enhanced_articles = []
        
        # Use ThreadPoolExecutor for CPU-bound newspaper operations
        with ThreadPoolExecutor(max_workers=config.MAX_CONCURRENT_REQUESTS) as executor:
            tasks = []
            
            for article in articles:
                if article.url and self._is_valid_url(article.url):
                    task = asyncio.get_event_loop().run_in_executor(
                        executor, self._extract_full_content, article
                    )
                    tasks.append(task)
            
            # Wait for all content extraction tasks
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, EnhancedArticle):
                        enhanced_articles.append(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"⚠️ Content extraction failed: {result}")
        
        logger.info(f"✅ Enhanced {len(enhanced_articles)} articles")
        return enhanced_articles
    
    def _extract_full_content(self, article: EnhancedArticle) -> EnhancedArticle:
        """Extract full content using newspaper3k"""
        try:
            news_article = NewsArticle(article.url)
            news_article.download()
            news_article.parse()
            news_article.nlp()
            
            # Update article with extracted content
            if news_article.text and len(news_article.text) > len(article.content):
                article.full_text = news_article.text
                article.content = news_article.text[:1000]  # First 1000 chars for processing
            
            if news_article.title and not article.title:
                article.title = news_article.title
            
            if news_article.authors:
                article.author = ', '.join(news_article.authors)
            
            if news_article.publish_date:
                article.published_date = news_article.publish_date
            
            if news_article.keywords:
                article.keywords = list(news_article.keywords)
            
            return article
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract content from {article.url}: {e}")
            return article
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and accessible"""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and parsed.scheme in ['http', 'https']
        except:
            return False
    
    def _extract_source(self, url: str) -> str:
        """Extract source domain from URL"""
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '').lower()
        except:
            return "unknown"
    
    def _calculate_source_credibility(self, url: str) -> float:
        """Calculate credibility score based on source"""
        source = self._extract_source(url)
        
        if source in self.trusted_sources:
            return 0.9
        elif any(trusted in source for trusted in self.trusted_sources):
            return 0.7
        elif source.endswith('.edu') or source.endswith('.gov'):
            return 0.8
        elif source.endswith('.org'):
            return 0.6
        else:
            return 0.4
    
    def _deduplicate_articles(self, articles: List[EnhancedArticle]) -> List[EnhancedArticle]:
        """Remove duplicate articles based on content hash"""
        seen_hashes = set()
        unique_articles = []
        
        for article in articles:
            if article.content_hash not in seen_hashes:
                seen_hashes.add(article.content_hash)
                unique_articles.append(article)
        
        logger.info(f"🔄 Removed {len(articles) - len(unique_articles)} duplicates")
        return unique_articles
    
    def _sort_articles(self, articles: List[EnhancedArticle]) -> List[EnhancedArticle]:
        """Sort articles by credibility and relevance"""
        def sort_key(article):
            # Combine credibility score with content length and recency
            credibility = article.credibility_score
            content_score = min(len(article.content) / 1000, 1.0)  # Normalize content length
            
            # Recency score (newer articles get higher score)
            recency_score = 0.5
            if article.published_date:
                days_old = (datetime.now() - article.published_date.replace(tzinfo=None)).days
                recency_score = max(0, 1 - (days_old / config.MAX_ARTICLE_AGE_DAYS))
            
            return credibility * 0.5 + content_score * 0.3 + recency_score * 0.2
        
        return sorted(articles, key=sort_key, reverse=True)

# Convenience function
async def scrape_enhanced_articles(search_queries: List[str]) -> List[EnhancedArticle]:
    """
    Scrape articles using enhanced multi-source scraper
    
    Args:
        search_queries: List of search queries
        
    Returns:
        List of enhanced articles with full content
    """
    scraper = EnhancedWebScraper()
    return await scraper.scrape_multiple_queries(search_queries)
