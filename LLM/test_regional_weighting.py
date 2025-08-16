"""
Test script for Regional News Weighting System
Demonstrates how regional sources get boosted for relevant news
"""

import asyncio
from news_source_weights import source_weights, RegionalNewsMatcher
from news_fetcher import MultiSourceNewsFetcher

def test_regional_detection():
    """Test regional keyword detection"""
    print("🔍 Testing Regional Detection...")
    print("=" * 50)
    
    matcher = RegionalNewsMatcher()
    
    # Test cases
    test_cases = [
        {
            "title": "US President Announces New Economic Policy",
            "description": "The United States government has implemented new economic measures affecting American businesses and Canadian trade partners.",
            "expected_regions": ["north_america"]
        },
        {
            "title": "European Union Reaches Climate Agreement",
            "description": "Germany, France, and Italy have agreed to new climate targets. The UK and Spain are also supporting this initiative.",
            "expected_regions": ["europe"]
        },
        {
            "title": "China and Japan Sign Trade Deal",
            "description": "Beijing and Tokyo have reached a historic agreement. South Korea and Singapore are watching closely.",
            "expected_regions": ["asia"]
        },
        {
            "title": "Middle East Peace Talks in Jerusalem",
            "description": "Israeli and Palestinian leaders meet in Jerusalem. Saudi Arabia and Qatar are mediating the discussions.",
            "expected_regions": ["middle_east"]
        },
        {
            "title": "African Union Summit in Johannesburg",
            "description": "South African President hosts leaders from Nigeria, Kenya, and Ethiopia to discuss continental cooperation.",
            "expected_regions": ["africa"]
        },
        {
            "title": "Brazil and Argentina Strengthen Ties",
            "description": "Brasilia and Buenos Aires sign new agreements. Chile and Colombia are also participating in the regional forum.",
            "expected_regions": ["latin_america"]
        },
        {
            "title": "Australia and New Zealand Climate Initiative",
            "description": "Canberra and Wellington launch joint environmental program. Fiji and Papua New Guinea join the Pacific alliance.",
            "expected_regions": ["oceania"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        detected_regions = matcher.detect_news_region(
            test_case["description"], 
            test_case["title"]
        )
        
        print(f"\n{i}. {test_case['title']}")
        print(f"   Detected: {detected_regions}")
        print(f"   Expected: {test_case['expected_regions']}")
        print(f"   ✅ Match: {set(detected_regions) == set(test_case['expected_regions'])}")

def test_regional_boosts():
    """Test regional boost calculations"""
    print("\n\n🚀 Testing Regional Boosts...")
    print("=" * 50)
    
    matcher = RegionalNewsMatcher()
    
    # Test cases for regional boosts
    test_cases = [
        {
            "news_content": "US President announces new policy affecting American citizens",
            "source_url": "https://cnn.com/politics/us-policy",
            "source_name": "CNN",
            "expected_boost": 1.5
        },
        {
            "news_content": "European Union reaches agreement on climate policy",
            "source_url": "https://bbc.com/news/europe-climate",
            "source_name": "BBC",
            "expected_boost": 1.5
        },
        {
            "news_content": "Asian markets show strong growth in technology sector",
            "source_url": "https://reuters.com/business/asia-tech",
            "source_name": "Reuters",
            "expected_boost": 1.0  # Reuters is international, not regional
        },
        {
            "news_content": "Local community celebrates new park opening",
            "source_url": "https://localnews.com/community-park",
            "source_name": "Local News",
            "expected_boost": 1.0  # Local news doesn't match regional content
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        # Detect regions in the news content
        detected_regions = matcher.detect_news_region(test_case["news_content"])
        
        # Calculate regional boost
        regional_boost = matcher.get_regional_boost(
            test_case["source_url"],
            test_case["source_name"],
            detected_regions
        )
        
        print(f"\n{i}. Source: {test_case['source_name']}")
        print(f"   Content: {test_case['news_content'][:60]}...")
        print(f"   Detected Regions: {detected_regions}")
        print(f"   Regional Boost: {regional_boost:.1f}x")
        print(f"   Expected: {test_case['expected_boost']:.1f}x")
        print(f"   ✅ Match: {regional_boost == test_case['expected_boost']}")

def test_source_weighting():
    """Test source weighting with regional intelligence"""
    print("\n\n⚖️ Testing Source Weighting...")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "url": "https://cnn.com/news/us-policy",
            "source_name": "CNN",
            "news_content": "US President announces new economic policy affecting American businesses",
            "news_title": "US Economic Policy Changes"
        },
        {
            "url": "https://bbc.com/news/uk-politics",
            "source_name": "BBC",
            "news_content": "British Prime Minister announces new UK government policy",
            "news_title": "UK Government Policy Update"
        },
        {
            "url": "https://reuters.com/news/world",
            "source_name": "Reuters",
            "news_content": "Global economic summit brings together world leaders",
            "news_title": "Global Economic Summit"
        },
        {
            "url": "https://unknown-source.com/news",
            "source_name": "Unknown Source",
            "news_content": "Some news about various topics",
            "news_title": "General News"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['source_name']}")
        
        # Get source weight with regional intelligence
        weight_info = source_weights.get_source_weight(
            url=test_case["url"],
            source_name=test_case["source_name"],
            news_content=test_case["news_content"],
            news_title=test_case["news_title"]
        )
        
        print(f"   Base Weight: {weight_info.weight:.3f}")
        print(f"   Category: {weight_info.category}")
        print(f"   Region: {weight_info.region}")
        print(f"   Fact Checking: {weight_info.fact_checking}")
        print(f"   Editorial Standards: {weight_info.editorial_standards}")
        print(f"   Bias Rating: {weight_info.bias_rating}")

async def test_news_fetcher():
    """Test the enhanced news fetcher"""
    print("\n\n📰 Testing Enhanced News Fetcher...")
    print("=" * 50)
    
    try:
        async with MultiSourceNewsFetcher() as fetcher:
            print("🔍 Fetching news with regional intelligence...")
            
            # Fetch a small number of articles for testing
            articles = await fetcher.fetch_category_news("general", 5)
            
            print(f"📰 Found {len(articles)} articles")
            
            # Display articles with regional information
            for i, article in enumerate(articles, 1):
                print(f"\n{i}. {article.title}")
                print(f"   Source: {article.source} ({article.source_category})")
                print(f"   Weight: {article.weighted_score:.3f}")
                print(f"   Regional Boost: {article.regional_boost:.2f}x")
                if article.detected_regions:
                    print(f"   Regions: {', '.join(article.detected_regions)}")
                print(f"   URL: {article.url}")
            
            # Show regional expert sources
            print(f"\n🌍 Regional Expert Sources:")
            for region in ['north_america', 'europe', 'asia', 'middle_east']:
                experts = fetcher.get_regional_experts(region)
                print(f"   {region.replace('_', ' ').title()}: {len(experts)} sources")
                
    except Exception as e:
        print(f"❌ News fetcher test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 TruthScope Regional Weighting System Tests")
    print("=" * 60)
    
    # Test 1: Regional Detection
    test_regional_detection()
    
    # Test 2: Regional Boosts
    test_regional_boosts()
    
    # Test 3: Source Weighting
    test_source_weighting()
    
    # Test 4: News Fetcher (async)
    print("\n" + "=" * 60)
    print("Running async news fetcher test...")
    asyncio.run(test_news_fetcher())
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")

if __name__ == "__main__":
    main()
