// Content script for Veritas Fact Checker Extension
// Handles text selection, result display, and user interactions on web pages

let currentResultPanel = null;
let isLoading = false;

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {
    case "showLoading":
      showLoadingPanel(request.text);
      break;
    case "showResult":
      showResultPanel(request.result, request.originalText);
      break;
    case "showError":
      showErrorPanel(request.error, request.originalText);
      break;
    case "togglePanel":
      toggleMainPanel();
      break;
  }
});

// Show loading panel
function showLoadingPanel(text) {
  removeExistingPanel();
  isLoading = true;
  
  const panel = createPanel();
  panel.innerHTML = `
    <div class="veritas-header">
      <div class="veritas-logo">🔍 Veritas</div>
      <button class="veritas-close" onclick="this.closest('.veritas-panel').remove()">×</button>
    </div>
    <div class="veritas-content">
      <div class="veritas-loading">
        <div class="veritas-spinner"></div>
        <p>Fact-checking: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"</p>
        <p class="veritas-loading-text">Analyzing with AI...</p>
      </div>
    </div>
  `;
  
  document.body.appendChild(panel);
  currentResultPanel = panel;
  
  // Auto-position panel
  positionPanel(panel);
}

// Show result panel
function showResultPanel(result, originalText) {
  removeExistingPanel();
  isLoading = false;
  
  // Debug logging
  console.log('🔍 Veritas Extension - Received result:', result);
  console.log('🔍 Veritas Extension - Matching articles:', result.matching_articles);
  console.log('🔍 Veritas Extension - Contradicting articles:', result.contradicting_articles);
  
  const panel = createPanel();
  const truthScore = Math.round((result.truth_score || 0) * 100);
  const confidenceScore = Math.round((result.confidence || 0) * 100);
  
  // Determine colors and verdict display
  const truthColor = getTruthColor(truthScore);
  const confidenceColor = getConfidenceColor(confidenceScore);
  const verdictDisplay = getVerdictDisplay(result.verdict);
  
  // Cache indicator
  const cacheIndicator = result.cached ? '<span class="veritas-cache-indicator">⚡ Cached</span>' : '';
  
  panel.innerHTML = `
    <div class="veritas-header">
      <div class="veritas-logo">🔍 Veritas</div>
      <button class="veritas-close" onclick="this.closest('.veritas-panel').remove()">×</button>
    </div>
    <div class="veritas-content">
      <div class="veritas-claim">
        <strong>Claim:</strong> "${originalText.substring(0, 100)}${originalText.length > 100 ? '...' : ''}"
      </div>
      
      <div class="veritas-scores">
        <div class="veritas-score">
          <div class="veritas-score-label">Truth Score</div>
          <div class="veritas-score-value" style="color: ${truthColor}">${truthScore}%</div>
        </div>
        <div class="veritas-score">
          <div class="veritas-score-label">Confidence</div>
          <div class="veritas-score-value" style="color: ${confidenceColor}">${confidenceScore}%</div>
        </div>
      </div>
      
      <div class="veritas-verdict ${verdictDisplay.class}">
        <strong>Verdict:</strong> ${verdictDisplay.text}
        ${cacheIndicator}
      </div>
      
      <div class="veritas-sources">
        <div class="veritas-sources-section">
          <strong>Supporting Sources (${result.matching_articles?.length || 0}):</strong>
          ${formatSources(result.matching_articles)}
        </div>
        <div class="veritas-sources-section">
          <strong>Contradicting Sources (${result.contradicting_articles?.length || 0}):</strong>
          ${formatSources(result.contradicting_articles)}
        </div>
      </div>
      
      <div class="veritas-footer">
        <small>Processed in ${result.processing_time || 0}s</small>
      </div>
    </div>
  `;
  
  document.body.appendChild(panel);
  currentResultPanel = panel;
  
  // Auto-position panel
  positionPanel(panel);
}

// Show error panel
function showErrorPanel(error, originalText) {
  removeExistingPanel();
  isLoading = false;
  
  const panel = createPanel();
  panel.innerHTML = `
    <div class="veritas-header">
      <div class="veritas-logo">🔍 Veritas</div>
      <button class="veritas-close" onclick="this.closest('.veritas-panel').remove()">×</button>
    </div>
    <div class="veritas-content">
      <div class="veritas-error">
        <div class="veritas-error-icon">⚠️</div>
        <div class="veritas-error-message">
          <strong>Fact-check failed</strong>
          <p>${error}</p>
          <p class="veritas-error-claim">Claim: "${originalText.substring(0, 50)}${originalText.length > 50 ? '...' : ''}"</p>
        </div>
      </div>
    </div>
  `;
  
  document.body.appendChild(panel);
  currentResultPanel = panel;
  
  positionPanel(panel);
}

// Create base panel element
function createPanel() {
  const panel = document.createElement('div');
  panel.className = 'veritas-panel';
  panel.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    width: 350px;
    max-height: 500px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    z-index: 10000;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    overflow: hidden;
  `;
  return panel;
}

// Position panel to avoid overlapping with page content
function positionPanel(panel) {
  // Simple positioning - can be enhanced with more sophisticated logic
  const rect = panel.getBoundingClientRect();
  const viewportHeight = window.innerHeight;
  const viewportWidth = window.innerWidth;
  
  // Adjust if panel goes off-screen
  if (rect.bottom > viewportHeight) {
    panel.style.top = Math.max(20, viewportHeight - rect.height - 20) + 'px';
  }
  
  if (rect.right > viewportWidth) {
    panel.style.right = '20px';
    panel.style.left = 'auto';
  }
}

// Remove existing panel
function removeExistingPanel() {
  if (currentResultPanel) {
    currentResultPanel.remove();
    currentResultPanel = null;
  }
}

// Helper functions
function getTruthColor(score) {
  if (score >= 70) return '#22c55e'; // Green
  if (score >= 40) return '#f59e0b'; // Yellow
  return '#ef4444'; // Red
}

function getConfidenceColor(score) {
  if (score >= 70) return '#22c55e';
  if (score >= 50) return '#f59e0b';
  return '#ef4444';
}

function getVerdictDisplay(verdict) {
  const verdictMap = {
    'MOST_LIKELY_TRUE': { text: 'Most Likely True', class: 'verdict-true' },
    'LIKELY_TRUE_NEEDS_SUPPORT': { text: 'Likely True (Needs More Support)', class: 'verdict-likely-true' },
    'INCONCLUSIVE_MIXED': { text: 'Inconclusive / Mixed Evidence', class: 'verdict-mixed' },
    'LIKELY_FALSE': { text: 'Likely False', class: 'verdict-false' },
    'INSUFFICIENT_DATA': { text: 'Insufficient Data', class: 'verdict-insufficient' },
    'TRUE': { text: 'True', class: 'verdict-true' },
    'FALSE': { text: 'False', class: 'verdict-false' },
    'MIXED': { text: 'Mixed Evidence', class: 'verdict-mixed' }
  };
  
  return verdictMap[verdict] || { text: verdict || 'Unknown', class: 'verdict-unknown' };
}

function formatSources(sources) {
  if (!sources || sources.length === 0) {
    return '<p class="veritas-no-sources">No sources found</p>';
  }
  
  return sources.slice(0, 3).map(source => {
    // Handle both old and new source formats
    const title = source.title || source.source || 'Untitled';
    const sourceName = source.source || 'Unknown source';
    const url = source.url || '#';
    
    return `
      <div class="veritas-source">
        <a href="${url}" target="_blank" rel="noopener">
          ${title}
        </a>
        <small>${sourceName}</small>
      </div>
    `;
  }).join('');
}

// Toggle main panel (for extension icon click)
function toggleMainPanel() {
  if (currentResultPanel) {
    removeExistingPanel();
  } else {
    // Show help panel
    const panel = createPanel();
    panel.innerHTML = `
      <div class="veritas-header">
        <div class="veritas-logo">🔍 Veritas Fact Checker</div>
        <button class="veritas-close" onclick="this.closest('.veritas-panel').remove()">×</button>
      </div>
      <div class="veritas-content">
        <div class="veritas-help">
          <h3>How to use:</h3>
          <ol>
            <li>Highlight any text on the page</li>
            <li>Right-click and select "🔍 Fact-check with Veritas"</li>
            <li>View the truth score, confidence, and sources</li>
          </ol>
          <p><strong>Powered by AI</strong> - Real-time fact-checking with multiple news sources</p>
        </div>
      </div>
    `;
    
    document.body.appendChild(panel);
    currentResultPanel = panel;
    positionPanel(panel);
  }
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
  removeExistingPanel();
});
