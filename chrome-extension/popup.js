// Popup script for Veritas Fact Checker Extension
// Handles popup interface, status checking, and quick testing

const API_BASE_URL = 'http://localhost:8000/api';

document.addEventListener('DOMContentLoaded', async () => {
    await checkAPIStatus();
    setupEventListeners();
});

// Check API status
async function checkAPIStatus() {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    try {
        const response = await fetch(`${API_BASE_URL}/v1/verify/status`, {
            method: 'GET',
            timeout: 5000
        });
        
        if (response.ok) {
            statusIndicator.className = 'status-indicator status-online';
            statusText.textContent = 'API Connected';
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('API status check failed:', error);
        statusIndicator.className = 'status-indicator status-offline';
        statusText.textContent = 'API Offline - Check if backend is running';
    }
}

// Setup event listeners
function setupEventListeners() {
    const testButton = document.getElementById('testButton');
    const testInput = document.getElementById('testInput');
    
    testButton.addEventListener('click', handleTestFactCheck);
    
    testInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleTestFactCheck();
        }
    });
}

// Handle test fact check
async function handleTestFactCheck() {
    const testButton = document.getElementById('testButton');
    const testInput = document.getElementById('testInput');
    const testText = testInput.value.trim();
    
    if (!testText) {
        alert('Please enter a claim to test');
        return;
    }
    
    // Show loading state
    testButton.disabled = true;
    testButton.textContent = 'Testing...';
    
    try {
        // Send message to background script to perform fact check
        const response = await chrome.runtime.sendMessage({
            action: 'factCheck',
            text: testText
        });
        
        if (response.success) {
            // Show result in a new tab or alert
            showTestResult(response.result, testText);
        } else {
            throw new Error(response.error);
        }
        
    } catch (error) {
        console.error('Test fact check failed:', error);
        alert(`Fact check failed: ${error.message}`);
    } finally {
        // Reset button state
        testButton.disabled = false;
        testButton.textContent = 'Test Fact Check';
    }
}

// Show test result
function showTestResult(result, originalText) {
    const truthScore = Math.round((result.truth_score || 0) * 100);
    const confidenceScore = Math.round(((result.confidence_score ?? result.confidence) || 0) * 100);
    
    const resultMessage = `
Test Result for: "${originalText}"

Truth Score: ${truthScore}%
Confidence: ${confidenceScore}%
Verdict: ${result.verdict || 'Unknown'}

Supporting Sources: ${result.supporting_sources?.length || 0}
Contradicting Sources: ${result.contradicting_sources?.length || 0}

Processing Time: ${result.processing_time || 0}s
    `.trim();
    
    alert(resultMessage);
}

// Refresh API status when popup is opened
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'refreshStatus') {
        checkAPIStatus();
    }
});
