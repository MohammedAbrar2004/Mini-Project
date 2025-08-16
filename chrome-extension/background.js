// Background script for Veritas Fact Checker Extension
// Handles context menu, API calls, and extension state management

const API_BASE_URL = 'http://localhost:8000/api';

// Create context menu when extension is installed
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "veritas-fact-check",
    title: "🔍 Fact-check with Veritas",
    contexts: ["selection"]
  });
  
  console.log("Veritas Fact Checker extension installed");
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "veritas-fact-check" && info.selectionText) {
    const selected = (info.selectionText || '').trim();
    if (!selected) return;
    console.log("Fact-checking selected text:", selected);
    
    // Show loading state
    chrome.tabs.sendMessage(tab.id, {
      action: "showLoading",
      text: selected
    });
    
    try {
      // Call Veritas API
      const result = await factCheckText(selected);
      
      // Send result to content script
      chrome.tabs.sendMessage(tab.id, {
        action: "showResult",
        result: result,
        originalText: selected
      });
      
    } catch (error) {
      console.error("Fact-check failed:", error);
      
      // Send error to content script
      chrome.tabs.sendMessage(tab.id, {
        action: "showError",
        error: error.message,
        originalText: selected
      });
    }
  }
});

// Function to call Veritas API
async function factCheckText(text) {
  const response = await fetch(`${API_BASE_URL}/fact-check`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: text
    })
  });
  
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }
  
  const data = await response.json();
  return data;
}

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "factCheck") {
    const t = (request.text || '').trim();
    factCheckText(t)
      .then(result => sendResponse({ success: true, result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    
    return true; // Keep message channel open for async response
  }
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
  chrome.tabs.sendMessage(tab.id, {
    action: "togglePanel"
  });
});
