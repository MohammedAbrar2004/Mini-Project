"""
Weighted Truth and Confidence Scoring System
Implements sophisticated scoring based on source weights, recency, and diversity
"""

import logging
from typing import List, Dict, Tuple
from datetime import datetime
from collections import defaultdict
from .news_source_weights import news_weights

logger = logging.getLogger(__name__)

class WeightedScoring:
    """
    Advanced scoring system that calculates:
    1. Weighted Truth Score based on source credibility and agreement
    2. Composite Confidence Score based on quantity, diversity, and recency
    """
    
    def __init__(self):
        self.weights_system = news_weights
    
    def calculate_weighted_truth_score(self, claim: str, articles: List[Dict]) -> Tuple[float, Dict]:
        """
        Calculate weighted truth score using the formula:
        Truth Score = (Σ(weight × agrees) / Σweights) × 100
        """
        if not articles:
            return 0.0, {"total_weight": 0, "supporting_weight": 0, "articles_analyzed": 0}
        
        claim_category = self.weights_system.get_category_from_claim(claim)
        claim_region = self.weights_system.get_region_from_claim(claim)
        
        total_weight = 0.0
        supporting_weight = 0.0
        article_details = []
        
        for article in articles:
            source_weight = self.weights_system.calculate_source_weight(
                article.get('url', ''),
                claim_category,
                claim_region
            )
            recency_factor = self.weights_system.calculate_recency_factor(
                article.get('published_date', '')
            )
            similarity_score = article.get('similarity_score', 0.5)
            combined_weight = source_weight * recency_factor * similarity_score
            
            # Prefer explicit stance tag when available
            stance = article.get('stance')
            if stance == 'supporting':
                agrees = True
            elif stance == 'contradicting':
                agrees = False
            else:
                # Fallback to similarity proxy
                agrees = similarity_score > 0.7
            
            total_weight += combined_weight
            if agrees:
                supporting_weight += combined_weight
            
            article_details.append({
                'url': article.get('url', ''),
                'source_weight': source_weight,
                'recency_factor': recency_factor,
                'similarity_score': similarity_score,
                'combined_weight': combined_weight,
                'agrees': agrees,
                'stance': stance
            })
        
        truth_score = (supporting_weight / total_weight * 100) if total_weight > 0 else 0.0
        
        details = {
            "total_weight": total_weight,
            "supporting_weight": supporting_weight,
            "articles_analyzed": len(articles),
            "claim_category": claim_category,
            "claim_region": claim_region,
            "article_details": article_details
        }
        
        logger.info(f"📊 Weighted Truth Score: {truth_score:.1f}% (Supporting: {supporting_weight:.2f}, Total: {total_weight:.2f})")
        
        return truth_score, details
    
    def calculate_composite_confidence_score(self, articles: List[Dict]) -> Tuple[float, Dict]:
        """
        Calculate composite confidence score using the formula:
        Confidence = (0.4 × Quantity) + (0.3 × Source Diversity) + (0.3 × Recency) × 100
        """
        if not articles:
            return 0.0, {"quantity": 0, "diversity": 0, "recency": 0}
        
        # 1. Quantity Score (capped at 10 articles)
        quantity_score = min(len(articles) / 10.0, 1.0)
        
        # 2. Source Diversity Score (capped at 5 unique sources)
        unique_sources = set()
        for article in articles:
            domain = self.weights_system.extract_domain(article.get('url', ''))
            if domain:
                unique_sources.add(domain)
        diversity_score = min(len(unique_sources) / 5.0, 1.0)
        
        # 3. Recency Score (average recency of all articles)
        recency_scores = []
        for article in articles:
            recency = self.weights_system.calculate_recency_factor(
                article.get('published_date', '')
            )
            recency_scores.append(recency)
        avg_recency = sum(recency_scores) / len(recency_scores) if recency_scores else 0.0
        
        confidence_score = (
            0.4 * quantity_score +
            0.3 * diversity_score + 
            0.3 * avg_recency
        ) * 100
        
        details = {
            "quantity": quantity_score,
            "diversity": diversity_score,
            "recency": avg_recency,
            "article_count": len(articles),
            "unique_sources": len(unique_sources),
            "source_list": list(unique_sources)
        }
        
        logger.info(f"🎯 Composite Confidence: {confidence_score:.1f}% (Q:{quantity_score:.2f}, D:{diversity_score:.2f}, R:{avg_recency:.2f})")
        
        return confidence_score, details
    
    def calculate_comprehensive_scores(self, claim: str, supporting_articles: List[Dict], 
                                     contradicting_articles: List[Dict]) -> Dict:
        all_articles = supporting_articles + contradicting_articles
        for article in supporting_articles:
            article['stance'] = 'supporting'
        for article in contradicting_articles:
            article['stance'] = 'contradicting'
        
        truth_score, truth_details = self.calculate_weighted_truth_score(claim, all_articles)
        confidence_score, confidence_details = self.calculate_composite_confidence_score(all_articles)
        verdict = self._determine_verdict(truth_score, confidence_score)
        
        return {
            "truth_score": truth_score / 100.0,
            "confidence_score": confidence_score / 100.0,
            "verdict": verdict,
            "truth_details": truth_details,
            "confidence_details": confidence_details,
            "supporting_count": len(supporting_articles),
            "contradicting_count": len(contradicting_articles),
            "total_articles": len(all_articles)
        }
    
    def _determine_verdict(self, truth_score: float, confidence_score: float) -> str:
        # High confidence verdicts
        if confidence_score >= 80:
            if truth_score >= 80:
                return "MOST_LIKELY_TRUE"
            elif truth_score <= 20:
                return "LIKELY_FALSE"
            else:
                return "INCONCLUSIVE_MIXED"
        elif confidence_score >= 50:
            if truth_score >= 70:
                return "LIKELY_TRUE_NEEDS_SUPPORT"
            elif truth_score <= 30:
                return "LIKELY_FALSE"
            else:
                return "INCONCLUSIVE_MIXED"
        else:
            return "INSUFFICIENT_DATA"

# Global instance
weighted_scorer = WeightedScoring()
