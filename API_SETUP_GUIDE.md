# 🔑 API Setup Guide for TruthScope

## 📋 **Required API Keys**

### **1. Google Custom Search Engine (Already Configured)**
- **Primary Key**: `AIzaSyAmNulMCDsTURu8d2ATYSeYoqnHWtGyFGk`
- **Primary CSE ID**: `e016465d162974c10`
- **Backup Key**: `AIzaSyDm0yP_ACaIrI6_WuQBqWRW4QI9kNArfXE`
- **Backup CSE ID**: `87a513050ae524e45`

**To Renew:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "APIs & Services" → "Credentials"
3. Find your API keys and click "Regenerate Key"
4. Update your `.env` files

---

### **2. News APIs (Recommended for Enhanced Coverage)**

#### **NewsAPI.org** ⭐ **HIGH PRIORITY**
- **Free Tier**: 1,000 requests/day
- **Cost**: Free
- **Sign Up**: [https://newsapi.org/register](https://newsapi.org/register)
- **Coverage**: Global, real-time news
- **Quality**: High

#### **GNews API** ⭐ **HIGH PRIORITY**
- **Free Tier**: 100 requests/day
- **Cost**: Free
- **Sign Up**: [https://gnews.io/](https://gnews.io/)
- **Coverage**: Global, breaking news
- **Quality**: High

#### **MediaStack API**
- **Free Tier**: 500 requests/month
- **Cost**: Free
- **Sign Up**: [https://mediastack.com/](https://mediastack.com/)
- **Coverage**: Global, multiple languages
- **Quality**: Medium

#### **Bing News Search API**
- **Free Tier**: 1,000 transactions/month
- **Cost**: Free
- **Sign Up**: [https://www.microsoft.com/en-us/bing/apis/bing-news-search-api](https://www.microsoft.com/en-us/bing/apis/bing-news-search-api)
- **Coverage**: Global, Microsoft-curated
- **Quality**: High

---

### **3. Social Media APIs (Optional)**

#### **Reddit API**
- **Free Tier**: Unlimited
- **Cost**: Free
- **Sign Up**: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
- **Use Case**: Social sentiment analysis

#### **Twitter API v2**
- **Free Tier**: 500,000 tweets/month
- **Cost**: Free
- **Sign Up**: [https://developer.twitter.com/](https://developer.twitter.com/)
- **Use Case**: Real-time news trends

---

### **4. AI/ML APIs (Optional)**

#### **Hugging Face API**
- **Free Tier**: 30,000 requests/month
- **Cost**: Free
- **Sign Up**: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
- **Use Case**: Advanced text analysis

---

## 🎯 **News Source Priority System**

### **Premium Sources (Weight: 0.9-1.0)**
These sources get **highest priority** and **+0.1 bonus** to their scores:

1. **BBC News** (Weight: 0.98) 🇬🇧
   - Most trusted international news source
   - Excellent fact-checking and editorial standards

2. **Al Jazeera** (Weight: 0.95) 🇶🇦
   - Comprehensive global coverage
   - Strong editorial standards and fact-checking

3. **CNN** (Weight: 0.92) 🇺🇸
   - Breaking news and live coverage
   - High editorial standards

### **Trusted Sources (Weight: 0.8-0.89)**
These sources get **high priority**:

- **Reuters** (0.88) - Wire service, very reliable
- **Associated Press** (0.87) - Wire service, excellent standards
- **The Guardian** (0.85) - Investigative journalism
- **The New York Times** (0.84) - Comprehensive coverage
- **The Washington Post** (0.83) - Political coverage
- **Bloomberg** (0.82) - Business and financial news
- **Financial Times** (0.81) - Business and economics
- **The Wall Street Journal** (0.80) - Business and politics

### **Standard Sources (Weight: 0.6-0.79)**
These sources get **medium priority**:

- **NPR** (0.78) - Public radio, good standards
- **The Economist** (0.77) - Analysis and commentary
- **Deutsche Welle** (0.76) - German international news
- **The Hindu** (0.75) - Indian news
- **Indian Express** (0.74) - Indian news
- **Business Standard** (0.73) - Indian business news

---

## ⚙️ **Configuration Steps**

### **Step 1: Get API Keys**
1. Sign up for the recommended APIs above
2. Copy your API keys

### **Step 2: Update Environment Variables**
Create or update your `.env` file:

```bash
# Google Custom Search Engine API Keys
GOOGLE_API_KEY=your_primary_google_api_key
GOOGLE_CSE_ID=your_primary_cse_id
GOOGLE_API_KEY_2=your_backup_google_api_key
GOOGLE_CSE_ID_2=your_backup_cse_id

# News APIs
NEWSAPI_KEY=your_newsapi_key_here
GNEWS_API_KEY=your_gnews_api_key_here
MEDIASTACK_API_KEY=your_mediastack_api_key_here
BING_NEWS_API_KEY=your_bing_news_api_key_here

# Social Media APIs (Optional)
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# AI/ML APIs (Optional)
HUGGINGFACE_API_TOKEN=your_huggingface_token_here

# Configuration
MAX_ARTICLES_PER_SOURCE=15
CACHE_EXPIRY_HOURS=2
REQUEST_TIMEOUT=30
MAX_CONCURRENT_REQUESTS=10
```

### **Step 3: Test the System**
Run the enhanced news fetcher to test:

```bash
cd LLM
python enhanced_news_fetcher.py
```

---

## 📊 **How the Weighting System Works**

### **Base Score Calculation**
1. **Source Weight**: Each news source has a base credibility score (0.0-1.0)
2. **Time Bonus**: Recent articles get +0.01 to +0.03 bonus
3. **Description Bonus**: Longer descriptions get +0.01 to +0.03 bonus
4. **Image Bonus**: Articles with images get +0.05 bonus
5. **Premium Bonus**: Al Jazeera, BBC, CNN get +0.1 bonus

### **Final Score Formula**
```
Final Score = Base Source Weight + Time Bonus + Description Bonus + Image Bonus + Premium Bonus
```

### **Example Scoring**
- **BBC Article**: 0.98 + 0.03 + 0.02 + 0.05 + 0.1 = **1.18** (capped at 1.0)
- **Unknown Source**: 0.25 + 0.01 + 0.01 + 0.0 + 0.0 = **0.27**

---

## 🚀 **Benefits of the New System**

1. **Quality First**: Premium sources like BBC, Al Jazeera, and CNN appear first
2. **Diverse Coverage**: Multiple APIs provide comprehensive news coverage
3. **Credibility Scoring**: Each article gets a credibility score
4. **Bias Awareness**: Sources are labeled with bias ratings
5. **Fact-Checking Info**: Shows which sources have fact-checking processes
6. **Editorial Standards**: Indicates quality of editorial processes

---

## 🔧 **Troubleshooting**

### **Common Issues**
1. **"Failed to fetch" errors**: Check API key validity and rate limits
2. **No news loading**: Verify API keys are correctly set in `.env`
3. **Slow loading**: Check internet connection and API response times

### **Rate Limit Management**
- **NewsAPI**: 1,000 requests/day
- **GNews**: 100 requests/day
- **MediaStack**: 500 requests/month
- **Bing**: 1,000 transactions/month

The system automatically manages these limits and falls back to available sources.

---

## 📞 **Support**

If you encounter issues:
1. Check the API documentation for each service
2. Verify your API keys are active
3. Check rate limits and quotas
4. Review the logs for specific error messages

---

**Happy News Fetching! 🎉**
