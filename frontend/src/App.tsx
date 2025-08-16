import React, { useState, useMemo, useCallback, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

// Lazy load components for better performance
const HomePage = lazy(() => import('./pages/HomePage'));
const ResultsPage = lazy(() => import('./pages/ResultsPage'));

// Loading component
const LoadingSpinner = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
  </div>
);

function App() {
  const [isLoading, setIsLoading] = useState(false);

  // Memoize the loading state setter
  const handleLoadingChange = useCallback((loading: boolean) => {
    setIsLoading(loading);
  }, []);

  // Memoize the app structure
  const appContent = useMemo(() => (
    <Router>
      <div className="App">
        {isLoading && (
          <div className="fixed top-4 right-4 z-50">
            <div className="bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg">
              Processing...
            </div>
          </div>
        )}
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            <Route path="/" element={<HomePage onLoadingChange={handleLoadingChange} />} />
            <Route path="/results" element={<ResultsPage />} />
          </Routes>
        </Suspense>
      </div>
    </Router>
  ), [isLoading, handleLoadingChange]);

  return appContent;
}

export default App;
