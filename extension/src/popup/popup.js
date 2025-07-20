// Digital Twin Browser Tracker - Popup Script

const API_BASE_URL = 'http://localhost:8000/api';

// DOM Elements
const authSection = document.getElementById('auth-section');
const loginForm = document.getElementById('login-form');
const loggedInDiv = document.getElementById('logged-in');
const statsSection = document.getElementById('stats-section');
const trackingSection = document.getElementById('tracking-section');
const privacySection = document.getElementById('privacy-section');

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  await checkAuthStatus();
  setupEventListeners();
  await loadStats();
  await updateCurrentSite();
});

// Check authentication status
async function checkAuthStatus() {
  const response = await chrome.runtime.sendMessage({ type: 'auth_status' });
  
  if (response.isAuthenticated) {
    showLoggedInState(response.userId);
    loadUserStats();
  } else {
    showLoginForm();
  }
}

// Show login form
function showLoginForm() {
  loginForm.classList.remove('hidden');
  loggedInDiv.classList.add('hidden');
  statsSection.classList.add('hidden');
  trackingSection.classList.add('hidden');
  privacySection.classList.add('hidden');
}

// Show logged in state
function showLoggedInState(userId) {
  loginForm.classList.add('hidden');
  loggedInDiv.classList.remove('hidden');
  statsSection.classList.remove('hidden');
  trackingSection.classList.remove('hidden');
  privacySection.classList.remove('hidden');
  
  // Show user email (stored locally)
  chrome.storage.local.get(['userEmail'], (result) => {
    if (result.userEmail) {
      document.getElementById('user-email').textContent = result.userEmail;
    }
  });
}

// Setup event listeners
function setupEventListeners() {
  // Login button
  document.getElementById('login-btn').addEventListener('click', handleLogin);
  
  // Enter key on password field
  document.getElementById('password').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      handleLogin();
    }
  });
  
  // Logout button
  document.getElementById('logout-btn').addEventListener('click', handleLogout);
  
  // Tracking toggle
  document.getElementById('tracking-toggle').addEventListener('change', handleTrackingToggle);
  
  // Privacy settings
  const privacyCheckboxes = ['track-clicks', 'track-scrolls', 'track-time', 'track-forms'];
  privacyCheckboxes.forEach(id => {
    document.getElementById(id).addEventListener('change', handlePrivacyChange);
  });
  
  // Footer links
  document.getElementById('open-dashboard').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'http://localhost:3000' });
  });
  
  document.getElementById('view-patterns').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'http://localhost:3000/behavioral' });
  });
}

// Handle login
async function handleLogin() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const errorMsg = document.getElementById('error-msg');
  
  if (!email || !password) {
    showError('Please enter email and password');
    return;
  }
  
  try {
    // Login via API
    const response = await fetch(`${API_BASE_URL}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: email,
        password: password
      })
    });
    
    if (!response.ok) {
      throw new Error('Invalid credentials');
    }
    
    const data = await response.json();
    
    // Get user info
    const userResponse = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${data.access_token}`
      }
    });
    
    const userData = await userResponse.json();
    
    // Send auth to background script
    await chrome.runtime.sendMessage({
      type: 'set_auth',
      token: data.access_token,
      userId: userData.user_id
    });
    
    // Store user email
    await chrome.storage.local.set({ userEmail: email });
    
    // Show logged in state
    showLoggedInState(userData.user_id);
    loadUserStats();
    
  } catch (error) {
    showError(error.message || 'Login failed');
  }
}

// Handle logout
async function handleLogout() {
  // Clear auth from background
  await chrome.runtime.sendMessage({
    type: 'set_auth',
    token: null,
    userId: null
  });
  
  // Clear stored data
  await chrome.storage.local.clear();
  
  // Show login form
  showLoginForm();
}

// Show error message
function showError(message) {
  const errorMsg = document.getElementById('error-msg');
  errorMsg.textContent = message;
  errorMsg.classList.remove('hidden');
  
  // Hide after 3 seconds
  setTimeout(() => {
    errorMsg.classList.add('hidden');
  }, 3000);
}

// Load user stats
async function loadUserStats() {
  try {
    // Get stats from local storage (updated by background script)
    const stats = await chrome.storage.local.get([
      'todayPageCount',
      'todayTimeSpent',
      'todayClickCount',
      'todayDomainCount'
    ]);
    
    // Update UI
    document.getElementById('pages-visited').textContent = stats.todayPageCount || 0;
    document.getElementById('time-spent').textContent = formatTime(stats.todayTimeSpent || 0);
    document.getElementById('clicks-made').textContent = stats.todayClickCount || 0;
    document.getElementById('domains-visited').textContent = stats.todayDomainCount || 0;
    
  } catch (error) {
    console.error('Error loading stats:', error);
  }
}

// Load tracking settings
async function loadStats() {
  const settings = await chrome.storage.local.get([
    'trackingEnabled',
    'trackClicks',
    'trackScrolls',
    'trackTime',
    'trackForms'
  ]);
  
  // Set defaults if not set
  document.getElementById('tracking-toggle').checked = settings.trackingEnabled !== false;
  document.getElementById('track-clicks').checked = settings.trackClicks !== false;
  document.getElementById('track-scrolls').checked = settings.trackScrolls !== false;
  document.getElementById('track-time').checked = settings.trackTime !== false;
  document.getElementById('track-forms').checked = settings.trackForms !== false;
  
  updateTrackingStatus(settings.trackingEnabled !== false);
}

// Handle tracking toggle
async function handleTrackingToggle(event) {
  const enabled = event.target.checked;
  await chrome.storage.local.set({ trackingEnabled: enabled });
  updateTrackingStatus(enabled);
}

// Update tracking status UI
function updateTrackingStatus(enabled) {
  const indicator = document.getElementById('status-indicator');
  const statusText = document.getElementById('status-text');
  
  if (enabled) {
    indicator.classList.remove('inactive');
    statusText.textContent = 'Active';
  } else {
    indicator.classList.add('inactive');
    statusText.textContent = 'Paused';
  }
}

// Handle privacy changes
async function handlePrivacyChange(event) {
  const setting = event.target.id.replace('-', '');
  const value = event.target.checked;
  
  await chrome.storage.local.set({ [setting]: value });
}

// Update current site info
async function updateCurrentSite() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (tab && tab.url) {
      const url = new URL(tab.url);
      document.getElementById('current-domain').textContent = url.hostname;
      
      // Get time on site from content script
      chrome.tabs.sendMessage(tab.id, { type: 'get_time_on_site' }, (response) => {
        if (response && response.timeOnSite) {
          document.getElementById('time-on-site').textContent = formatTime(response.timeOnSite);
        }
      });
    }
  } catch (error) {
    document.getElementById('current-domain').textContent = 'N/A';
  }
}

// Format time display
function formatTime(seconds) {
  if (seconds < 60) {
    return `${seconds}s`;
  } else if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}m`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
}

// Refresh stats periodically
setInterval(() => {
  loadUserStats();
  updateCurrentSite();
}, 5000);