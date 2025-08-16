import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import FactCheckInput from '../components/FactCheckInput';
import NewsDashboard from '../components/NewsDashboard';

interface HomePageProps {
  onLoadingChange?: (loading: boolean) => void;
}

const HomePage: React.FC<HomePageProps> = React.memo(({ onLoadingChange }) => {
  const navigate = useNavigate();
  const [latestNews, setLatestNews] = useState<any[]>([]);
  const [isLoadingNews, setIsLoadingNews] = useState(false);

  // Memoize the news loading function
  const loadLatestNews = useCallback(async () => {
    setIsLoadingNews(true);
    try {
      const response = await fetch('/api/v1/news/latest');
      if (response.ok) {
        const data = await response.json();
        setLatestNews(data.articles || []);
      } else {
        console.warn('Failed to load latest news');
      }
    } catch (error) {
      console.error('Error loading latest news:', error);
    } finally {
      setIsLoadingNews(false);
    }
  }, []);

  // Load news on component mount
  useEffect(() => {
    loadLatestNews();
  }, [loadLatestNews]);

  // Memoize the fact check handler
  const handleFactCheck = useCallback(async (claim: string) => {
    if (onLoadingChange) {
      onLoadingChange(true);
    }
    
    try {
      const response = await fetch('/api/fact-check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: claim }),
      });

      if (response.ok) {
        const result = await response.json();
        navigate('/results', { state: { result, claim } });
      } else {
        console.error('Fact check failed');
      }
    } catch (error) {
      console.error('Error during fact check:', error);
    } finally {
      if (onLoadingChange) {
        onLoadingChange(false);
      }
    }
  }, [navigate, onLoadingChange]);

  // Memoize the news dashboard
  const newsDashboard = useMemo(() => (
    <NewsDashboard 
      news={latestNews} 
      isLoading={isLoadingNews}
      onRefresh={loadLatestNews}
    />
  ), [latestNews, isLoadingNews, loadLatestNews]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="text-center flex-1">
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                TRUTH SCOPE
              </h1>
              <div className="w-32 h-1 bg-gradient-to-r from-blue-500 to-purple-600 mx-auto rounded-full"></div>
              <p className="text-gray-600 mt-3 text-lg">
                AI-Powered Fact-Checking & News Verification
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Fact Check Input */}
          <div className="lg:order-1">
            <FactCheckInput onSubmit={handleFactCheck} />
          </div>

          {/* News Dashboard */}
          <div className="lg:order-2">
            {newsDashboard}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-300">
            Powered by advanced AI and multiple news sources for comprehensive fact-checking
          </p>
        </div>
      </footer>
    </div>
  );
});

HomePage.displayName = 'HomePage';

export default HomePage;
