# Veritas Chrome Extension

This extension integrates with the Veritas backend to fact-check selected text on webpages.

- API base URL now uses the unified endpoint at `/api/fact-check`.
- Ensure the FastAPI backend is running on `http://localhost:8000`.

## 🚀 Features

- **Text Selection Fact-Checking**: Highlight any text and right-click to fact-check
- **Real-time Results**: Get truth scores, confidence levels, and verdicts instantly
- **Source Analysis**: View supporting and contradicting news sources
- **Beautiful UI**: Clean, modern interface with color-coded results
- **API Integration**: Seamlessly connects to your Veritas backend

## 📋 Prerequisites

Before installing the extension, make sure you have:

1. **Veritas Backend Running**: Your Veritas API should be running on `http://localhost:8000`
2. **Chrome Browser**: Version 88 or higher (for Manifest V3 support)

## 🛠️ Installation

### Quick Installation

1. **Run the Setup Script**:
   - Double-click `install.bat` (Windows) for guided setup
   - Or follow the manual steps below

### Manual Installation

1. **Open Chrome Extensions Page**:
   - Go to `chrome://extensions/`
   - Or click Menu → More Tools → Extensions

2. **Enable Developer Mode**:
   - Toggle the "Developer mode" switch in the top right

3. **Load the Extension**:
   - Click "Load unpacked"
   - Select the `chrome-extension` folder from your Veritas project

4. **Verify Installation**:
   - You should see "Veritas Fact Checker" in your extensions list
   - The extension will appear in your Chrome toolbar (may not have an icon initially)

### Method 2: Package for Distribution

1. **Create Extension Package**:
   ```bash
   # In the chrome-extension directory
   zip -r veritas-fact-checker.zip . -x "*.DS_Store" "README.md"
   ```

2. **Install from Package**:
   - Go to `chrome://extensions/`
   - Enable Developer mode
   - Click "Load unpacked" and select the folder, or drag the .zip file

## 🎯 How to Use

### Basic Usage

1. **Start Your Backend**:
   ```bash
   # Make sure your Veritas API is running
   cd /path/to/veritas
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Navigate to Any Website**:
   - Go to any news website or page with text content

3. **Fact-Check Text**:
   - Highlight any text you want to fact-check
   - Right-click and select "🔍 Fact-check with Veritas"
   - Wait for the analysis (usually 2-5 seconds)

4. **View Results**:
   - A popup will appear in the bottom-right corner
   - Review the truth score, confidence, verdict, and sources
   - Click the × to close the popup

### Extension Popup

Click the Veritas icon in your Chrome toolbar to:
- Check API connection status
- View usage instructions
- Test the fact-checking with a sample claim

## 📊 Understanding Results

### Truth Score
- **Green (70-100%)**: Likely true, well-supported by evidence
- **Yellow (40-69%)**: Mixed evidence, requires careful consideration  
- **Red (0-39%)**: Likely false, contradicted by evidence

### Confidence Score
- **High (70-100%)**: Strong confidence in the analysis
- **Medium (50-69%)**: Moderate confidence
- **Low (0-49%)**: Low confidence, insufficient data

### Verdicts
- **Most Likely True**: High truth score with strong evidence
- **Likely True (Needs More Support)**: Good evidence but could use more sources
- **Inconclusive / Mixed Evidence**: Conflicting information
- **Likely False**: Evidence suggests the claim is false
- **Insufficient Data**: Not enough information to make a determination

## 🔧 Configuration

### API Endpoint Configuration

If your Veritas API is running on a different port or domain, update the `API_BASE_URL` in:

1. **background.js** (line 4):
   ```javascript
   const API_BASE_URL = 'http://your-domain.com:8000/api/v1/verify';
   ```

2. **popup.js** (line 4):
   ```javascript
   const API_BASE_URL = 'http://your-domain.com:8000/api/v1/verify';
   ```

3. **manifest.json** host_permissions:
   ```json
   "host_permissions": [
     "http://your-domain.com:8000/*"
   ]
   ```

### CORS Configuration

Make sure your Veritas backend allows requests from the extension. In your `app/main.py`, ensure CORS is configured:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify chrome-extension://* for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🐛 Troubleshooting

### Common Issues

1. **"Could not load icon" Error**:
   - This is normal if you haven't created icons yet
   - The extension will work fine without icons
   - To fix: Open `create-icons.html` to generate icons, or remove icon references from `manifest.json`

2. **"API Offline" Status**:
   - Check if your Veritas backend is running on port 8000
   - Verify the API endpoint URL in the extension files
   - Check browser console for CORS errors

3. **Context Menu Not Appearing**:
   - Make sure you've selected text before right-clicking
   - Try refreshing the page and selecting text again
   - Check if the extension is enabled in chrome://extensions/

4. **No Results Popup**:
   - Check the browser console for JavaScript errors
   - Verify the API is responding correctly
   - Try the test function in the extension popup

5. **CORS Errors**:
   - Update your backend CORS configuration
   - Add chrome-extension://* to allowed origins

### Debug Mode

1. **Open Developer Tools**:
   - Right-click on any page → Inspect
   - Go to Console tab

2. **Check Extension Logs**:
   - Go to chrome://extensions/
   - Click "Details" on Veritas Fact Checker
   - Click "Inspect views: background page"

3. **View Network Requests**:
   - In Developer Tools, go to Network tab
   - Perform a fact-check and check for API requests

## 📁 File Structure

```
chrome-extension/
├── manifest.json          # Extension configuration
├── background.js          # Service worker for API calls
├── content.js            # Content script for page interaction
├── content.css           # Styles for result popup
├── popup.html            # Extension popup interface
├── popup.js              # Popup functionality
├── icons/                # Extension icons (add your own)
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
└── README.md             # This file
```

## 🔒 Privacy & Security

- The extension only processes text that you explicitly select and fact-check
- No browsing data is collected or stored
- All fact-checking requests go directly to your Veritas API
- No third-party tracking or analytics

## 🚀 Next Steps

1. **Add Icons**:
   - Open `create-icons.html` in your browser to generate icons automatically
   - Or create custom icon files (16x16, 32x32, 48x48, 128x128 pixels) and place them in the `icons/` folder
   - Update `manifest.json` to include the icon references
2. **Test Thoroughly**: Test on various websites and with different types of claims
3. **Package for Distribution**: Create a .zip file for sharing or Chrome Web Store submission
4. **Enhance Features**: Consider adding keyboard shortcuts, batch processing, or result history

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your Veritas backend is working correctly
3. Check browser console for error messages
4. Test the API directly using curl or Postman

---

**Happy Fact-Checking! 🔍✨**
