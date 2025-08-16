"""
Enhanced Multi-Source News Fetcher for Veritas Dashboard
Fetches news from multiple APIs to provide comprehensive coverage
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from dataclasses import dataclass
import json
import re
from urllib.parse import urlparse
import hashlib

# Import the weighting system
from .news_source_weights import source_weights

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    """Enhanced data class for news articles"""
    headline: str
    time: str
    description: str
    url: str
    source: str
    category: str
    api_source: str  # Which API provided this article
    published_at: Optional[datetime] = None
    image_url: Optional[str] = None
    sentiment_score: Optional[float] = None
    credibility_score: Optional[float] = None
    source_weight: Optional[float] = None
    source_category: Optional[str] = None
    verification_level: Optional[int] = None
    bias_rating: Optional[str] = None
    fact_checking: Optional[bool] = None
    editorial_standards: Optional[str] = None
    weighted_score: Optional[float] = None

class MultiSourceNewsFetcher:
    """Fetches news from multiple APIs for comprehensive coverage"""
    
    def __init__(self):
        self.session = None
        self.api_keys = self._load_api_keys()
        self.category_mappings = {
            'politics': ['politics', 'government', 'election', 'policy', 'congress', 'senate'],
            'economics': ['business', 'economy', 'finance', 'market', 'stocks', 'trade'],
            'celebrity': ['entertainment', 'celebrity', 'hollywood', 'music', 'movies', 'tv'],
            'sports': ['sports', 'football', 'basketball', 'soccer', 'baseball', 'tennis']
        }
        
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables"""
        return {
            'newsapi': os.getenv('NEWSAPI_KEY'),
            'gnews': os.getenv('GNEWS_API_KEY'),
            'mediastack': os.getenv('MEDIASTACK_API_KEY'),
            'bing': os.getenv('BING_NEWS_API_KEY'),
            'reddit_client_id': os.getenv('REDDIT_CLIENT_ID'),
            'reddit_client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
            'twitter': os.getenv('TWITTER_BEARER_TOKEN')
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'VeritasNewsBot/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_all_news(self, limit_per_category: int = 5) -> Dict[str, List[NewsArticle]]:
        """Fetch news from all sources for all categories"""
        tasks = []
        for category in self.category_mappings.keys():
            tasks.append(self.fetch_category_news(category, limit_per_category))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        news_data = {}
        for category, result in zip(self.category_mappings.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {category} news: {result}")
                news_data[category] = []
            else:
                news_data[category] = result
        
        return news_data
    
    async def fetch_category_news(self, category: str, limit: int = 5) -> List[NewsArticle]:
        """Fetch news for a specific category from multiple sources"""
        articles = []
        category_terms = self.category_mappings.get(category, [category])
        
        # Fetch from multiple APIs concurrently
        tasks = []
        
        # NewsAPI
        if self.api_keys['newsapi']:
            tasks.append(self._fetch_from_newsapi(category_terms, limit))
        
        # GNews
        if self.api_keys['gnews']:
            tasks.append(self._fetch_from_gnews(category_terms, limit))
        
        # MediaStack
        if self.api_keys['mediastack']:
            tasks.append(self._fetch_from_mediastack(category_terms, limit))
        
        # Bing News
        if self.api_keys['bing']:
            tasks.append(self._fetch_from_bing(category_terms, limit))
        
        # Execute all tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    articles.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"API fetch error: {result}")
        
        # Apply source weighting and scoring
        articles = self._apply_source_weighting(articles)
        
        # Deduplicate articles based on URL and headline similarity
        articles = self._deduplicate_articles(articles)
        
        # Sort by weighted score (highest first) and limit results
        articles.sort(key=lambda x: x.weighted_score or 0, reverse=True)
        
        return articles[:limit]
    
    async def _fetch_from_newsapi(self, category_terms: List[str], limit: int) -> List[NewsArticle]:
        """Fetch from NewsAPI.org"""
        articles = []
        
        for term in category_terms[:2]:  # Try first 2 terms
            try:
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': term,
                    'apiKey': self.api_keys['newsapi'],
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': min(limit * 2, 20),
                    'from': (datetime.now() - timedelta(days=2)).isoformat()
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get('articles', []):
                            article = NewsArticle(
                                headline=item.get('title', ''),
                                time=self._format_time(item.get('publishedAt', '')),
                                description=item.get('description', ''),
                                url=item.get('url', ''),
                                source=item.get('source', {}).get('name', 'Unknown'),
                                category=self._determine_category(term),
                                api_source='NewsAPI',
                                published_at=self._parse_datetime(item.get('publishedAt', '')),
                                image_url=item.get('urlToImage')
                            )
                            
                            if article.headline and article.url:
                                articles.append(article)
                
                if len(articles) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"NewsAPI error for term '{term}': {e}")
        
        return articles
    
    async def _fetch_from_gnews(self, category_terms: List[str], limit: int) -> List[NewsArticle]:
        """Fetch from GNews API"""
        articles = []
        
        for term in category_terms[:2]:
            try:
                url = "https://gnews.io/api/v4/search"
                params = {
                    'q': term,
                    'token': self.api_keys['gnews'],
                    'lang': 'en',
                    'country': 'us',
                    'max': min(limit * 2, 20),
                    'sortby': 'publishedAt'
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get('articles', []):
                            article = NewsArticle(
                                headline=item.get('title', ''),
                                time=self._format_time(item.get('publishedAt', '')),
                                description=item.get('description', ''),
                                url=item.get('url', ''),
                                source=item.get('source', {}).get('name', 'Unknown'),
                                category=self._determine_category(term),
                                api_source='GNews',
                                published_at=self._parse_datetime(item.get('publishedAt', '')),
                                image_url=item.get('image')
                            )
                            
                            if article.headline and article.url:
                                articles.append(article)
                
                if len(articles) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"GNews error for term '{term}': {e}")
        
        return articles
    
    async def _fetch_from_mediastack(self, category_terms: List[str], limit: int) -> List[NewsArticle]:
        """Fetch from MediaStack API"""
        articles = []
        
        for term in category_terms[:2]:
            try:
                url = "http://api.mediastack.com/v1/news"
                params = {
                    'access_key': self.api_keys['mediastack'],
                    'keywords': term,
                    'languages': 'en',
                    'countries': 'us',
                    'limit': min(limit * 2, 20),
                    'sort': 'published_desc'
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get('data', []):
                            article = NewsArticle(
                                headline=item.get('title', ''),
                                time=self._format_time(item.get('published_at', '')),
                                description=item.get('description', ''),
                                url=item.get('url', ''),
                                source=item.get('source', 'Unknown'),
                                category=self._determine_category(term),
                                api_source='MediaStack',
                                published_at=self._parse_datetime(item.get('published_at', '')),
                                image_url=item.get('image')
                            )
                            
                            if article.headline and article.url:
                                articles.append(article)
                
                if len(articles) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"MediaStack error for term '{term}': {e}")
        
        return articles
    
    async def _fetch_from_bing(self, category_terms: List[str], limit: int) -> List[NewsArticle]:
        """Fetch from Bing News Search API"""
        articles = []
        
        for term in category_terms[:2]:
            try:
                url = "https://api.bing.microsoft.com/v7.0/news/search"
                headers = {
                    'Ocp-Apim-Subscription-Key': self.api_keys['bing']
                }
                params = {
                    'q': term,
                    'count': min(limit * 2, 20),
                    'mkt': 'en-US',
                    'freshness': 'Day'
                }
                
                async with self.session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get('value', []):
                            article = NewsArticle(
                                headline=item.get('name', ''),
                                time=self._format_time(item.get('datePublished', '')),
                                description=item.get('description', ''),
                                url=item.get('url', ''),
                                source=item.get('provider', [{}])[0].get('name', 'Unknown'),
                                category=self._determine_category(term),
                                api_source='Bing',
                                published_at=self._parse_datetime(item.get('datePublished', '')),
                                image_url=item.get('image', {}).get('thumbnail', {}).get('contentUrl')
                            )
                            
                            if article.headline and article.url:
                                articles.append(article)
                
                if len(articles) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"Bing News error for term '{term}': {e}")
        
        return articles
    
    def _determine_category(self, term: str) -> str:
        """Determine the category based on search term"""
        for category, terms in self.category_mappings.items():
            if any(t in term.lower() for t in terms):
                return category
        return 'general'
    
    def _format_time(self, time_str: str) -> str:
        """Format time string for display"""
        try:
            dt = self._parse_datetime(time_str)
            if dt:
                return dt.strftime("%B %d, %Y")
        except:
            pass
        return "Recent"
    
    def _parse_datetime(self, time_str: str) -> Optional[datetime]:
        """Parse datetime string"""
        if not time_str:
            return None
        
        # Try different datetime formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on URL and headline similarity"""
        seen_urls = set()
        seen_headlines = set()
        unique_articles = []
        
        for article in articles:
            # Check URL similarity
            url_hash = self._get_url_hash(article.url)
            if url_hash in seen_urls:
                continue
            
            # Check headline similarity (fuzzy matching)
            headline_normalized = self._normalize_headline(article.headline)
            if headline_normalized in seen_headlines:
                continue
            
            seen_urls.add(url_hash)
            seen_headlines.add(headline_normalized)
            unique_articles.append(article)
        
        return unique_articles
    
    def _get_url_hash(self, url: str) -> str:
        """Get a hash of the URL domain and path"""
        try:
            parsed = urlparse(url)
            domain_path = f"{parsed.netloc}{parsed.path}"
            return hashlib.md5(domain_path.encode()).hexdigest()
        except:
            return hashlib.md5(url.encode()).hexdigest()
    
    def _normalize_headline(self, headline: str) -> str:
        """Normalize headline for similarity comparison"""
        return re.sub(r'[^\w\s]', '', headline.lower()).strip()

    def _apply_source_weighting(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Apply source weighting to articles"""
        for article in articles:
            # Get source weight information
            source_weight = source_weights.get_source_weight(article.url, article.source)
            
            # Calculate weighted score
            weighted_score = self._calculate_weighted_score(article, source_weight)
            
            # Update article with weight information
            article.source_weight = source_weight.weight
            article.source_category = source_weight.category
            article.verification_level = source_weight.verification_level
            article.bias_rating = source_weight.bias_rating
            article.fact_checking = source_weight.fact_checking
            article.editorial_standards = source_weight.editorial_standards
            article.weighted_score = weighted_score
            article.credibility_score = source_weight.weight
        
        return articles
    
    def _calculate_weighted_score(self, article: NewsArticle, source_weight) -> float:
        """Calculate weighted score for an article"""
        base_score = source_weight.weight
        
        # Bonus for recent articles
        time_bonus = self._calculate_time_bonus(article.time)
        
        # Bonus for longer descriptions
        description_bonus = self._calculate_description_bonus(article.description)
        
        # Bonus for having image
        image_bonus = 0.05 if article.image_url else 0.0
        
        # Bonus for premium sources (Al Jazeera, BBC, CNN)
        premium_bonus = 0.1 if source_weight.weight >= 0.9 else 0.0
        
        # Calculate final weighted score
        weighted_score = base_score + time_bonus + description_bonus + image_bonus + premium_bonus
        
        # Ensure score doesn't exceed 1.0
        return min(weighted_score, 1.0)
    
    def _calculate_time_bonus(self, time_str: str) -> float:
        """Calculate time-based bonus for recent articles"""
        try:
            # Parse the time string and calculate recency bonus
            # This is a simplified version - you might want to enhance this
            if 'today' in time_str.lower() or 'recent' in time_str.lower():
                return 0.03
            elif 'yesterday' in time_str.lower():
                return 0.02
            else:
                return 0.01
        except:
            return 0.01
    
    def _calculate_description_bonus(self, description: str) -> float:
        """Calculate bonus based on description quality"""
        if not description:
            return 0.0
        
        length = len(description)
        if length > 200:
            return 0.03
        elif length > 100:
            return 0.02
        elif length > 50:
            return 0.01
        else:
            return 0.0

# Usage example
async def main():
    """Example usage of the enhanced news fetcher"""
    async with MultiSourceNewsFetcher() as fetcher:
        news = await fetcher.fetch_all_news(limit_per_category=5)
        
        for category, articles in news.items():
            print(f"\n=== {category.upper()} NEWS ===")
            for article in articles:
                print(f"• {article.headline}")
                print(f"  Source: {article.source} via {article.api_source}")
                print(f"  Time: {article.time}")
                print()

if __name__ == "__main__":
    asyncio.run(main())
