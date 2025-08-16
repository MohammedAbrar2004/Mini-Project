"""
Enhanced News Source Weighting System with Regional Intelligence
Provides weighted scoring for news sources based on credibility, bias, and regional relevance
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import re
from urllib.parse import urlparse
import json
import time
from datetime import datetime, timedelta

@dataclass
class SourceWeight:
    """Data class for source weighting information"""
    weight: float  # Base weight (0.0 to 1.0)
    category: str  # 'international', 'national', 'regional', 'local'
    bias_rating: str  # 'left', 'center-left', 'center', 'center-right', 'right'
    fact_checking: str  # 'excellent', 'good', 'fair', 'poor'
    editorial_standards: str  # 'high', 'medium', 'low'
    region: str  # Primary region/country of coverage
    languages: List[str]  # Languages of publication
    expertise_areas: List[str]  # Areas of specialized coverage
    verification_level: str  # 'verified', 'unverified', 'suspicious'
    credibility_multiplier: float = 1.0  # Additional credibility boost

class RegionalNewsMatcher:
    """Matches news content to relevant regional sources"""
    
    def __init__(self):
        # Regional keywords and their associated regions
        self.regional_keywords = {
            # North America
            'north_america': [
                'united states', 'usa', 'us', 'america', 'american', 'canada', 'canadian',
                'mexico', 'mexican', 'washington dc', 'new york', 'california', 'texas',
                'florida', 'ontario', 'quebec', 'british columbia', 'mexico city'
            ],
            'europe': [
                'europe', 'european', 'united kingdom', 'uk', 'britain', 'british',
                'germany', 'german', 'france', 'french', 'italy', 'italian', 'spain',
                'spanish', 'netherlands', 'dutch', 'sweden', 'swedish', 'norway',
                'norwegian', 'denmark', 'danish', 'poland', 'polish', 'russia',
                'russian', 'ukraine', 'ukrainian', 'london', 'berlin', 'paris',
                'rome', 'madrid', 'amsterdam', 'stockholm', 'oslo', 'copenhagen',
                'warsaw', 'moscow', 'kyiv'
            ],
            'asia': [
                'asia', 'asian', 'china', 'chinese', 'japan', 'japanese', 'india',
                'indian', 'south korea', 'korean', 'singapore', 'singaporean',
                'thailand', 'thai', 'vietnam', 'vietnamese', 'indonesia',
                'indonesian', 'malaysia', 'malaysian', 'philippines', 'filipino',
                'pakistan', 'pakistani', 'bangladesh', 'bangladeshi', 'beijing',
                'tokyo', 'new delhi', 'seoul', 'bangkok', 'hanoi', 'jakarta',
                'kuala lumpur', 'manila', 'islamabad', 'dhaka'
            ],
            'middle_east': [
                'middle east', 'middle eastern', 'israel', 'israeli', 'palestine',
                'palestinian', 'saudi arabia', 'saudi', 'iran', 'iranian', 'turkey',
                'turkish', 'egypt', 'egyptian', 'lebanon', 'lebanese', 'jordan',
                'jordanian', 'syria', 'syrian', 'iraq', 'iraqi', 'qatar', 'qatari',
                'uae', 'emirates', 'kuwait', 'kuwaiti', 'jerusalem', 'tel aviv',
                'riyadh', 'tehran', 'istanbul', 'cairo', 'beirut', 'amman',
                'damascus', 'baghdad', 'doha', 'abu dhabi', 'kuwait city'
            ],
            'africa': [
                'africa', 'african', 'south africa', 'south african', 'nigeria',
                'nigerian', 'kenya', 'kenyan', 'ethiopia', 'ethiopian', 'ghana',
                'ghanese', 'morocco', 'moroccan', 'algeria', 'algerian', 'egypt',
                'egyptian', 'tunisia', 'tunisian', 'libya', 'libyan', 'sudan',
                'sudanese', 'somalia', 'somali', 'uganda', 'ugandan', 'tanzania',
                'tanzanian', 'johannesburg', 'cape town', 'lagos', 'nairobi',
                'addis ababa', 'accra', 'rabat', 'algiers', 'cairo', 'tunis',
                'tripoli', 'khartoum', 'mogadishu', 'kampala', 'dodoma'
            ],
            'latin_america': [
                'latin america', 'latin american', 'brazil', 'brazilian', 'argentina',
                'argentine', 'chile', 'chilean', 'colombia', 'colombian', 'peru',
                'peruvian', 'venezuela', 'venezuelan', 'ecuador', 'ecuadorian',
                'bolivia', 'bolivian', 'paraguay', 'paraguayan', 'uruguay',
                'uruguayan', 'panama', 'panamanian', 'costa rica', 'costa rican',
                'nicaragua', 'nicaraguan', 'honduras', 'honduran', 'el salvador',
                'salvadoran', 'guatemala', 'guatemalan', 'belize', 'belizean',
                'brasilia', 'buenos aires', 'santiago', 'bogota', 'lima',
                'caracas', 'quito', 'la paz', 'asuncion', 'montevideo',
                'panama city', 'san jose', 'managua', 'tegucigalpa', 'san salvador',
                'guatemala city', 'belmopan'
            ],
            'oceania': [
                'oceania', 'oceania', 'australia', 'australian', 'new zealand',
                'zealand', 'fiji', 'fijian', 'papua new guinea', 'papua new guinean',
                'samoa', 'samoan', 'tonga', 'tongan', 'vanuatu', 'vanuatuan',
                'solomon islands', 'solomon islander', 'canberra', 'sydney',
                'melbourne', 'brisbane', 'perth', 'wellington', 'auckland',
                'suva', 'port moresby', 'apia', 'nuku\'alofa', 'port vila',
                'honiara'
            ]
        }
        
        # Regional news sources mapping
        self.regional_sources = {
            'north_america': [
                'cnn.com', 'foxnews.com', 'nbcnews.com', 'abcnews.go.com',
                'cbsnews.com', 'usatoday.com', 'nytimes.com', 'washingtonpost.com',
                'wsj.com', 'latimes.com', 'chicagotribune.com', 'bostonglobe.com',
                'cbc.ca', 'ctvnews.ca', 'globalnews.ca', 'theglobeandmail.com',
                'nationalpost.com', 'reforma.com', 'eluniversal.com.mx',
                'milenio.com', 'proceso.com.mx'
            ],
            'europe': [
                'bbc.com', 'bbc.co.uk', 'theguardian.com', 'independent.co.uk',
                'telegraph.co.uk', 'dailymail.co.uk', 'mirror.co.uk', 'express.co.uk',
                'spiegel.de', 'faz.net', 'welt.de', 'zeit.de', 'lemonde.fr',
                'lefigaro.fr', 'liberation.fr', 'corriere.it', 'repubblica.it',
                'ansa.it', 'elpais.com', 'elmundo.es', 'abc.es', 'nos.nl',
                'nu.nl', 'svt.se', 'dn.se', 'aftenposten.no', 'vg.no',
                'dr.dk', 'berlingske.dk', 'wyborcza.pl', 'rp.pl', 'tvn24.pl',
                'rt.com', 'tass.com', 'interfax.ru', 'ukrinform.net', 'unian.info'
            ],
            'asia': [
                'scmp.com', 'chinadaily.com.cn', 'xinhuanet.com', 'people.com.cn',
                'asahi.com', 'mainichi.jp', 'yomiuri.co.jp', 'nhk.or.jp',
                'thehindu.com', 'timesofindia.indiatimes.com', 'indianexpress.com',
                'hindustantimes.com', 'koreaherald.com', 'koreatimes.co.kr',
                'straitstimes.com', 'todayonline.com', 'bangkokpost.com',
                'nationthailand.com', 'vietnamnews.vn', 'tuoitrenews.vn',
                'thejakartapost.com', 'kompas.com', 'thestar.com.my',
                'malaysiakini.com', 'philstar.com', 'inquirer.net',
                'dawn.com', 'tribune.com.pk', 'thedailystar.net', 'bdnews24.com'
            ],
            'middle_east': [
                'haaretz.com', 'timesofisrael.com', 'jpost.com', 'ynetnews.com',
                'maannews.net', 'wafa.ps', 'aljazeera.net', 'aljazeera.com',
                'arabnews.com', 'saudigazette.com.sa', 'tehrantimes.com',
                'irna.ir', 'hurriyet.com.tr', 'milliyet.com.tr', 'ahram.org.eg',
                'egypttoday.com', 'dailystar.com.lb', 'naharnet.com',
                'jordantimes.com', 'ammonnews.net', 'sana.sy', 'syriatimes.sy',
                'iraqinews.com', 'iraq-businessnews.com', 'qatar-tribune.com',
                'thepeninsulaqatar.com', 'kuwaittimes.com', 'arabtimes.com',
                'gulfnews.com', 'thenational.ae', 'khaleejtimes.com'
            ],
            'africa': [
                'mg.co.za', 'iol.co.za', 'news24.com', 'timeslive.co.za',
                'vanguardngr.com', 'punchng.com', 'guardian.ng', 'thisdaylive.com',
                'nation.co.ke', 'standardmedia.co.ke', 'the-star.co.ke',
                'ethiopianreporter.com', 'addisfortune.net', 'ghanaweb.com',
                'myjoyonline.com', 'ghanaian-times.com', 'moroccoworldnews.com',
                'moroccotribune.com', 'algerie-focus.com', 'tsa-algerie.com',
                'libyaobserver.ly', 'libyaherald.com', 'sudantribune.com',
                'sudanvisiondaily.com', 'hiiraan.com', 'somalicurrent.com',
                'monitor.co.ug', 'newvision.co.ug', 'dailynews.co.tz',
                'thecitizen.co.tz'
            ],
            'latin_america': [
                'globo.com', 'uol.com.br', 'estadao.com.br', 'folha.uol.com.br',
                'clarin.com', 'lanacion.com.ar', 'infobae.com', 'lanacion.com.ar',
                'emol.com', 'latercera.com', 'biobiochile.cl', 'eltiempo.com',
                'elespectador.com', 'semana.com', 'elcomercio.pe', 'peru21.pe',
                'eluniversal.com', 'el-nacional.com', 'ultimasnoticias.com.ve',
                'elcomercio.com', 'eluniverso.com', 'lahora.com.ec',
                'paginasiete.bo', 'eldeber.com.bo', 'abc.com.py', 'ultimahora.com',
                'elobservador.com.uy', 'elpais.com.uy', 'panamaamerica.com.pa',
                'prensa.com', 'nacion.com', 'larepublica.net', 'diarioextra.com',
                'prensalibre.com', 'elperiodico.com.gt', 'reportero.com.gt',
                'reporter.bz', 'amandala.com.bz'
            ],
            'oceania': [
                'abc.net.au', 'news.com.au', 'smh.com.au', 'theage.com.au',
                'heraldsun.com.au', 'dailytelegraph.com.au', 'adelaidenow.com.au',
                'perthnow.com.au', 'couriermail.com.au', 'brisbanetimes.com.au',
                'stuff.co.nz', 'nzherald.co.nz', 'tvnz.co.nz', 'newshub.co.nz',
                'fijisun.com.fj', 'fijitimes.com.fj', 'postcourier.com.pg',
                'thenational.com.pg', 'samoaobserver.ws', 'savali.ws',
                'matangitonga.to', 'tonga-online.to', 'dailypost.vu',
                'vanuatudaily.com', 'solomonstarnews.com', 'islandssun.com'
            ]
        }
    
    def detect_news_region(self, text: str, title: str = "") -> List[str]:
        """
        Detect which regions the news content is relevant to
        Returns list of relevant regions
        """
        if not text and not title:
            return []
        
        # Combine text and title for analysis
        content = f"{title} {text}".lower()
        
        detected_regions = []
        
        for region, keywords in self.regional_keywords.items():
            # Count keyword matches
            match_count = sum(1 for keyword in keywords if keyword in content)
            
            # If we have significant matches, consider this region relevant
            if match_count >= 2:  # At least 2 keyword matches
                detected_regions.append(region)
            elif match_count == 1 and any(keyword in title.lower() for keyword in keywords):
                # Single match in title is also significant
                detected_regions.append(region)
        
        return detected_regions
    
    def get_regional_boost(self, source_url: str, source_name: str, 
                          detected_regions: List[str]) -> float:
        """
        Calculate regional boost multiplier for a source
        Returns multiplier (1.0 = no boost, 1.8 = 80% boost, etc.)
        """
        if not detected_regions:
            return 1.0  # No regional relevance, no boost
        
        # Extract domain from URL
        try:
            domain = urlparse(source_url).netloc.lower()
        except:
            domain = source_name.lower()
        
        # Check if source is from any of the detected regions
        for region in detected_regions:
            if region in self.regional_sources:
                for regional_source in self.regional_sources[region]:
                    if regional_source in domain:
                        # Source is from relevant region - give significant boost
                        return 1.8  # 80% boost for regional expertise
        
        return 1.0  # No regional match, no boost

class SourceWeights:
    """Enhanced news source weighting system with regional intelligence"""
    
    def __init__(self):
        self.regional_matcher = RegionalNewsMatcher()
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize the source weight database with enhanced credibility multipliers"""
        self.source_weights = {
            # International Premium Sources (Highest credibility, global reach)
            'reuters.com': SourceWeight(0.98, 'international', 'center', 'excellent', 'high', 'global', ['en'], ['breaking_news', 'business', 'politics'], 'verified', 1.5),
            'ap.org': SourceWeight(0.98, 'international', 'center', 'excellent', 'high', 'global', ['en'], ['breaking_news', 'politics', 'world_news'], 'verified', 1.5),
            'bloomberg.com': SourceWeight(0.95, 'international', 'center', 'excellent', 'high', 'global', ['en'], ['business', 'finance', 'markets'], 'verified', 1.4),
            'bbc.com': SourceWeight(0.93, 'international', 'center', 'excellent', 'high', 'global', ['en'], ['world_news', 'politics', 'culture'], 'verified', 1.4),
            'aljazeera.com': SourceWeight(0.90, 'international', 'center-left', 'excellent', 'high', 'global', ['en', 'ar'], ['middle_east', 'world_news', 'politics'], 'verified', 1.3),
            
            # Regional Powerhouses (High credibility in their regions)
            'cnn.com': SourceWeight(0.88, 'national', 'center-left', 'good', 'high', 'north_america', ['en'], ['breaking_news', 'politics', 'world_news'], 'verified', 1.3),
            'foxnews.com': SourceWeight(0.82, 'national', 'center-right', 'good', 'high', 'north_america', ['en'], ['politics', 'breaking_news', 'opinion'], 'verified', 1.2),
            'nbcnews.com': SourceWeight(0.86, 'national', 'center-left', 'good', 'high', 'north_america', ['en'], ['breaking_news', 'politics', 'investigative'], 'verified', 1.3),
            'abcnews.go.com': SourceWeight(0.85, 'national', 'center', 'good', 'high', 'north_america', ['en'], ['breaking_news', 'politics', 'entertainment'], 'verified', 1.2),
            'cbsnews.com': SourceWeight(0.84, 'national', 'center', 'good', 'high', 'north_america', ['en'], ['breaking_news', 'investigative', 'politics'], 'verified', 1.2),
            
            # Regional News Leaders
            'theguardian.com': SourceWeight(0.90, 'national', 'center-left', 'excellent', 'high', 'europe', ['en'], ['politics', 'investigative', 'culture'], 'verified', 1.3),
            'lemonde.fr': SourceWeight(0.89, 'national', 'center', 'excellent', 'high', 'europe', ['fr'], ['politics', 'culture', 'world_news'], 'verified', 1.3),
            'spiegel.de': SourceWeight(0.88, 'national', 'center-left', 'excellent', 'high', 'europe', ['de'], ['investigative', 'politics', 'world_news'], 'verified', 1.3),
            'corriere.it': SourceWeight(0.87, 'national', 'center', 'good', 'high', 'europe', ['it'], ['politics', 'culture', 'world_news'], 'verified', 1.2),
            'elpais.com': SourceWeight(0.86, 'national', 'center-left', 'good', 'high', 'europe', ['es'], ['politics', 'culture', 'world_news'], 'verified', 1.2),
            
            # Asian Regional Leaders
            'scmp.com': SourceWeight(0.89, 'regional', 'center', 'excellent', 'high', 'asia', ['en'], ['asia_pacific', 'business', 'politics'], 'verified', 1.3),
            'asahi.com': SourceWeight(0.88, 'national', 'center', 'excellent', 'high', 'asia', ['ja'], ['politics', 'world_news', 'culture'], 'verified', 1.3),
            'thehindu.com': SourceWeight(0.87, 'national', 'center', 'excellent', 'high', 'asia', ['en'], ['politics', 'culture', 'world_news'], 'verified', 1.3),
            'koreaherald.com': SourceWeight(0.86, 'national', 'center', 'good', 'high', 'asia', ['en'], ['politics', 'business', 'culture'], 'verified', 1.2),
            'straitstimes.com': SourceWeight(0.85, 'national', 'center', 'good', 'high', 'asia', ['en'], ['asia_pacific', 'business', 'politics'], 'verified', 1.2),
            
            # Middle East Regional Leaders
            'haaretz.com': SourceWeight(0.88, 'national', 'center-left', 'excellent', 'high', 'middle_east', ['en', 'he'], ['politics', 'middle_east', 'world_news'], 'verified', 1.3),
            'aljazeera.net': SourceWeight(0.87, 'regional', 'center-left', 'excellent', 'high', 'middle_east', ['ar', 'en'], ['middle_east', 'world_news', 'politics'], 'verified', 1.3),
            'arabnews.com': SourceWeight(0.85, 'national', 'center', 'good', 'high', 'middle_east', ['en'], ['middle_east', 'business', 'politics'], 'verified', 1.2),
            'tehrantimes.com': SourceWeight(0.83, 'national', 'center', 'good', 'medium', 'middle_east', ['en'], ['politics', 'middle_east', 'world_news'], 'verified', 1.1),
            'hurriyet.com.tr': SourceWeight(0.84, 'national', 'center', 'good', 'medium', 'middle_east', ['tr'], ['politics', 'world_news', 'culture'], 'verified', 1.1),
            
            # African Regional Leaders
            'mg.co.za': SourceWeight(0.86, 'national', 'center-left', 'good', 'high', 'africa', ['en'], ['politics', 'africa', 'world_news'], 'verified', 1.2),
            'vanguardngr.com': SourceWeight(0.84, 'national', 'center', 'good', 'medium', 'africa', ['en'], ['politics', 'africa', 'business'], 'verified', 1.1),
            'nation.co.ke': SourceWeight(0.85, 'national', 'center', 'good', 'medium', 'africa', ['en'], ['politics', 'africa', 'world_news'], 'verified', 1.1),
            'ethiopianreporter.com': SourceWeight(0.83, 'national', 'center', 'good', 'medium', 'africa', ['en'], ['politics', 'africa', 'culture'], 'verified', 1.0),
            'ghanaweb.com': SourceWeight(0.82, 'national', 'center', 'good', 'medium', 'africa', ['en'], ['politics', 'africa', 'business'], 'verified', 1.0),
            
            # Latin American Regional Leaders
            'globo.com': SourceWeight(0.87, 'national', 'center', 'excellent', 'high', 'latin_america', ['pt'], ['politics', 'entertainment', 'sports'], 'verified', 1.2),
            'clarin.com': SourceWeight(0.86, 'national', 'center', 'good', 'high', 'latin_america', ['es'], ['politics', 'culture', 'world_news'], 'verified', 1.2),
            'emol.com': SourceWeight(0.85, 'national', 'center', 'good', 'high', 'latin_america', ['es'], ['politics', 'business', 'world_news'], 'verified', 1.2),
            'eltiempo.com': SourceWeight(0.84, 'national', 'center', 'good', 'high', 'latin_america', ['es'], ['politics', 'culture', 'world_news'], 'verified', 1.1),
            'elcomercio.pe': SourceWeight(0.83, 'national', 'center', 'good', 'medium', 'latin_america', ['es'], ['politics', 'business', 'world_news'], 'verified', 1.0),
            
            # Oceania Regional Leaders
            'abc.net.au': SourceWeight(0.88, 'national', 'center', 'excellent', 'high', 'oceania', ['en'], ['politics', 'world_news', 'culture'], 'verified', 1.2),
            'stuff.co.nz': SourceWeight(0.86, 'national', 'center', 'good', 'high', 'oceania', ['en'], ['politics', 'world_news', 'culture'], 'verified', 1.1),
            'fijisun.com.fj': SourceWeight(0.81, 'national', 'center', 'good', 'medium', 'oceania', ['en'], ['politics', 'oceania', 'culture'], 'verified', 1.0),
            'solomonstarnews.com': SourceWeight(0.79, 'national', 'center', 'good', 'medium', 'oceania', ['en'], ['politics', 'oceania', 'world_news'], 'verified', 1.0),
            
            # Local/Regional Sources (Lower base weight but can get regional boost)
            'localnews.com': SourceWeight(0.73, 'local', 'center', 'fair', 'medium', 'north_america', ['en'], ['local_news', 'community'], 'verified', 1.0),
            'citytimes.com': SourceWeight(0.71, 'local', 'center', 'fair', 'medium', 'north_america', ['en'], ['local_news', 'community'], 'verified', 1.0),
            'townherald.com': SourceWeight(0.68, 'local', 'center', 'fair', 'medium', 'north_america', ['en'], ['local_news', 'community'], 'verified', 1.0),
        }
    
    def get_source_weight(self, url: str, source_name: str = "", 
                         news_content: str = "", news_title: str = "") -> SourceWeight:
        """
        Get weighted source information with regional intelligence
        """
        # Extract domain from URL
        try:
            domain = urlparse(url).netloc.lower()
        except:
            domain = source_name.lower() if source_name else "unknown"
        
        # Look for exact domain match first
        if domain in self.source_weights:
            base_weight = self.source_weights[domain]
        else:
            # Try to find partial matches
            base_weight = self._find_partial_match(domain)
        
        # Apply regional boost if news content is provided
        if news_content or news_title:
            detected_regions = self.regional_matcher.detect_news_region(news_content, news_title)
            regional_boost = self.regional_matcher.get_regional_boost(url, source_name, detected_regions)
            
            # Create enhanced weight with regional boost
            enhanced_weight = SourceWeight(
                weight=min(1.0, base_weight.weight * regional_boost),  # Cap at 1.0
                category=base_weight.category,
                bias_rating=base_weight.bias_rating,
                fact_checking=base_weight.fact_checking,
                editorial_standards=base_weight.editorial_standards,
                region=base_weight.region,
                languages=base_weight.languages,
                expertise_areas=base_weight.expertise_areas,
                verification_level=base_weight.verification_level,
                credibility_multiplier=base_weight.credibility_multiplier
            )
            
            return enhanced_weight
        
        return base_weight
    
    def calculate_balanced_score(self, sources: List[Dict], detected_regions: List[str]) -> float:
        """
        Calculate balanced score that prioritizes credibility, quantity, and regional expertise
        """
        if not sources:
            return 0.0
        
        total_score = 0.0
        credibility_bonus = 0.0
        regional_bonus = 0.0
        quantity_bonus = 0.0
        
        # Process each source
        for source in sources:
            source_url = source.get('url', '')
            source_name = source.get('source', 'Unknown')
            
            # Get base source weight
            source_weight_info = self.get_source_weight(
                url=source_url,
                source_name=source_name,
                news_content="",  # We already have detected regions
                news_title=""
            )
            
            # Base weight with credibility multiplier
            base_weight = source_weight_info.weight * source_weight_info.credibility_multiplier
            
            # Regional expertise bonus
            regional_boost = self.regional_matcher.get_regional_boost(
                source_url, source_name, detected_regions
            )
            
            # Similarity score from the source
            similarity_score = source.get('similarity_score', 0.5)
            
            # Calculate final source score
            source_score = base_weight * regional_boost * similarity_score
            total_score += source_score
            
            # Accumulate bonuses for analysis
            credibility_bonus += source_weight_info.credibility_multiplier
            regional_bonus += regional_boost
            quantity_bonus += 1.0
        
        # Calculate averages
        avg_credibility = credibility_bonus / len(sources) if sources else 0.0
        avg_regional = regional_bonus / len(sources) if sources else 0.0
        
        # Apply quantity bonus (more sources = higher confidence)
        quantity_multiplier = min(1.5, 1.0 + (len(sources) - 1) * 0.1)  # Max 50% bonus for quantity
        
        # Final balanced score
        final_score = (total_score / len(sources)) * quantity_multiplier
        
        # Additional credibility bonus for high-credibility sources
        if avg_credibility > 1.2:  # If average credibility is high
            final_score *= 1.2  # 20% bonus
        
        # Regional expertise bonus (even if sources don't match region)
        if avg_regional > 1.3:  # If sources have good regional expertise
            final_score *= 1.1  # 10% bonus
        
        return min(1.0, final_score)  # Cap at 1.0
    
    def calculate_recency_factor(self, published_date: str) -> float:
        """
        Calculate recency factor for news articles
        Returns multiplier based on how recent the article is
        """
        try:
            if not published_date or published_date == "Unknown":
                return 0.8  # Default for unknown dates
            
            # Handle relative time formats like "2 hours ago", "3 days ago"
            if "ago" in published_date.lower():
                if "hour" in published_date.lower():
                    return 1.0  # Very recent
                elif "day" in published_date.lower():
                    return 0.95  # Recent
                elif "week" in published_date.lower():
                    return 0.9  # Moderately recent
                elif "month" in published_date.lower():
                    return 0.8  # Less recent
                else:
                    return 0.7  # Old
            
            # Handle ISO format dates
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                age_hours = (datetime.now() - dt).total_seconds() / 3600
                
                if age_hours < 1:
                    return 1.0  # Less than 1 hour
                elif age_hours < 6:
                    return 0.98  # Less than 6 hours
                elif age_hours < 24:
                    return 0.95  # Less than 24 hours
                elif age_hours < 72:
                    return 0.9   # Less than 3 days
                elif age_hours < 168:
                    return 0.8   # Less than 1 week
                else:
                    return 0.7   # Older than 1 week
            except:
                return 0.8  # Fallback for parsing errors
                
        except Exception as e:
            return 0.8  # Default fallback
    
    def _find_partial_match(self, domain: str) -> SourceWeight:
        """Find best partial match for domain"""
        best_match = None
        best_score = 0
        
        for source_domain, weight in self.source_weights.items():
            # Check if domain contains source domain or vice versa
            if source_domain in domain or domain in source_domain:
                # Calculate similarity score
                score = len(set(domain.split('.')) & set(source_domain.split('.')))
                if score > best_score:
                    best_score = score
                    best_match = weight
        
        if best_match:
            return best_match
        
        # Return default weight for unknown sources
        return SourceWeight(
            weight=0.50,  # Neutral weight
            category='unknown',
            bias_rating='center',
            fact_checking='fair',
            editorial_standards='medium',
            region='unknown',
            languages=['en'],
            expertise_areas=['general'],
            verification_level='unverified',
            credibility_multiplier=1.0
        )
    
    def get_regional_experts(self, region: str) -> List[str]:
        """Get list of expert sources for a specific region"""
        if region in self.regional_matcher.regional_sources:
            return self.regional_matcher.regional_sources[region]
        return []
    
    def get_credibility_ranking(self, min_weight: float = 0.7) -> List[Tuple[str, float]]:
        """Get ranked list of sources by credibility"""
        ranked = [(domain, weight.weight) for domain, weight in self.source_weights.items()]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return [(domain, weight) for domain, weight in ranked if weight >= min_weight]

# Global instance
source_weights = SourceWeights()
