"""
Sophisticated Content Analyzer
Analyzes scraped content for context, region, time, and creates structured JSON for LLM
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import spacy
from textstat import flesch_reading_ease, flesch_kincaid_grade
from fuzzywuzzy import fuzz
import numpy as np
from collections import Counter
import asyncio

from config import config
from enhanced_web_scraper import EnhancedArticle

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentAnalysis:
    """Comprehensive content analysis result"""
    original_claim: str
    total_articles: int
    supporting_articles: List[Dict[str, Any]]
    contradicting_articles: List[Dict[str, Any]]
    neutral_articles: List[Dict[str, Any]]
    regional_analysis: Dict[str, Any]
    temporal_analysis: Dict[str, Any]
    source_credibility_analysis: Dict[str, Any]
    content_similarity_scores: List[float]
    key_entities: List[Dict[str, Any]]
    sentiment_analysis: Dict[str, Any]
    structured_json_for_llm: Dict[str, Any]
    processing_time: float

class ContentAnalyzer:
    """Sophisticated content analyzer for fact-checking"""
    
    def __init__(self):
        self.nlp = None
        self.load_nlp_model()
        
    def load_nlp_model(self):
        """Load spaCy NLP model"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("✅ spaCy model loaded for content analysis")
        except OSError:
            logger.warning("⚠️ spaCy model not found. Some features will be limited.")
            self.nlp = None
    
    async def analyze_content(self, claim: str, articles: List[EnhancedArticle]) -> ContentAnalysis:
        """
        Perform comprehensive content analysis
        
        Args:
            claim: Original claim to verify
            articles: List of scraped articles
            
        Returns:
            ContentAnalysis with detailed analysis results
        """
        import time
        start_time = time.time()
        
        logger.info(f"🔍 Analyzing content for {len(articles)} articles...")
        
        # Step 1: Categorize articles by stance
        supporting, contradicting, neutral = await self._categorize_articles_by_stance(claim, articles)
        
        # Step 2: Regional analysis
        regional_analysis = self._analyze_regional_context(articles)
        
        # Step 3: Temporal analysis
        temporal_analysis = self._analyze_temporal_context(articles)
        
        # Step 4: Source credibility analysis
        credibility_analysis = self._analyze_source_credibility(articles)
        
        # Step 5: Content similarity analysis
        similarity_scores = self._calculate_content_similarity(claim, articles)
        
        # Step 6: Extract key entities
        key_entities = self._extract_key_entities(claim, articles)
        
        # Step 7: Sentiment analysis
        sentiment_analysis = self._analyze_sentiment(articles)
        
        # Step 8: Create structured JSON for LLM
        structured_json = self._create_structured_json_for_llm(
            claim, supporting, contradicting, neutral, 
            regional_analysis, temporal_analysis, credibility_analysis
        )
        
        processing_time = time.time() - start_time
        
        result = ContentAnalysis(
            original_claim=claim,
            total_articles=len(articles),
            supporting_articles=supporting,
            contradicting_articles=contradicting,
            neutral_articles=neutral,
            regional_analysis=regional_analysis,
            temporal_analysis=temporal_analysis,
            source_credibility_analysis=credibility_analysis,
            content_similarity_scores=similarity_scores,
            key_entities=key_entities,
            sentiment_analysis=sentiment_analysis,
            structured_json_for_llm=structured_json,
            processing_time=processing_time
        )
        
        logger.info(f"✅ Content analysis complete in {processing_time:.2f}s")
        logger.info(f"📊 Supporting: {len(supporting)}, Contradicting: {len(contradicting)}, Neutral: {len(neutral)}")
        
        return result
    
    async def _categorize_articles_by_stance(self, claim: str, articles: List[EnhancedArticle]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Categorize articles as supporting, contradicting, or neutral"""
        supporting = []
        contradicting = []
        neutral = []
        
        claim_lower = claim.lower()
        claim_neg = self._has_negation(claim_lower)
        claim_entities = set(self._extract_simple_entities(claim_lower))
        
        for article in articles:
            article_dict = self._article_to_dict(article)
            
            similarity_score = self._calculate_semantic_similarity(claim, article.content)
            article_dict['similarity_score'] = similarity_score
            
            stance_score = self._analyze_stance(claim, article.content)
            article_dict['stance_score'] = stance_score
            
            content_lower = (article.content or '').lower()
            content_neg = self._has_negation(content_lower)
            content_entities = set(self._extract_simple_entities(content_lower))
            
            # Entity mismatch penalty: if main entities don't overlap, reduce stance confidence
            entity_overlap = len(claim_entities & content_entities)
            if entity_overlap == 0 and similarity_score < 0.7:
                stance_score *= 0.5
            
            # Negation flip: if polarity differs and similarity is decent, flip towards contradiction
            if claim_neg != content_neg and similarity_score >= 0.5:
                stance_score = min(-abs(stance_score), -0.3)
            
            # Categorize
            if stance_score > 0.3:
                article_dict['stance'] = 'supporting'
                supporting.append(article_dict)
            elif stance_score < -0.3:
                article_dict['stance'] = 'contradicting'
                contradicting.append(article_dict)
            else:
                article_dict['stance'] = 'neutral'
                neutral.append(article_dict)
        
        return supporting, contradicting, neutral
    
    def _has_negation(self, text: str) -> bool:
        tokens = set(re.findall(r"\b[\w'-]+\b", text))
        neg = {"not", "no", "never", "without", "false", "deny", "denies", "refute", "refutes", "debunk", "myth"}
        return any(t in tokens for t in neg)
    
    def _extract_simple_entities(self, text: str) -> List[str]:
        # Lightweight entity proxy: proper nouns and capitalized words
        return re.findall(r"\b[A-Z][a-zA-Z0-9_-]{2,}\b", text)
    
    def _analyze_stance(self, claim: str, content: str) -> float:
        """Analyze stance of content towards claim (-1 to 1) with negation and fuzzy cues."""
        if not content:
            return 0.0
        
        claim_lower = claim.lower()
        content_lower = content.lower()
        
        support_keywords = ['confirm', 'verify', 'true', 'accurate', 'correct', 'validates', 'supports']
        contradict_keywords = ['false', 'fake', 'incorrect', 'debunk', 'refute', 'deny', 'dispute', 'not']
        
        support_count = sum(1 for keyword in support_keywords if keyword in content_lower)
        contradict_count = sum(1 for keyword in contradict_keywords if keyword in content_lower)
        
        fuzzy_similarity = fuzz.partial_ratio(claim_lower, content_lower) / 100.0
        
        score = (support_count - contradict_count) * 0.15 + (fuzzy_similarity - 0.5) * 0.6
        return max(-1.0, min(1.0, score))
    
    def _calculate_semantic_similarity(self, claim: str, content: str) -> float:
        """Calculate semantic similarity between claim and content"""
        if not self.nlp or not content:
            return 0.0
        
        try:
            claim_doc = self.nlp(claim)
            content_doc = self.nlp(content[:1000])  # Limit content length
            
            return claim_doc.similarity(content_doc)
        except:
            # Fallback to fuzzy matching
            return fuzz.partial_ratio(claim.lower(), content.lower()) / 100.0
    
    def _analyze_regional_context(self, articles: List[EnhancedArticle]) -> Dict[str, Any]:
        """Analyze regional context of articles"""
        regions = []
        sources_by_region = {}
        
        for article in articles:
            region = self._extract_region_from_source(article.source)
            if region:
                regions.append(region)
                if region not in sources_by_region:
                    sources_by_region[region] = []
                sources_by_region[region].append(article.source)
        
        region_counts = Counter(regions)
        
        return {
            'dominant_regions': dict(region_counts.most_common(5)),
            'total_regions': len(region_counts),
            'sources_by_region': sources_by_region,
            'regional_diversity_score': len(region_counts) / max(len(articles), 1)
        }
    
    def _extract_region_from_source(self, source: str) -> Optional[str]:
        """Extract region from source domain"""
        region_mapping = {
            '.uk': 'United Kingdom',
            '.au': 'Australia',
            '.ca': 'Canada',
            '.in': 'India',
            '.de': 'Germany',
            '.fr': 'France',
            '.jp': 'Japan',
            '.cn': 'China',
            '.br': 'Brazil',
            '.za': 'South Africa'
        }
        
        for tld, region in region_mapping.items():
            if source.endswith(tld):
                return region
        
        # Default to US for .com and others
        if any(us_indicator in source for us_indicator in ['cnn', 'nytimes', 'washingtonpost', 'npr']):
            return 'United States'
        
        return 'International'
    
    def _analyze_temporal_context(self, articles: List[EnhancedArticle]) -> Dict[str, Any]:
        """Analyze temporal context of articles"""
        dates = []
        articles_with_dates = 0
        
        for article in articles:
            if article.published_date:
                dates.append(article.published_date)
                articles_with_dates += 1
        
        if not dates:
            return {
                'articles_with_dates': 0,
                'date_range': None,
                'temporal_clustering': {},
                'recency_score': 0.0
            }
        
        dates.sort()
        date_range = {
            'earliest': dates[0].isoformat(),
            'latest': dates[-1].isoformat(),
            'span_days': (dates[-1] - dates[0]).days
        }
        
        # Analyze temporal clustering
        now = datetime.now()
        time_buckets = {
            'last_24h': 0,
            'last_week': 0,
            'last_month': 0,
            'older': 0
        }
        
        for date in dates:
            days_ago = (now - date.replace(tzinfo=None)).days
            if days_ago <= 1:
                time_buckets['last_24h'] += 1
            elif days_ago <= 7:
                time_buckets['last_week'] += 1
            elif days_ago <= 30:
                time_buckets['last_month'] += 1
            else:
                time_buckets['older'] += 1
        
        # Calculate recency score
        recent_articles = time_buckets['last_24h'] + time_buckets['last_week']
        recency_score = recent_articles / max(len(dates), 1)
        
        return {
            'articles_with_dates': articles_with_dates,
            'date_range': date_range,
            'temporal_clustering': time_buckets,
            'recency_score': recency_score
        }
    
    def _analyze_source_credibility(self, articles: List[EnhancedArticle]) -> Dict[str, Any]:
        """Analyze source credibility distribution"""
        credibility_scores = [article.credibility_score for article in articles]
        sources = [article.source for article in articles]
        
        source_credibility = {}
        for article in articles:
            if article.source not in source_credibility:
                source_credibility[article.source] = []
            source_credibility[article.source].append(article.credibility_score)
        
        # Calculate average credibility per source
        avg_source_credibility = {
            source: np.mean(scores) 
            for source, scores in source_credibility.items()
        }
        
        return {
            'overall_credibility_score': np.mean(credibility_scores) if credibility_scores else 0.0,
            'credibility_distribution': {
                'high': len([s for s in credibility_scores if s >= 0.7]),
                'medium': len([s for s in credibility_scores if 0.4 <= s < 0.7]),
                'low': len([s for s in credibility_scores if s < 0.4])
            },
            'source_credibility_scores': avg_source_credibility,
            'most_credible_sources': sorted(avg_source_credibility.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def _calculate_content_similarity(self, claim: str, articles: List[EnhancedArticle]) -> List[float]:
        """Calculate content similarity scores"""
        similarity_scores = []
        
        for article in articles:
            score = self._calculate_semantic_similarity(claim, article.content)
            similarity_scores.append(score)
        
        return similarity_scores
    
    def _extract_key_entities(self, claim: str, articles: List[EnhancedArticle]) -> List[Dict[str, Any]]:
        """Extract key entities from claim and articles"""
        if not self.nlp:
            return []
        
        all_text = claim + " " + " ".join([article.content for article in articles[:10]])
        doc = self.nlp(all_text)
        
        entity_counts = Counter()
        entity_info = {}
        
        for ent in doc.ents:
            if len(ent.text) > 2 and ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT']:
                entity_counts[ent.text] += 1
                entity_info[ent.text] = {
                    'label': ent.label_,
                    'description': spacy.explain(ent.label_)
                }
        
        key_entities = []
        for entity, count in entity_counts.most_common(10):
            key_entities.append({
                'text': entity,
                'count': count,
                'label': entity_info[entity]['label'],
                'description': entity_info[entity]['description']
            })
        
        return key_entities
    
    def _analyze_sentiment(self, articles: List[EnhancedArticle]) -> Dict[str, Any]:
        """Analyze sentiment of articles (simplified)"""
        # This is a simplified sentiment analysis
        # In production, you'd use a proper sentiment analysis model
        
        positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'win', 'victory']
        negative_words = ['bad', 'terrible', 'negative', 'fail', 'loss', 'defeat', 'crisis']
        
        sentiment_scores = []
        
        for article in articles:
            content_lower = article.content.lower()
            positive_count = sum(1 for word in positive_words if word in content_lower)
            negative_count = sum(1 for word in negative_words if word in content_lower)
            
            if positive_count + negative_count > 0:
                sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            else:
                sentiment = 0.0
            
            sentiment_scores.append(sentiment)
        
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
        
        return {
            'average_sentiment': avg_sentiment,
            'sentiment_distribution': {
                'positive': len([s for s in sentiment_scores if s > 0.1]),
                'neutral': len([s for s in sentiment_scores if -0.1 <= s <= 0.1]),
                'negative': len([s for s in sentiment_scores if s < -0.1])
            }
        }
    
    def _create_structured_json_for_llm(self, claim: str, supporting: List[Dict], 
                                      contradicting: List[Dict], neutral: List[Dict],
                                      regional: Dict, temporal: Dict, credibility: Dict) -> Dict[str, Any]:
        """Create sophisticated JSON structure for LLM analysis"""
        
        structured_data = {
            "claim_analysis": {
                "original_claim": claim,
                "claim_length": len(claim),
                "claim_complexity": self._assess_claim_complexity(claim)
            },
            "evidence_summary": {
                "total_sources": len(supporting) + len(contradicting) + len(neutral),
                "supporting_sources": len(supporting),
                "contradicting_sources": len(contradicting),
                "neutral_sources": len(neutral),
                "support_ratio": len(supporting) / max(len(supporting) + len(contradicting), 1)
            },
            "source_analysis": {
                "credibility_distribution": credibility['credibility_distribution'],
                "overall_credibility": credibility['overall_credibility_score'],
                "most_credible_sources": credibility['most_credible_sources'][:3]
            },
            "temporal_context": {
                "recency_score": temporal['recency_score'],
                "temporal_clustering": temporal['temporal_clustering'],
                "articles_with_dates": temporal['articles_with_dates']
            },
            "regional_context": {
                "regional_diversity": regional['regional_diversity_score'],
                "dominant_regions": regional['dominant_regions'],
                "total_regions": regional['total_regions']
            },
            "detailed_evidence": {
                "supporting_articles": supporting[:5],  # Top 5 supporting
                "contradicting_articles": contradicting[:5],  # Top 5 contradicting
                "neutral_articles": neutral[:3]  # Top 3 neutral
            },
            "analysis_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "confidence_indicators": self._calculate_confidence_indicators(
                    supporting, contradicting, neutral, credibility, temporal, regional
                )
            }
        }
        
        return structured_data
    
    def _assess_claim_complexity(self, claim: str) -> str:
        """Assess complexity of the claim"""
        if len(claim) < 50:
            return "simple"
        elif len(claim) < 150:
            return "moderate"
        else:
            return "complex"
    
    def _calculate_confidence_indicators(self, supporting: List, contradicting: List, 
                                       neutral: List, credibility: Dict, 
                                       temporal: Dict, regional: Dict) -> Dict[str, float]:
        """Calculate confidence indicators for the analysis"""
        
        total_articles = len(supporting) + len(contradicting) + len(neutral)
        
        indicators = {
            "source_quantity": min(total_articles / 10, 1.0),  # Normalize to 10 articles
            "source_credibility": credibility['overall_credibility_score'],
            "temporal_relevance": temporal['recency_score'],
            "regional_diversity": regional['regional_diversity_score'],
            "evidence_consistency": abs(len(supporting) - len(contradicting)) / max(total_articles, 1)
        }
        
        return indicators
    
    def _article_to_dict(self, article: EnhancedArticle) -> Dict[str, Any]:
        """Convert EnhancedArticle to dictionary"""
        return {
            'title': article.title,
            'source': article.source,
            'url': article.url,
            'content_snippet': article.content[:300],
            'published_date': article.published_date.isoformat() if article.published_date else None,
            'credibility_score': article.credibility_score,
            'author': article.author
        }

# Convenience function
async def analyze_content(claim: str, articles: List[EnhancedArticle]) -> ContentAnalysis:
    """
    Analyze content for fact-checking
    
    Args:
        claim: Original claim to verify
        articles: List of enhanced articles
        
    Returns:
        ContentAnalysis with comprehensive analysis
    """
    analyzer = ContentAnalyzer()
    return await analyzer.analyze_content(claim, articles)
