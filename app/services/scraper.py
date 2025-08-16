import logging
import requests
from typing import List, Dict
from urllib.parse import urlparse
import re

from app.core.config import settings

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; VeritasBot/1.0; +https://yourdomain.com/bot)"
}

# Known source mappings for better display names
SOURCE_MAPPINGS = {
    'reuters.com': 'Reuters',
    'bbc.com': 'BBC News',
    'bbc.co.uk': 'BBC News',
    'cnn.com': 'CNN',
    'nytimes.com': 'The New York Times',
    'washingtonpost.com': 'The Washington Post',
    'theguardian.com': 'The Guardian',
    'apnews.com': 'Associated Press',
    'bloomberg.com': 'Bloomberg',
    'wsj.com': 'The Wall Street Journal',
    'ft.com': 'Financial Times',
    'npr.org': 'NPR',
    'aljazeera.com': 'Al Jazeera',
    'dw.com': 'Deutsche Welle',
    'economist.com': 'The Economist',
    'thehindu.com': 'The Hindu',
    'indianexpress.com': 'The Indian Express',
    'business-standard.com': 'Business Standard',
    'cnbc.com': 'CNBC',
    'foxnews.com': 'Fox News',
    'abcnews.go.com': 'ABC News',
    'cbsnews.com': 'CBS News',
    'nbcnews.com': 'NBC News',
    'usatoday.com': 'USA Today',
    'politico.com': 'Politico',
    'huffpost.com': 'HuffPost',
    'buzzfeed.com': 'BuzzFeed',
    'vox.com': 'Vox',
    'slate.com': 'Slate',
    'theatlantic.com': 'The Atlantic',
    'newyorker.com': 'The New Yorker',
    'time.com': 'Time',
    'newsweek.com': 'Newsweek',
    'espn.com': 'ESPN',
    'variety.com': 'Variety',
    'rollingstone.com': 'Rolling Stone',
    'ew.com': 'Entertainment Weekly'
}

def extract_source_name(url: str, display_link: str = "") -> str:
    """Extract a clean source name from URL or display link"""
    try:
        # Use display_link if available (it's usually cleaner)
        if display_link:
            domain = display_link.lower()
        else:
            # Parse URL to get domain
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

        # Remove www. prefix
        domain = re.sub(r'^www\.', '', domain)

        # Check if we have a known mapping
        if domain in SOURCE_MAPPINGS:
            return SOURCE_MAPPINGS[domain]

        # For unknown domains, create a readable name
        # Remove common TLD extensions and capitalize
        clean_name = re.sub(r'\.(com|org|net|co\.uk|co\.in|in)$', '', domain)
        clean_name = clean_name.replace('.', ' ').title()

        return clean_name

    except Exception as e:
        logger.warning(f"Failed to extract source name from {url}: {e}")
        return "Unknown Source"

def extract_published_date(item: dict) -> str:
    """Extract published date from Google search result item"""
    try:
        # Google sometimes provides date in pagemap or other metadata
        pagemap = item.get('pagemap', {})

        # Try different possible date fields
        date_fields = [
            'metatags',
            'article',
            'newsarticle',
            'webpage'
        ]

        for field in date_fields:
            if field in pagemap:
                for meta in pagemap[field]:
                    # Look for common date meta tags
                    date_keys = [
                        'datePublished',
                        'publishedTime',
                        'article:published_time',
                        'pubdate',
                        'date'
                    ]

                    for key in date_keys:
                        if key in meta and meta[key]:
                            return meta[key]

        # Fallback: try to extract from snippet or title
        snippet = item.get('snippet', '')
        if 'ago' in snippet.lower():
            # Look for patterns like "2 hours ago", "3 days ago"
            import re
            time_pattern = r'(\d+)\s+(hour|day|week|month)s?\s+ago'
            match = re.search(time_pattern, snippet.lower())
            if match:
                return f"{match.group(1)} {match.group(2)}s ago"

        return "Recent"

    except Exception as e:
        logger.warning(f"Failed to extract date: {e}")
        return "Unknown"

def fetch_articles_from_google(query: str, num_results: int = 8) -> List[Dict]:
    """Fetches articles using Google Custom Search API"""
    logger.info(f"🌐 Querying Google CSE: {query}")

    # Debug: Check if API credentials are loaded
    logger.info(f"🔧 [SCRAPER] API Key present: {'Yes' if settings.GOOGLE_API_KEY else 'No'}")
    logger.info(f"🔧 [SCRAPER] CSE ID present: {'Yes' if settings.GOOGLE_CSE_ID else 'No'}")

    if not settings.GOOGLE_API_KEY or not settings.GOOGLE_CSE_ID:
        logger.error("❌ Google API credentials not configured properly")
        return []

    try:
        url = (
            f"https://www.googleapis.com/customsearch/v1?"
            f"key={settings.GOOGLE_API_KEY}&cx={settings.GOOGLE_CSE_ID}&q={query}"
        )

        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # Raise HTTP errors early
        data = response.json()

        if "items" not in data:
            logger.warning(f"⚠️ No items in response. Full response: {data}")
            return []

        articles = []
        seen_links = set()
        for item in data["items"][:num_results * 2]:  # over-fetch then filter
            link = item.get("link")
            if not link or link in seen_links:
                continue
            seen_links.add(link)
            snippet = item.get("snippet", "") or ""
            if len(snippet) < 80:  # low-content early skip
                continue

            # Extract source name from URL or displayLink
            source = extract_source_name(item.get("link", ""), item.get("displayLink", ""))

            articles.append({
                "title": item.get("title"),
                "snippet": snippet,
                "link": link,
                "source": source,
                "displayLink": item.get("displayLink"),
                "published_date": extract_published_date(item),
            })

            if len(articles) >= num_results:
                break

        logger.info(f"✅ Retrieved {len(articles)} articles.")
        return articles

    except Exception as e:
        logger.error(f"❌ Error fetching articles: {e}")
        return []
