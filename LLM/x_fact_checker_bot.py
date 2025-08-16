"""
Automated X/Twitter Fact-Checking Bot for TruthScope
Monitors mentions, extracts claims, and auto-replies with verification results
"""

import tweepy
import asyncio
import logging
import re
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from dataclasses import dataclass
from urllib.parse import urlparse
import hashlib

# Import TruthScope components
from .news_source_weights import source_weights
from .enhanced_web_scraper import EnhancedWebScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('x_fact_checker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TweetMention:
    """Data class for tweet mentions"""
    tweet_id: str
    user_id: str
    username: str
    text: str
    created_at: datetime
    is_retweet: bool
    is_quote: bool
    language: str
    urls: List[str]
    hashtags: List[str]

@dataclass
class FactCheckResult:
    """Data class for fact-checking results"""
    claim: str
    verdict: str  # 'true', 'false', 'misleading', 'unverified'
    confidence: float  # 0.0 to 1.0
    credibility_score: float
    explanation: str
    sources: List[Dict]
    processing_time: float
    timestamp: datetime

class XFactCheckerBot:
    """Automated X/Twitter fact-checking bot"""
    
    def __init__(self):
        self.api = None
        self.client = None
        self.scraper = None
        self.processed_mentions = set()
        self.rate_limit_delay = 30  # seconds between API calls
        self.last_mention_check = None
        self.bot_username = "TruthScopeBot"  # Change this to your bot's username
        
        # Initialize Twitter API
        self._initialize_twitter_api()
        
        # Initialize web scraper for fact-checking
        self._initialize_scraper()
        
        # Load configuration
        self.config = self._load_config()
        
    def _initialize_twitter_api(self):
        """Initialize Twitter API v2 client"""
        try:
            # API v2 Client (for reading)
            self.client = tweepy.Client(
                bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
                consumer_key=os.getenv('TWITTER_API_KEY'),
                consumer_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
                wait_on_rate_limit=True
            )
            
            # API v1.1 (for replying)
            auth = tweepy.OAuthHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET')
            )
            auth.set_access_token(
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            logger.info("✅ Twitter API initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Twitter API: {e}")
            raise
    
    def _initialize_scraper(self):
        """Initialize the web scraper for fact-checking"""
        try:
            self.scraper = EnhancedWebScraper()
            logger.info("✅ Web scraper initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize web scraper: {e}")
            self.scraper = None
    
    def _load_config(self) -> Dict:
        """Load bot configuration"""
        return {
            'mention_keywords': [
                'fact check', 'is this true', 'verify', 'truth', 'real news',
                'fake news', 'hoax', 'debunk', 'factcheck', 'verification'
            ],
            'excluded_words': [
                'bot', 'automated', 'spam', 'test', 'hello', 'hi'
            ],
            'max_reply_length': 280,
            'min_confidence_threshold': 0.6,
            'cooldown_minutes': 5,  # Don't reply to same user too frequently
            'max_daily_replies': 100
        }
    
    def start_monitoring(self):
        """Start monitoring for mentions"""
        logger.info("🚀 Starting X Fact-Checking Bot...")
        logger.info(f"🤖 Bot username: @{self.bot_username}")
        
        while True:
            try:
                # Check for new mentions
                mentions = self._get_mentions()
                
                for mention in mentions:
                    if self._should_process_mention(mention):
                        self._process_mention(mention)
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _get_mentions(self) -> List[TweetMention]:
        """Get recent mentions of the bot"""
        try:
            # Get mentions timeline
            mentions = self.client.get_users_mentions(
                id=self.client.get_me().data.id,
                max_results=20,
                tweet_fields=['created_at', 'lang', 'entities']
            )
            
            if not mentions.data:
                return []
            
            tweet_mentions = []
            for tweet in mentions.data:
                # Skip if already processed
                if tweet.id in self.processed_mentions:
                    continue
                
                # Extract URLs and hashtags
                urls = []
                hashtags = []
                if tweet.entities:
                    if 'urls' in tweet.entities:
                        urls = [url['expanded_url'] for url in tweet.entities['urls']]
                    if 'hashtags' in tweet.entities:
                        hashtags = [tag['tag'] for tag in tweet.entities['hashtags']]
                
                mention = TweetMention(
                    tweet_id=str(tweet.id),
                    user_id=str(tweet.author_id),
                    username=self._get_username_by_id(tweet.author_id),
                    text=tweet.text,
                    created_at=tweet.created_at,
                    is_retweet=False,  # Simplified for now
                    is_quote=False,    # Simplified for now
                    language=tweet.lang or 'en',
                    urls=urls,
                    hashtags=hashtags
                )
                
                tweet_mentions.append(mention)
            
            return tweet_mentions
            
        except Exception as e:
            logger.error(f"❌ Error getting mentions: {e}")
            return []
    
    def _get_username_by_id(self, user_id: str) -> str:
        """Get username from user ID"""
        try:
            user = self.client.get_user(id=user_id)
            return user.data.username
        except:
            return "unknown_user"
    
    def _should_process_mention(self, mention: TweetMention) -> bool:
        """Determine if a mention should be processed"""
        # Skip if already processed
        if mention.tweet_id in self.processed_mentions:
            return False
        
        # Skip if not in English (for now)
        if mention.language != 'en':
            return False
        
        # Check if it contains fact-checking keywords
        text_lower = mention.text.lower()
        
        # Must contain fact-checking keywords
        has_keywords = any(keyword in text_lower for keyword in self.config['mention_keywords'])
        if not has_keywords:
            return False
        
        # Must not contain excluded words
        has_excluded = any(word in text_lower for word in self.config['excluded_words'])
        if has_excluded:
            return False
        
        # Check cooldown (don't spam same user)
        if self._is_user_in_cooldown(mention.user_id):
            return False
        
        return True
    
    def _is_user_in_cooldown(self, user_id: str) -> bool:
        """Check if user is in cooldown period"""
        # This is a simplified implementation
        # In production, you'd want to store this in a database
        return False
    
    def _process_mention(self, mention: TweetMention):
        """Process a mention and generate fact-check reply"""
        try:
            logger.info(f"🔍 Processing mention from @{mention.username}: {mention.text[:100]}...")
            
            # Extract the claim to fact-check
            claim = self._extract_claim(mention.text)
            if not claim:
                logger.info(f"⚠️ No claim found in mention from @{mention.username}")
                return
            
            # Perform fact-checking
            fact_check_result = self._fact_check_claim(claim)
            if not fact_check_result:
                logger.error(f"❌ Failed to fact-check claim: {claim}")
                return
            
            # Generate reply
            reply_text = self._generate_reply(fact_check_result, mention.username)
            
            # Post reply
            self._post_reply(reply_text, mention.tweet_id)
            
            # Mark as processed
            self.processed_mentions.add(mention.tweet_id)
            
            logger.info(f"✅ Fact-check completed for @{mention.username}")
            
        except Exception as e:
            logger.error(f"❌ Error processing mention: {e}")
    
    def _extract_claim(self, tweet_text: str) -> Optional[str]:
        """Extract the claim to fact-check from tweet text"""
        # Remove bot username and common phrases
        text = re.sub(r'@\w+', '', tweet_text)  # Remove usernames
        text = re.sub(r'#\w+', '', text)         # Remove hashtags
        text = re.sub(r'https?://\S+', '', text) # Remove URLs
        
        # Look for fact-checking patterns
        patterns = [
            r'is it true that (.+?)(?:\?|$|\.)',
            r'fact check (.+?)(?:\?|$|\.)',
            r'verify (.+?)(?:\?|$|\.)',
            r'is (.+?) true(?:\?|$|\.)',
            r'(.+?) - fact check(?:\?|$|\.)',
            r'(.+?) - verify(?:\?|$|\.)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                claim = match.group(1).strip()
                if len(claim) > 10:  # Minimum claim length
                    return claim
        
        # If no pattern matches, try to extract the main content
        sentences = text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and not any(word in sentence.lower() for word in ['fact check', 'verify', 'true']):
                return sentence
        
        return None
    
    def _fact_check_claim(self, claim: str) -> Optional[FactCheckResult]:
        """Perform fact-checking on a claim"""
        try:
            start_time = time.time()
            
            logger.info(f"🔍 Fact-checking claim: {claim}")
            
            # Use the enhanced web scraper to search for information
            if not self.scraper:
                logger.error("❌ Web scraper not available")
                return None
            
            # Search for the claim
            search_results = asyncio.run(self.scraper.search_claim(claim))
            
            # Analyze results and generate verdict
            verdict, confidence, explanation, sources = self._analyze_results(search_results, claim)
            
            # Calculate credibility score
            credibility_score = self._calculate_credibility_score(sources)
            
            processing_time = time.time() - start_time
            
            result = FactCheckResult(
                claim=claim,
                verdict=verdict,
                confidence=confidence,
                credibility_score=credibility_score,
                explanation=explanation,
                sources=sources,
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in fact-checking: {e}")
            return None
    
    def _analyze_results(self, search_results: List, claim: str) -> Tuple[str, float, str, List]:
        """Analyze search results to determine verdict"""
        if not search_results:
            return "unverified", 0.0, "No sources found to verify this claim.", []
        
        # Count positive vs negative results
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        sources = []
        for result in search_results[:5]:  # Top 5 results
            source_info = {
                'title': getattr(result, 'title', 'Unknown'),
                'url': getattr(result, 'url', ''),
                'source': getattr(result, 'source', 'Unknown'),
                'credibility': getattr(result, 'credibility_score', 0.5)
            }
            sources.append(source_info)
            
            # Simple sentiment analysis (this could be enhanced with NLP)
            title_lower = source_info['title'].lower()
            if any(word in title_lower for word in ['true', 'confirmed', 'verified', 'fact']):
                positive_count += 1
            elif any(word in title_lower for word in ['false', 'fake', 'hoax', 'debunked']):
                negative_count += 1
            else:
                neutral_count += 1
        
        # Determine verdict based on counts
        total = len(search_results)
        if total == 0:
            return "unverified", 0.0, "No sources found to verify this claim.", sources
        
        positive_ratio = positive_count / total
        negative_ratio = negative_count / total
        
        if positive_ratio > 0.6:
            verdict = "true"
            confidence = min(0.9, positive_ratio + 0.3)
            explanation = f"Multiple credible sources ({positive_count}/{total}) confirm this claim."
        elif negative_ratio > 0.6:
            verdict = "false"
            confidence = min(0.9, negative_ratio + 0.3)
            explanation = f"Multiple credible sources ({negative_count}/{total}) refute this claim."
        elif positive_ratio > negative_ratio:
            verdict = "likely true"
            confidence = 0.6 + (positive_ratio - negative_ratio) * 0.2
            explanation = f"More sources support this claim ({positive_count} vs {negative_count}), but verification is needed."
        elif negative_ratio > positive_ratio:
            verdict = "likely false"
            confidence = 0.6 + (negative_ratio - positive_ratio) * 0.2
            explanation = f"More sources refute this claim ({negative_count} vs {positive_count}), but verification is needed."
        else:
            verdict = "unverified"
            confidence = 0.5
            explanation = "Mixed evidence found. This claim requires further verification."
        
        return verdict, confidence, explanation, sources
    
    def _calculate_credibility_score(self, sources: List[Dict]) -> float:
        """Calculate overall credibility score based on sources"""
        if not sources:
            return 0.0
        
        total_score = 0.0
        for source in sources:
            # Get source weight from our weighting system
            source_weight = source_weights.get_source_weight(source['url'], source['source'])
            total_score += source_weight.weight
        
        return total_score / len(sources)
    
    def _generate_reply(self, result: FactCheckResult, username: str) -> str:
        """Generate a reply tweet with fact-check results"""
        # Create emoji for verdict
        verdict_emoji = {
            'true': '✅',
            'likely true': '🟢',
            'unverified': '🟡',
            'likely false': '🟠',
            'false': '❌'
        }.get(result.verdict, '❓')
        
        # Format confidence as percentage
        confidence_pct = int(result.confidence * 100)
        
        # Create reply text
        reply = f"🔍 FACT CHECK for @{username}:\n\n"
        reply += f"{verdict_emoji} VERDICT: {result.verdict.upper()}\n"
        reply += f"📊 Confidence: {confidence_pct}%\n"
        reply += f"🎯 Credibility: {int(result.credibility_score * 100)}%\n\n"
        
        # Add explanation (truncate if too long)
        explanation = result.explanation[:150] + "..." if len(result.explanation) > 150 else result.explanation
        reply += f"💡 {explanation}\n\n"
        
        # Add source count
        if result.sources:
            reply += f"📚 Sources: {len(result.sources)} verified\n"
        
        # Add processing time
        reply += f"⏱️ Processed in {result.processing_time:.1f}s\n\n"
        reply += f"🤖 Powered by @{self.bot_username} #TruthScope #FactCheck"
        
        # Ensure reply fits Twitter's character limit
        if len(reply) > 280:
            reply = reply[:277] + "..."
        
        return reply
    
    def _post_reply(self, reply_text: str, tweet_id: str):
        """Post a reply to a tweet"""
        try:
            # Post reply using API v1.1
            reply = self.api.update_status(
                status=reply_text,
                in_reply_to_status_id=tweet_id,
                auto_populate_reply_metadata=True
            )
            
            logger.info(f"✅ Reply posted successfully: {reply.id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to post reply: {e}")
    
    def get_bot_stats(self) -> Dict:
        """Get bot statistics"""
        return {
            'processed_mentions': len(self.processed_mentions),
            'uptime': datetime.now() - (self.last_mention_check or datetime.now()),
            'rate_limit_delay': self.rate_limit_delay,
            'bot_username': self.bot_username
        }

# Main execution
if __name__ == "__main__":
    try:
        # Create and start the bot
        bot = XFactCheckerBot()
        
        # Start monitoring
        bot.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        raise
