# Digital Twin Browser Tracker Chrome Extension

This Chrome extension tracks your browsing behavior to help your Digital Twin learn your patterns and preferences.

## Features

- **Page Visit Tracking**: Records URLs visited and time spent
- **Click Tracking**: Monitors interaction patterns
- **Scroll Behavior**: Tracks reading patterns
- **Time Analysis**: Measures engagement with content
- **Privacy-First**: All data is processed locally first
- **Pattern Recognition**: Identifies browsing habits

## Installation

1. **Load the Extension**:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `extension` directory

2. **Login to Digital Twin**:
   - Click the extension icon in Chrome toolbar
   - Login with your Digital Twin credentials
   - The extension will start tracking automatically

## Privacy Controls

The extension provides granular privacy controls:
- Toggle tracking on/off
- Disable specific tracking types (clicks, scrolls, etc.)
- All sensitive data is anonymized before sending

## How It Works

1. **Behavior Collection**: The extension tracks various interactions:
   - Page visits and navigation patterns
   - Click locations and frequencies
   - Scroll depth and reading speed
   - Time spent on different sites
   - Form interaction patterns (no data captured)

2. **Local Processing**: Data is processed locally to extract patterns:
   - Domain categorization
   - Time-of-day patterns
   - Navigation flows
   - Engagement metrics

3. **Pattern Extraction**: Only patterns are sent to your Digital Twin:
   - No passwords or form data
   - No private content
   - Only behavioral patterns

## Data Tracked

### Page Visits
- URL (domain and path)
- Page title
- Visit duration
- Transition type (link, typed, bookmark)

### Interactions
- Click positions and elements
- Scroll depth and speed
- Time spent reading
- Navigation patterns

### Patterns
- Most visited domains
- Peak browsing hours
- Content preferences
- Reading speed

## Development

### Project Structure
```
extension/
├── manifest.json          # Extension configuration
├── src/
│   ├── background/       # Background service worker
│   ├── content/          # Content scripts
│   ├── popup/            # Extension popup UI
│   └── utils/            # Shared utilities
└── icons/                # Extension icons
```

### Building from Source
No build process needed - Chrome loads the extension directly.

### Testing
1. Make changes to the code
2. Go to `chrome://extensions/`
3. Click the refresh button on the extension card
4. Test your changes

## API Integration

The extension communicates with your Digital Twin backend at:
- `http://localhost:8000/api/behavioral/track-batch`

Ensure your backend is running before using the extension.

## Troubleshooting

### Extension Not Working
- Check if you're logged in (click extension icon)
- Ensure backend is running
- Check Chrome console for errors (F12 → Console)

### No Data Being Tracked
- Verify tracking is enabled in popup
- Check privacy settings
- Ensure you're on a trackable page (not chrome://)

### Login Issues
- Verify backend is running at localhost:8000
- Check credentials are correct
- Look for errors in popup console

## Contributing

Feel free to enhance the extension with:
- More sophisticated pattern detection
- Additional privacy controls
- Better visualization in popup
- Integration with more browser APIs