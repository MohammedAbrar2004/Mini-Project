"""
Enhanced Multi-Source News Fetcher with Regional Intelligence
Fetches news from multiple APIs and applies regional weighting
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import os
from urllib.parse import urlparse
import hashlib
import re

# Import the enhanced source weighting system
from .news_source_weights import source_weights

@dataclass
class NewsArticle:
    """Enhanced news article data structure"""
    title: str
    description: str
    url: str
    source: str
    api_source: str  # Which API provided this article
    published_at: Optional[datetime]
    image_url: Optional[str]
    sentiment_score: float = 0.0
    credibility_score: float = 0.0
    source_weight: float = 0.0
    source_category: str = "unknown"
    verification_level: str = "unverified"
    bias_rating: str = "center"
    fact_checking: str = "fair"
    editorial_standards: str = "medium"
    weighted_score: float = 0.0
    regional_boost: float = 1.0
    detected_regions: List[str] = None

class MultiSourceNewsFetcher:
    """Fetches news from multiple APIs with regional intelligence"""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.session = None
        self.cache = {}
        self.cache_expiry = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'TruthScope/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables"""
        return {
            'newsapi': os.getenv('NEWSAPI_KEY'),
            'gnews': os.getenv('GNEWS_API_KEY'),
            'mediastack': os.getenv('MEDIASTACK_API_KEY'),
            'google_cse': os.getenv('GOOGLE_API_KEY_NEW'),
            'google_cse_id': os.getenv('GOOGLE_CSE_ID')
        }
    
    async def fetch_category_news(self, category: str = "general", 
                                 max_articles: int = 20) -> List[NewsArticle]:
        """Fetch news from multiple sources concurrently"""
        tasks = []
        
        # NewsAPI
        if self.api_keys['newsapi']:
            tasks.append(self._fetch_from_newsapi(category, max_articles))
        
        # GNews
        if self.api_keys['gnews']:
            tasks.append(self._fetch_from_gnews(category, max_articles))
        
        # MediaStack
        if self.api_keys['mediastack']:
            tasks.append(self._fetch_from_mediastack(category, max_articles))
        
        # Google Custom Search (for additional coverage)
        if self.api_keys['google_cse'] and self.api_keys['google_cse_id']:
            tasks.append(self._fetch_from_google_cse(category, max_articles))
        
        if not tasks:
            raise ValueError("No API keys configured")
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and process results
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                print(f"API fetch error: {result}")
        
        # Apply regional intelligence and weighting
        enhanced_articles = self._apply_regional_intelligence(all_articles)
        
        # Deduplicate articles
        unique_articles = self._deduplicate_articles(enhanced_articles)
        
        # Sort by weighted score
        unique_articles.sort(key=lambda x: x.weighted_score, reverse=True)
        
        return unique_articles[:max_articles]
    
    def _apply_regional_intelligence(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Apply regional intelligence to articles"""
        for article in articles:
            # Detect regions in the news content
            detected_regions = source_weights.regional_matcher.detect_news_region(
                article.description, article.title
            )
            article.detected_regions = detected_regions
            
            # Get source weight with regional intelligence
            source_weight_info = source_weights.get_source_weight(
                url=article.url,
                source_name=article.source,
                news_content=article.description,
                news_title=article.title
            )
            
            # Apply regional boost
            regional_boost = source_weights.regional_matcher.get_regional_boost(
                article.url, article.source, detected_regions
            )
            article.regional_boost = regional_boost
            
            # Update article with source weight information
            article.source_weight = source_weight_info.weight
            article.source_category = source_weight_info.category
            article.verification_level = source_weight_info.verification_level
            article.bias_rating = source_weight_info.bias_rating
            article.fact_checking = source_weight_info.fact_checking
            article.editorial_standards = source_weight_info.editorial_standards
            
            # Calculate weighted score with regional boost
            article.weighted_score = self._calculate_enhanced_score(article)
        
        return articles
    
    def _calculate_enhanced_score(self, article: NewsArticle) -> float:
        """Calculate enhanced weighted score with regional intelligence and balanced scoring"""
        # Get source weight info with credibility multiplier
        source_weight_info = source_weights.get_source_weight(
            url=article.url,
            source_name=article.source,
            news_content=article.description,
            news_title=article.title
        )
        
        # Base score with credibility multiplier
        base_score = source_weight_info.weight * source_weight_info.credibility_multiplier
        
        # Apply regional boost
        regional_score = base_score * article.regional_boost
        
        # Recency factor from source weights
        recency_factor = source_weights.calculate_recency_factor(
            article.published_at.strftime('%Y-%m-%d %H:%M:%S') if article.published_at else "Unknown"
        )
        
        # Description quality bonus
        description_bonus = self._calculate_description_bonus(article.description)
        
        # Sentiment balance bonus (neutral articles get slight boost)
        sentiment_bonus = self._calculate_sentiment_bonus(article.sentiment_score)
        
        # Final weighted score with recency factor
        final_score = regional_score * recency_factor + description_bonus + sentiment_bonus
        
        return min(1.0, final_score)  # Cap at 1.0
    
    def _calculate_time_bonus(self, published_at: Optional[datetime]) -> float:
        """Calculate time-based bonus for recent articles"""
        if not published_at:
            return 0.0
        
        age_hours = (datetime.now() - published_at).total_seconds() / 3600
        
        if age_hours < 1:  # Less than 1 hour
            return 0.05
        elif age_hours < 6:  # Less than 6 hours
            return 0.03
        elif age_hours < 24:  # Less than 24 hours
            return 0.01
        
        return 0.0
    
    def _calculate_description_bonus(self, description: str) -> float:
        """Calculate bonus based on description quality"""
        if not description:
            return 0.0
        
        # Bonus for longer, more detailed descriptions
        word_count = len(description.split())
        
        if word_count > 50:
            return 0.03
        elif word_count > 30:
            return 0.02
        elif word_count > 15:
            return 0.01
        
        return 0.0
    
    def _calculate_sentiment_bonus(self, sentiment_score: float) -> float:
        """Calculate bonus for balanced sentiment"""
        # Slight bonus for neutral sentiment (balanced reporting)
        if -0.1 <= sentiment_score <= 0.1:
            return 0.02
        elif -0.3 <= sentiment_score <= 0.3:
            return 0.01
        
        return 0.0
    
    async def _fetch_from_newsapi(self, category: str, max_articles: int) -> List[NewsArticle]:
        """Fetch news from NewsAPI"""
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'country': 'us',
                'category': category,
                'apiKey': self.api_keys['newsapi'],
                'pageSize': min(max_articles, 100)
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_newsapi_response(data, max_articles)
                else:
                    print(f"NewsAPI error: {response.status}")
                    return []
        except Exception as e:
            print(f"NewsAPI fetch error: {e}")
            return []
    
    async def _fetch_from_gnews(self, category: str, max_articles: int) -> List[NewsArticle]:
        """Fetch news from GNews"""
        try:
            url = "https://gnews.io/api/v4/top-headlines"
            params = {
                'category': category,
                'lang': 'en',
                'country': 'us',
                'apikey': self.api_keys['gnews'],
                'max': min(max_articles, 100)
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_gnews_response(data, max_articles)
                else:
                    print(f"GNews error: {response.status}")
                    return []
        except Exception as e:
            print(f"GNews fetch error: {e}")
            return []
    
    async def _fetch_from_mediastack(self, category: str, max_articles: int) -> List[NewsArticle]:
        """Fetch news from MediaStack"""
        try:
            url = "http://api.mediastack.com/v1/news"
            params = {
                'access_key': self.api_keys['mediastack'],
                'categories': category,
                'languages': 'en',
                'countries': 'us',
                'limit': min(max_articles, 100)
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_mediastack_response(data, max_articles)
                else:
                    print(f"MediaStack error: {response.status}")
                    return []
        except Exception as e:
            print(f"MediaStack fetch error: {e}")
            return []
        
    async def _fetch_from_google_cse(self, category: str, max_articles: int) -> List[NewsArticle]:
        """Fetch news from Google Custom Search Engine"""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
                    params = {
                'key': self.api_keys['google_cse'],
                'cx': self.api_keys['google_cse_id'],
                'q': f"news {category}",
                'num': min(max_articles, 10),  # Google CSE limit
                'dateRestrict': 'd1'  # Last 24 hours
            }
            
            async with self.session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                    return self._parse_google_cse_response(data, max_articles)
                else:
                    print(f"Google CSE error: {response.status}")
                    return []
        except Exception as e:
            print(f"Google CSE fetch error: {e}")
            return []
    
    def _parse_newsapi_response(self, data: Dict, max_articles: int) -> List[NewsArticle]:
        """Parse NewsAPI response"""
        articles = []
        if 'articles' not in data:
            return articles
        
        for item in data['articles'][:max_articles]:
            try:
                published_at = None
                if item.get('publishedAt'):
                    published_at = datetime.fromisoformat(item['publishedAt'].replace('Z', '+00:00'))
                                
                                article = NewsArticle(
                    title=item.get('title', ''),
                                    description=item.get('description', ''),
                                    url=item.get('url', ''),
                                    source=item.get('source', {}).get('name', 'Unknown'),
                    api_source='NewsAPI',
                    published_at=published_at,
                    image_url=item.get('urlToImage'),
                    sentiment_score=0.0,  # NewsAPI doesn't provide sentiment
                    credibility_score=0.0,  # Will be calculated later
                    source_weight=0.0,  # Will be calculated later
                    source_category="unknown",  # Will be calculated later
                    verification_level="unverified",  # Will be calculated later
                    bias_rating="center",  # Will be calculated later
                    fact_checking="fair",  # Will be calculated later
                    editorial_standards="medium",  # Will be calculated later
                    weighted_score=0.0,  # Will be calculated later
                    regional_boost=1.0,  # Will be calculated later
                    detected_regions=[]  # Will be calculated later
                )
                articles.append(article)
            except Exception as e:
                print(f"Error parsing NewsAPI article: {e}")
                continue
        
        return articles
    
    def _parse_gnews_response(self, data: Dict, max_articles: int) -> List[NewsArticle]:
        """Parse GNews response"""
        articles = []
        if 'articles' not in data:
            return articles
        
        for item in data['articles'][:max_articles]:
            try:
                published_at = None
                if item.get('publishedAt'):
                    published_at = datetime.fromisoformat(item['publishedAt'].replace('Z', '+00:00'))
                
                article = NewsArticle(
                    title=item.get('title', ''),
                    description=item.get('description', ''),
                    url=item.get('url', ''),
                    source=item.get('source', {}).get('name', 'Unknown'),
                    api_source='GNews',
                    published_at=published_at,
                    image_url=item.get('image'),
                    sentiment_score=0.0,  # GNews doesn't provide sentiment
                    credibility_score=0.0,  # Will be calculated later
                    source_weight=0.0,  # Will be calculated later
                    source_category="unknown",  # Will be calculated later
                    verification_level="unverified",  # Will be calculated later
                    bias_rating="center",  # Will be calculated later
                    fact_checking="fair",  # Will be calculated later
                    editorial_standards="medium",  # Will be calculated later
                    weighted_score=0.0,  # Will be calculated later
                    regional_boost=1.0,  # Will be calculated later
                    detected_regions=[]  # Will be calculated later
                )
                articles.append(article)
                except Exception as e:
                print(f"Error parsing GNews article: {e}")
                    continue
        
        return articles
    
    def _parse_mediastack_response(self, data: Dict, max_articles: int) -> List[NewsArticle]:
        """Parse MediaStack response"""
        articles = []
        if 'data' not in data:
            return articles
        
        for item in data['data'][:max_articles]:
            try:
                published_at = None
                if item.get('published_at'):
                    published_at = datetime.fromisoformat(item['published_at'].replace('Z', '+00:00'))
                
                article = NewsArticle(
                    title=item.get('title', ''),
                    description=item.get('description', ''),
                    url=item.get('url', ''),
                    source=item.get('source', 'Unknown'),
                    api_source='MediaStack',
                    published_at=published_at,
                    image_url=item.get('image'),
                    sentiment_score=0.0,  # MediaStack doesn't provide sentiment
                    credibility_score=0.0,  # Will be calculated later
                    source_weight=0.0,  # Will be calculated later
                    source_category="unknown",  # Will be calculated later
                    verification_level="unverified",  # Will be calculated later
                    bias_rating="center",  # Will be calculated later
                    fact_checking="fair",  # Will be calculated later
                    editorial_standards="medium",  # Will be calculated later
                    weighted_score=0.0,  # Will be calculated later
                    regional_boost=1.0,  # Will be calculated later
                    detected_regions=[]  # Will be calculated later
                )
                articles.append(article)
            except Exception as e:
                print(f"Error parsing MediaStack article: {e}")
                continue
        
        return articles
    
    def _parse_google_cse_response(self, data: Dict, max_articles: int) -> List[NewsArticle]:
        """Parse Google CSE response"""
        articles = []
        if 'items' not in data:
            return articles
        
        for item in data['items'][:max_articles]:
            try:
                # Google CSE doesn't provide publication date
            article = NewsArticle(
                    title=item.get('title', ''),
                    description=item.get('snippet', ''),
                    url=item.get('link', ''),
                    source=item.get('displayLink', 'Unknown'),
                    api_source='Google CSE',
                    published_at=None,
                    image_url=None,  # Google CSE doesn't provide images
                    sentiment_score=0.0,  # Google CSE doesn't provide sentiment
                    credibility_score=0.0,  # Will be calculated later
                    source_weight=0.0,  # Will be calculated later
                    source_category="unknown",  # Will be calculated later
                    verification_level="unverified",  # Will be calculated later
                    bias_rating="center",  # Will be calculated later
                    fact_checking="fair",  # Will be calculated later
                    editorial_standards="medium",  # Will be calculated later
                    weighted_score=0.0,  # Will be calculated later
                    regional_boost=1.0,  # Will be calculated later
                    detected_regions=[]  # Will be calculated later
            )
            articles.append(article)
            except Exception as e:
                print(f"Error parsing Google CSE article: {e}")
                continue
        
        return articles
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on URL and title similarity"""
        seen_urls = set()
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            url_hash = self._get_url_hash(article.url)
            normalized_title = self._normalize_headline(article.title)
            
            if url_hash not in seen_urls and normalized_title not in seen_titles:
                seen_urls.add(url_hash)
                seen_titles.add(normalized_title)
                unique_articles.append(article)
        
        return unique_articles
    
    def _get_url_hash(self, url: str) -> str:
        """Generate hash for URL comparison"""
        try:
            parsed = urlparse(url)
            # Remove query parameters and fragments for better deduplication
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            return hashlib.md5(clean_url.encode()).hexdigest()
        except:
            return hashlib.md5(url.encode()).hexdigest()
    
    def _normalize_headline(self, headline: str) -> str:
        """Normalize headline for comparison"""
        if not headline:
            return ""
        
        # Remove common prefixes and suffixes
        normalized = headline.lower()
        normalized = re.sub(r'^(breaking|update|exclusive|just in|developing):\s*', '', normalized)
        normalized = re.sub(r'\s*[-–—]\s*.*$', '', normalized)  # Remove everything after dash
        
        # Remove punctuation and extra whitespace
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def get_regional_experts(self, region: str) -> List[str]:
        """Get list of expert sources for a specific region"""
        return source_weights.get_regional_experts(region)
    
    def get_credibility_ranking(self, min_weight: float = 0.7) -> List[Tuple[str, float]]:
        """Get ranked list of sources by credibility"""
        return source_weights.get_credibility_ranking(min_weight)

# Example usage
async def main():
    """Example usage of the enhanced news fetcher"""
    async with MultiSourceNewsFetcher() as fetcher:
        print("🔍 Fetching news with regional intelligence...")
        
        # Fetch general news
        articles = await fetcher.fetch_category_news("general", 15)
        
        print(f"📰 Found {len(articles)} articles")
        
        # Display top articles with regional information
        for i, article in enumerate(articles[:5], 1):
            print(f"\n{i}. {article.title}")
            print(f"   Source: {article.source} ({article.source_category})")
            print(f"   Weight: {article.weighted_score:.3f}")
            print(f"   Regional Boost: {article.regional_boost:.2f}x")
            if article.detected_regions:
                print(f"   Regions: {', '.join(article.detected_regions)}")
            print(f"   URL: {article.url}")
        
        # Show regional experts
        print(f"\n🌍 Regional Expert Sources:")
        for region in ['north_america', 'europe', 'asia', 'middle_east']:
            experts = fetcher.get_regional_experts(region)
            print(f"   {region.replace('_', ' ').title()}: {len(experts)} sources")

if __name__ == "__main__":
    asyncio.run(main())
