// Digital Twin Browser Tracker - Background Service Worker

// Configuration
const API_BASE_URL = 'http://localhost:8000/api';
const BATCH_SIZE = 10;
const SYNC_INTERVAL = 30000; // 30 seconds

// State management
let behaviorQueue = [];
let isAuthenticated = false;
let authToken = null;
let userId = null;

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('Digital Twin Browser Tracker installed');
  initializeAuth();
  setupListeners();
  startPeriodicSync();
});

// Authentication
async function initializeAuth() {
  const stored = await chrome.storage.local.get(['authToken', 'userId']);
  if (stored.authToken && stored.userId) {
    authToken = stored.authToken;
    userId = stored.userId;
    isAuthenticated = true;
    console.log('Authenticated with stored credentials');
  }
}

// Setup event listeners
function setupListeners() {
  // Track page visits
  chrome.webNavigation.onCompleted.addListener((details) => {
    if (details.frameId === 0) { // Main frame only
      trackPageVisit(details);
    }
  });

  // Track tab activation
  chrome.tabs.onActivated.addListener(async (activeInfo) => {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (tab.url) {
      trackTabSwitch(tab);
    }
  });

  // Track tab updates
  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
      trackPageUpdate(tab);
    }
  });

  // Track idle state
  chrome.idle.onStateChanged.addListener((newState) => {
    trackIdleState(newState);
  });

  // Listen for messages from content script
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    handleContentMessage(request, sender, sendResponse);
    return true; // Keep message channel open for async response
  });
}

// Tracking functions
function trackPageVisit(details) {
  const behavior = {
    type: 'page_visit',
    timestamp: new Date().toISOString(),
    data: {
      url: details.url,
      tabId: details.tabId,
      transitionType: details.transitionType,
      transitionQualifiers: details.transitionQualifiers
    }
  };
  
  queueBehavior(behavior);
}

function trackTabSwitch(tab) {
  const behavior = {
    type: 'tab_switch',
    timestamp: new Date().toISOString(),
    data: {
      url: tab.url,
      title: tab.title,
      tabId: tab.id,
      windowId: tab.windowId
    }
  };
  
  queueBehavior(behavior);
}

function trackPageUpdate(tab) {
  const behavior = {
    type: 'page_update',
    timestamp: new Date().toISOString(),
    data: {
      url: tab.url,
      title: tab.title,
      tabId: tab.id
    }
  };
  
  queueBehavior(behavior);
}

function trackIdleState(state) {
  const behavior = {
    type: 'idle_state',
    timestamp: new Date().toISOString(),
    data: {
      state: state // 'active', 'idle', or 'locked'
    }
  };
  
  queueBehavior(behavior);
}

// Handle messages from content script
async function handleContentMessage(request, sender, sendResponse) {
  switch (request.type) {
    case 'track_click':
      trackClick(request.data, sender.tab);
      sendResponse({ success: true });
      break;
      
    case 'track_scroll':
      trackScroll(request.data, sender.tab);
      sendResponse({ success: true });
      break;
      
    case 'track_time_spent':
      trackTimeSpent(request.data, sender.tab);
      sendResponse({ success: true });
      break;
      
    case 'auth_status':
      sendResponse({ isAuthenticated, userId });
      break;
      
    case 'set_auth':
      authToken = request.token;
      userId = request.userId;
      isAuthenticated = true;
      await chrome.storage.local.set({ authToken, userId });
      sendResponse({ success: true });
      break;
      
    default:
      sendResponse({ error: 'Unknown message type' });
  }
}

// Track user interactions
function trackClick(data, tab) {
  const behavior = {
    type: 'click',
    timestamp: new Date().toISOString(),
    data: {
      ...data,
      url: tab.url,
      title: tab.title
    }
  };
  
  queueBehavior(behavior);
}

function trackScroll(data, tab) {
  const behavior = {
    type: 'scroll',
    timestamp: new Date().toISOString(),
    data: {
      ...data,
      url: tab.url,
      title: tab.title
    }
  };
  
  queueBehavior(behavior);
}

function trackTimeSpent(data, tab) {
  const behavior = {
    type: 'time_spent',
    timestamp: new Date().toISOString(),
    data: {
      ...data,
      url: tab.url,
      title: tab.title
    }
  };
  
  queueBehavior(behavior);
}

// Queue management
function queueBehavior(behavior) {
  if (!isAuthenticated) {
    console.log('Not authenticated, skipping behavior tracking');
    return;
  }
  
  behaviorQueue.push(behavior);
  
  // Process queue if it reaches batch size
  if (behaviorQueue.length >= BATCH_SIZE) {
    processBehaviorQueue();
  }
}

// Process and send behaviors to backend
async function processBehaviorQueue() {
  if (behaviorQueue.length === 0 || !isAuthenticated) {
    return;
  }
  
  const behaviors = [...behaviorQueue];
  behaviorQueue = []; // Clear queue
  
  try {
    const response = await fetch(`${API_BASE_URL}/behavioral/track-batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        behaviors: behaviors,
        source: 'chrome_extension'
      })
    });
    
    if (!response.ok) {
      // Re-queue behaviors if request failed
      behaviorQueue.unshift(...behaviors);
      console.error('Failed to send behaviors:', response.status);
      
      // If unauthorized, clear auth
      if (response.status === 401) {
        isAuthenticated = false;
        authToken = null;
        userId = null;
        await chrome.storage.local.remove(['authToken', 'userId']);
      }
    } else {
      console.log(`Successfully sent ${behaviors.length} behaviors`);
    }
  } catch (error) {
    // Re-queue behaviors if request failed
    behaviorQueue.unshift(...behaviors);
    console.error('Error sending behaviors:', error);
  }
}

// Periodic sync
function startPeriodicSync() {
  setInterval(() => {
    processBehaviorQueue();
  }, SYNC_INTERVAL);
}

// Pattern analysis (local processing)
chrome.alarms.create('analyzePatterns', { periodInMinutes: 60 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'analyzePatterns') {
    analyzeLocalPatterns();
  }
});

async function analyzeLocalPatterns() {
  try {
    // Get browsing history for pattern analysis
    const oneHourAgo = Date.now() - (60 * 60 * 1000);
    
    chrome.history.search({
      text: '',
      startTime: oneHourAgo,
      maxResults: 100
    }, (historyItems) => {
      const patterns = extractPatterns(historyItems);
      
      // Send patterns to backend
      if (patterns && isAuthenticated) {
        sendPatterns(patterns);
      }
    });
  } catch (error) {
    console.error('Error analyzing patterns:', error);
  }
}

function extractPatterns(historyItems) {
  const domains = {};
  const categories = {};
  const timePatterns = {};
  
  historyItems.forEach(item => {
    // Extract domain
    try {
      const url = new URL(item.url);
      const domain = url.hostname;
      domains[domain] = (domains[domain] || 0) + 1;
      
      // Categorize (simplified)
      const category = categorizeUrl(url);
      categories[category] = (categories[category] || 0) + 1;
      
      // Time patterns
      const hour = new Date(item.lastVisitTime).getHours();
      const timeSlot = getTimeSlot(hour);
      timePatterns[timeSlot] = (timePatterns[timeSlot] || 0) + 1;
    } catch (e) {
      // Invalid URL
    }
  });
  
  return {
    topDomains: Object.entries(domains)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10),
    categories: categories,
    timePatterns: timePatterns,
    totalVisits: historyItems.length
  };
}

function categorizeUrl(url) {
  const domain = url.hostname.toLowerCase();
  
  // Simple categorization based on domain
  if (domain.includes('google') || domain.includes('bing')) return 'search';
  if (domain.includes('youtube') || domain.includes('netflix')) return 'entertainment';
  if (domain.includes('facebook') || domain.includes('twitter') || domain.includes('instagram')) return 'social';
  if (domain.includes('github') || domain.includes('stackoverflow')) return 'development';
  if (domain.includes('amazon') || domain.includes('ebay')) return 'shopping';
  if (domain.includes('news') || domain.includes('cnn') || domain.includes('bbc')) return 'news';
  
  return 'other';
}

function getTimeSlot(hour) {
  if (hour >= 6 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 17) return 'afternoon';
  if (hour >= 17 && hour < 22) return 'evening';
  return 'night';
}

async function sendPatterns(patterns) {
  try {
    await fetch(`${API_BASE_URL}/behavioral/patterns`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        patterns: patterns,
        source: 'chrome_extension',
        timestamp: new Date().toISOString()
      })
    });
  } catch (error) {
    console.error('Error sending patterns:', error);
  }
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    trackPageVisit,
    trackClick,
    extractPatterns
  };
}