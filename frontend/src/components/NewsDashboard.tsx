import { useState, useEffect, useMemo } from 'react'
import { ChevronLeft, ChevronRight, ExternalLink, Eye, X, RefreshCw, AlertCircle } from 'lucide-react'
import { newsService, NewsArticle } from '../services/newsService'

// Use NewsArticle from service with image support
interface NewsItem extends NewsArticle {
  image?: string
  imageAlt?: string
}

// Website Preview Modal Component
interface WebsitePreviewProps {
  url: string
  title: string
  onClose: () => void
}

const WebsitePreview = ({ url, title, onClose }: WebsitePreviewProps) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white newspaper-border w-full max-w-6xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b-2 border-newspaper-black">
          <h3 className="newspaper-subheading text-lg text-newspaper-black truncate">
            {title}
          </h3>
          <div className="flex items-center space-x-2">
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-1 px-3 py-1 bg-newspaper-black text-white hover:bg-newspaper-gray transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              <span className="text-sm">Open Original</span>
            </a>
            <button
              onClick={onClose}
              className="p-2 hover:bg-newspaper-light-gray transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Preview Content */}
        <div className="flex-1 overflow-hidden">
          <iframe
            src={url}
            className="w-full h-full border-0"
            title={`Preview of ${title}`}
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
          />
        </div>
      </div>
    </div>
  )
}

const NewsDashboard = () => {
  const [currentSlide, setCurrentSlide] = useState(0)
  const [newsData, setNewsData] = useState<{ [key: string]: NewsItem[] }>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [previewTitle, setPreviewTitle] = useState<string>('')
  const [imageErrors, setImageErrors] = useState<Set<string>>(new Set())
  const [loadingImages, setLoadingImages] = useState<Set<string>>(new Set())

  const categories = ['politics', 'economics', 'celebrity', 'sports']
  const categoryTitles = {
    politics: 'POLITICS',
    economics: 'ECONOMICS',
    celebrity: 'CELEBRITY',
    sports: 'SPORTS'
  }

  // Generate placeholder image based on category and article
  const generatePlaceholderImage = (category: string, title: string, index: number) => {
    const categoryColors = {
      politics: '#1e40af', // Blue
      economics: '#059669', // Green
      celebrity: '#dc2626', // Red
      sports: '#7c2d12'     // Brown
    }

    const color = categoryColors[category as keyof typeof categoryColors] || '#6b7280'
    const initials = title.split(' ').slice(0, 2).map(word => word[0]).join('').toUpperCase()

    // Create a simple SVG placeholder
    const svg = `
      <svg width="400" height="250" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="${color}"/>
        <rect x="10" y="10" width="380" height="230" fill="none" stroke="white" stroke-width="2" opacity="0.3"/>
        <text x="50%" y="45%" text-anchor="middle" fill="white" font-size="48" font-weight="bold" font-family="Arial">${initials}</text>
        <text x="50%" y="65%" text-anchor="middle" fill="white" font-size="14" font-family="Arial" opacity="0.8">${category.toUpperCase()}</text>
      </svg>
    `

    return `data:image/svg+xml;base64,${btoa(svg)}`
  }

  // Get image URL for news item
  const getImageUrl = (item: NewsItem, index: number) => {
    // If we have a real image and it hasn't failed to load
    if (item.image && !imageErrors.has(item.id)) {
      return item.image
    }

    // Generate placeholder
    return generatePlaceholderImage(item.category, item.title, index)
  }

  // Handle image load errors
  const handleImageError = (itemId: string) => {
    setImageErrors(prev => new Set([...prev, itemId]))
    setLoadingImages(prev => {
      const newSet = new Set(prev)
      newSet.delete(itemId)
      return newSet
    })
  }

  // Handle image load start
  const handleImageLoadStart = (itemId: string) => {
    setLoadingImages(prev => new Set([...prev, itemId]))
  }

  // Handle image load success
  const handleImageLoadSuccess = (itemId: string) => {
    setLoadingImages(prev => {
      const newSet = new Set(prev)
      newSet.delete(itemId)
      return newSet
    })
  }

  // Generate image URL for articles (try to get real images when possible)
  const generateImageUrl = (article: any, category: string, index: number) => {
    // Try to extract image from article URL using a service
    if (article.url && newsService.isValidPreviewUrl(article.url)) {
      // Use a placeholder service that generates images based on URL
      const domain = new URL(article.url).hostname

      // For known news sites, try to use their favicon or a generic news image
      const knownSites = {
        'reuters.com': 'https://via.placeholder.com/400x250/1e40af/ffffff?text=Reuters',
        'bbc.com': 'https://via.placeholder.com/400x250/cc0000/ffffff?text=BBC',
        'cnn.com': 'https://via.placeholder.com/400x250/cc0000/ffffff?text=CNN',
        'nytimes.com': 'https://via.placeholder.com/400x250/000000/ffffff?text=NYT',
        'apnews.com': 'https://via.placeholder.com/400x250/0066cc/ffffff?text=AP',
        'bloomberg.com': 'https://via.placeholder.com/400x250/000000/ffffff?text=Bloomberg',
        'theguardian.com': 'https://via.placeholder.com/400x250/052962/ffffff?text=Guardian'
      }

      if (knownSites[domain as keyof typeof knownSites]) {
        return knownSites[domain as keyof typeof knownSites]
      }

      // Use Unsplash for generic category images
      const categoryKeywords = {
        politics: 'government,politics,capitol',
        economics: 'business,finance,money',
        celebrity: 'entertainment,hollywood,celebrity',
        sports: 'sports,stadium,athlete'
      }

      const keyword = categoryKeywords[category as keyof typeof categoryKeywords] || 'news'
      return `https://source.unsplash.com/400x250/?${keyword}&sig=${index}`
    }

    // Fallback to generated placeholder
    return generatePlaceholderImage(category, article.title, index)
  }

  // Stable memoized arrays to avoid re-renders when slide changes
  const currentCategory = useMemo(() => categories[currentSlide], [currentSlide])
  const currentNews = newsData[currentCategory] || []

  // Fetch news data from API
  const fetchNewsData = async () => {
    try {
      setLoading(true)
      setError(null)

      const result = await newsService.getAllNews()

      if (result.status === 'success') {
        // Enhance news data with images
        const enhancedData: { [key: string]: NewsItem[] } = {}

        for (const [category, articles] of Object.entries(result.data)) {
          enhancedData[category] = articles.map((article: any, index: number) => ({
            ...article,
            image: generateImageUrl(article, category, index),
            imageAlt: `${article.title} - ${article.source}`
          }))
        }

        setNewsData(enhancedData)
      } else {
        throw new Error('Failed to fetch news data')
      }
    } catch (err) {
      console.error('Error fetching news:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch news')
      // Use fallback data from service with images
      const fallbackData = newsService.getFallbackNews()
      const enhancedFallbackData: { [key: string]: NewsItem[] } = {}

      for (const [category, articles] of Object.entries(fallbackData)) {
        enhancedFallbackData[category] = articles.map((article: any, index: number) => ({
          ...article,
          image: generateImageUrl(article, category, index),
          imageAlt: `${article.title} - ${article.source}`
        }))
      }

      setNewsData(enhancedFallbackData)
    } finally {
      setLoading(false)
    }
  }

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % categories.length)
  }

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + categories.length) % categories.length)
  }

  const handleNewsClick = (url: string, title: string) => {
    if (newsService.isValidPreviewUrl(url)) {
      // Open in new tab
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  const handlePreviewClick = (url: string, title: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (newsService.isValidPreviewUrl(url)) {
      setPreviewUrl(url)
      setPreviewTitle(title)
    }
  }

  const closePreview = () => {
    setPreviewUrl(null)
    setPreviewTitle('')
  }

  useEffect(() => {
    fetchNewsData()
  }, [])

  useEffect(() => {
    const interval = setInterval(nextSlide, 8000) // Auto-advance every 8 seconds
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-newspaper-black mx-auto mb-4"></div>
          <p className="newspaper-body text-newspaper-gray">Loading latest news...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Website Preview Modal */}
      {previewUrl && (
        <WebsitePreview
          url={previewUrl}
          title={previewTitle}
          onClose={closePreview}
        />
      )}
      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700 newspaper-body">
              Failed to load latest news. Showing cached content.
            </span>
          </div>
          <button
            onClick={fetchNewsData}
            className="flex items-center space-x-1 px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span className="text-sm">Retry</span>
          </button>
        </div>
      )}

      {/* Category Navigation */}
      <div className="flex justify-center mb-6">
        <div className="flex items-center space-x-4">
          <div className="flex space-x-1 division-bg p-1 rounded shadow-sm">
            {categories.map((category, index) => (
              <button
                key={category}
                onClick={() => setCurrentSlide(index)}
                className={`px-4 py-2 newspaper-body font-semibold transition-colors ${
                  index === currentSlide
                    ? 'bg-newspaper-black text-white'
                    : 'text-newspaper-gray hover:text-newspaper-black'
                }`}
              >
                {categoryTitles[category as keyof typeof categoryTitles]}
              </button>
            ))}
          </div>

          {/* Refresh Button */}
          <button
            onClick={fetchNewsData}
            disabled={loading}
            className="flex items-center space-x-1 px-3 py-2 bg-newspaper-black text-white hover:bg-newspaper-gray transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Refresh news"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span className="text-sm">Refresh</span>
          </button>
        </div>
      </div>

      {/* Slideshow Container */}
      <div className="relative overflow-hidden">
        <div 
          className="flex transition-transform duration-500 ease-in-out"
          style={{ transform: `translateX(-${currentSlide * 100}%)` }}
        >
          {categories.map((category) => (
            <div key={category} className="w-full flex-shrink-0">
              <div className="text-center mb-4">
                <h3 className="newspaper-subheading-bold text-3xl text-newspaper-black">
                  {categoryTitles[category as keyof typeof categoryTitles]} NEWS
                </h3>
                <div className="newspaper-divider w-24 mx-auto mt-2"></div>
              </div>

              {/* No Articles Message */}
              {currentNews.length === 0 ? (
                <div className="text-center py-12">
                  <AlertCircle className="w-12 h-12 text-newspaper-gray mx-auto mb-4" />
                  <h4 className="newspaper-subheading text-xl text-newspaper-gray mb-2">
                    No articles available
                  </h4>
                  <p className="newspaper-body text-newspaper-gray">
                    Unable to load {categoryTitles[category as keyof typeof categoryTitles].toLowerCase()} news at this time.
                  </p>
                </div>
              ) : (
                /* News Layout: 1 big + 2 + 2 */
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Big news item (left) */}
                <div className="md:col-span-2">
                  {currentNews[0] && (
                    <div
                      className="newspaper-border h-full paper-texture hover:shadow-lg transition-shadow cursor-pointer group overflow-hidden"
                      onClick={() => handleNewsClick(currentNews[0].url || '', currentNews[0].title)}
                    >
                      {/* Image Section */}
                      <div className={`news-image-container h-48 ${loadingImages.has(currentNews[0].id) ? 'image-loading' : ''}`}>
                        <img
                          src={getImageUrl(currentNews[0], 0)}
                          alt={currentNews[0].imageAlt || currentNews[0].title}
                          className="news-image"
                          onError={() => handleImageError(currentNews[0].id)}
                          onLoadStart={() => handleImageLoadStart(currentNews[0].id)}
                          onLoad={() => handleImageLoadSuccess(currentNews[0].id)}
                          loading="lazy"
                          decoding="async"
                          fetchpriority="low"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>

                        {/* Action buttons overlay */}
                        <div className="absolute top-4 right-4 flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          {newsService.isValidPreviewUrl(currentNews[0].url) && (
                            <>
                              <button
                                onClick={(e) => handlePreviewClick(currentNews[0].url || '', currentNews[0].title, e)}
                                className="p-2 bg-black/50 hover:bg-black/70 rounded transition-colors backdrop-blur-sm"
                                title="Preview website"
                              >
                                <Eye className="w-4 h-4 text-white" />
                              </button>
                              <div className="p-2 bg-black/50 rounded backdrop-blur-sm">
                                <ExternalLink className="w-4 h-4 text-white" />
                              </div>
                            </>
                          )}
                        </div>

                        {/* Category badge */}
                        <div className="absolute bottom-4 left-4">
                          <span className="px-3 py-1 bg-newspaper-accent text-white text-xs font-semibold uppercase tracking-wide rounded">
                            {categoryTitles[category as keyof typeof categoryTitles]}
                          </span>
                        </div>
                      </div>

                      {/* Content Section */}
                      <div className="p-6">
                        <div className="mb-3 flex items-center justify-between">
                          <span className="text-xs font-semibold text-newspaper-gray uppercase tracking-wide">
                            {currentNews[0].source}
                          </span>
                          <span className="text-xs text-newspaper-gray">
                            {newsService.formatTimestamp(currentNews[0].publishedAt)}
                          </span>
                        </div>
                        <h4 className="newspaper-subheading-bold text-xl mb-3 text-newspaper-black leading-tight group-hover:text-newspaper-accent transition-colors">
                          {currentNews[0].title}
                        </h4>
                        <p className="newspaper-body text-newspaper-gray text-sm leading-relaxed">
                          {currentNews[0].summary}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Smaller news items (right) */}
                <div className="space-y-4">
                  {currentNews.slice(1, 5).map((item, index) => (
                    <div
                      key={item.id}
                      className="newspaper-border division-bg hover:shadow-lg transition-shadow cursor-pointer group overflow-hidden"
                      onClick={() => handleNewsClick(item.url || '', item.title)}
                    >
                      <div className="flex">
                        {/* Image */}
                        <div className={`news-image-container w-24 h-20 flex-shrink-0 ${loadingImages.has(item.id) ? 'image-loading' : ''}`}>
                          <img
                            src={getImageUrl(item, index + 1)}
                            alt={item.imageAlt || item.title}
                            className="news-image"
                            onError={() => handleImageError(item.id)}
                            onLoadStart={() => handleImageLoadStart(item.id)}
                            onLoad={() => handleImageLoadSuccess(item.id)}
                            loading="lazy"
                            decoding="async"
                            fetchpriority="low"
                          />
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent to-black/20"></div>
                        </div>

                        {/* Content */}
                        <div className="flex-1 p-3">
                          <div className="mb-1 flex items-center justify-between">
                            <span className="text-xs font-semibold text-newspaper-accent uppercase tracking-wide">
                              {item.source}
                            </span>
                            <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              {newsService.isValidPreviewUrl(item.url) && (
                                <>
                                  <button
                                    onClick={(e) => handlePreviewClick(item.url || '', item.title, e)}
                                    className="p-1 hover:bg-newspaper-light-gray rounded transition-colors"
                                    title="Preview website"
                                  >
                                    <Eye className="w-3 h-3 text-newspaper-gray" />
                                  </button>
                                  <ExternalLink className="w-3 h-3 text-newspaper-gray" />
                                </>
                              )}
                            </div>
                          </div>
                          <h5 className="newspaper-body-bold text-sm text-newspaper-black mb-1 leading-tight group-hover:text-newspaper-accent transition-colors line-clamp-2">
                            {item.title}
                          </h5>
                          <p className="text-xs text-newspaper-gray line-clamp-2 mb-1">
                            {item.summary}
                          </p>
                          <div className="text-xs text-newspaper-gray">
                            {newsService.formatTimestamp(item.publishedAt)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Navigation Arrows */}
        <button
          onClick={prevSlide}
          className="absolute left-4 top-1/2 transform -translate-y-1/2 paper-texture newspaper-border p-2 hover:division-bg transition-colors shadow-md"
        >
          <ChevronLeft className="w-6 h-6 text-newspaper-black" />
        </button>
        <button
          onClick={nextSlide}
          className="absolute right-4 top-1/2 transform -translate-y-1/2 paper-texture newspaper-border p-2 hover:division-bg transition-colors shadow-md"
        >
          <ChevronRight className="w-6 h-6 text-newspaper-black" />
        </button>
      </div>

      {/* Slide Indicators */}
      <div className="flex justify-center mt-6 space-x-2">
        {categories.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentSlide(index)}
            className={`w-3 h-3 rounded-full transition-colors ${
              index === currentSlide ? 'bg-newspaper-black' : 'bg-newspaper-border'
            }`}
          />
        ))}
      </div>
    </div>
  )
}

export default NewsDashboard
