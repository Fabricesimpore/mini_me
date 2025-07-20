// Digital Twin Browser Tracker - Content Script
// Tracks user interactions within web pages

(function() {
  'use strict';

  // Configuration
  const SCROLL_DEBOUNCE_MS = 1000;
  const CLICK_COOLDOWN_MS = 100;
  const TIME_UPDATE_INTERVAL_MS = 30000; // 30 seconds

  // State
  let lastClickTime = 0;
  let scrollTimeout = null;
  let pageStartTime = Date.now();
  let totalScrollDistance = 0;
  let maxScrollDepth = 0;
  let clickCount = 0;

  // Initialize
  function init() {
    if (shouldSkipTracking()) {
      console.log('Skipping tracking for this page');
      return;
    }

    setupEventListeners();
    startTimeTracking();
    console.log('Digital Twin content script initialized');
  }

  // Check if we should skip tracking for this page
  function shouldSkipTracking() {
    const url = window.location.href;
    
    // Skip certain URLs
    const skipPatterns = [
      /^chrome:\/\//,
      /^chrome-extension:\/\//,
      /^about:/,
      /^file:\/\//,
      /localhost:\d+/  // Skip localhost development
    ];
    
    return skipPatterns.some(pattern => pattern.test(url));
  }

  // Setup event listeners
  function setupEventListeners() {
    // Click tracking
    document.addEventListener('click', handleClick, true);
    
    // Scroll tracking
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    // Form interaction tracking
    document.addEventListener('focus', handleFormFocus, true);
    document.addEventListener('change', handleFormChange, true);
    
    // Page visibility tracking
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Beforeunload tracking
    window.addEventListener('beforeunload', handlePageUnload);
  }

  // Click handler
  function handleClick(event) {
    const now = Date.now();
    
    // Debounce clicks
    if (now - lastClickTime < CLICK_COOLDOWN_MS) {
      return;
    }
    
    lastClickTime = now;
    clickCount++;

    const target = event.target;
    const clickData = {
      element: target.tagName.toLowerCase(),
      className: target.className || '',
      id: target.id || '',
      text: extractText(target),
      href: target.href || '',
      position: {
        x: event.pageX,
        y: event.pageY,
        viewportX: event.clientX,
        viewportY: event.clientY
      },
      timestamp: new Date().toISOString()
    };

    // Special handling for different element types
    if (target.tagName === 'A') {
      clickData.isExternalLink = isExternalLink(target.href);
    } else if (target.tagName === 'BUTTON' || target.type === 'submit') {
      clickData.isFormSubmit = true;
    }

    sendToBackground('track_click', clickData);
  }

  // Scroll handler
  function handleScroll() {
    // Clear existing timeout
    if (scrollTimeout) {
      clearTimeout(scrollTimeout);
    }

    // Update scroll metrics
    const currentScrollY = window.scrollY;
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = document.documentElement.clientHeight;
    const scrollPercentage = (currentScrollY / (scrollHeight - clientHeight)) * 100;

    totalScrollDistance += Math.abs(currentScrollY - (window.lastScrollY || 0));
    window.lastScrollY = currentScrollY;

    if (scrollPercentage > maxScrollDepth) {
      maxScrollDepth = scrollPercentage;
    }

    // Debounce scroll tracking
    scrollTimeout = setTimeout(() => {
      const scrollData = {
        scrollPercentage: Math.round(scrollPercentage),
        maxScrollDepth: Math.round(maxScrollDepth),
        totalScrollDistance: Math.round(totalScrollDistance),
        timestamp: new Date().toISOString()
      };

      sendToBackground('track_scroll', scrollData);
    }, SCROLL_DEBOUNCE_MS);
  }

  // Form focus handler
  function handleFormFocus(event) {
    const target = event.target;
    
    if (isFormElement(target)) {
      const formData = {
        element: target.tagName.toLowerCase(),
        type: target.type || '',
        name: target.name || '',
        id: target.id || '',
        action: 'focus',
        timestamp: new Date().toISOString()
      };

      sendToBackground('track_form_interaction', formData);
    }
  }

  // Form change handler
  function handleFormChange(event) {
    const target = event.target;
    
    if (isFormElement(target)) {
      const formData = {
        element: target.tagName.toLowerCase(),
        type: target.type || '',
        name: target.name || '',
        id: target.id || '',
        action: 'change',
        hasValue: !!target.value,
        timestamp: new Date().toISOString()
      };

      // Don't track actual values for privacy
      sendToBackground('track_form_interaction', formData);
    }
  }

  // Visibility change handler
  function handleVisibilityChange() {
    const visibilityData = {
      hidden: document.hidden,
      visibilityState: document.visibilityState,
      timestamp: new Date().toISOString()
    };

    sendToBackground('track_visibility', visibilityData);

    // Update time spent when page becomes hidden
    if (document.hidden) {
      updateTimeSpent();
    } else {
      // Reset start time when page becomes visible
      pageStartTime = Date.now();
    }
  }

  // Page unload handler
  function handlePageUnload() {
    updateTimeSpent();
  }

  // Time tracking
  function startTimeTracking() {
    // Send initial time update
    setTimeout(updateTimeSpent, TIME_UPDATE_INTERVAL_MS);

    // Set up periodic updates
    setInterval(updateTimeSpent, TIME_UPDATE_INTERVAL_MS);
  }

  function updateTimeSpent() {
    const timeSpent = Math.round((Date.now() - pageStartTime) / 1000); // in seconds

    const timeData = {
      timeSpent: timeSpent,
      clickCount: clickCount,
      maxScrollDepth: Math.round(maxScrollDepth),
      totalScrollDistance: Math.round(totalScrollDistance),
      timestamp: new Date().toISOString()
    };

    sendToBackground('track_time_spent', timeData);
  }

  // Utility functions
  function extractText(element) {
    // Extract meaningful text from element
    let text = element.textContent || element.innerText || '';
    text = text.trim().substring(0, 100); // Limit length
    return text;
  }

  function isExternalLink(href) {
    if (!href) return false;
    
    try {
      const url = new URL(href);
      return url.hostname !== window.location.hostname;
    } catch (e) {
      return false;
    }
  }

  function isFormElement(element) {
    const formTags = ['INPUT', 'SELECT', 'TEXTAREA'];
    return formTags.includes(element.tagName);
  }

  // Communication with background script
  function sendToBackground(type, data) {
    chrome.runtime.sendMessage({
      type: type,
      data: data
    }).catch(error => {
      // Extension might be reloading
      console.error('Error sending message to background:', error);
    });
  }

  // Page analysis
  function analyzePageContent() {
    // Extract page metadata
    const metadata = {
      title: document.title,
      description: getMetaContent('description'),
      keywords: getMetaContent('keywords'),
      author: getMetaContent('author'),
      ogType: getMetaContent('og:type'),
      articlePublished: getMetaContent('article:published_time'),
      wordCount: estimateWordCount(),
      linkCount: document.querySelectorAll('a').length,
      imageCount: document.querySelectorAll('img').length,
      hasVideo: document.querySelectorAll('video').length > 0,
      hasAudio: document.querySelectorAll('audio').length > 0,
      language: document.documentElement.lang || 'unknown'
    };

    return metadata;
  }

  function getMetaContent(name) {
    const meta = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
    return meta ? meta.content : null;
  }

  function estimateWordCount() {
    const text = document.body.innerText || document.body.textContent || '';
    return text.trim().split(/\s+/).length;
  }

  // Privacy-preserving content analysis
  function getPageTopics() {
    // Extract potential topics from headers and important text
    const headers = Array.from(document.querySelectorAll('h1, h2, h3'))
      .map(h => h.textContent.trim())
      .filter(text => text.length > 0);

    const importantText = Array.from(document.querySelectorAll('article, main, [role="main"]'))
      .map(el => el.textContent.trim().substring(0, 500))
      .filter(text => text.length > 0);

    return {
      headers: headers.slice(0, 10), // Top 10 headers
      summary: importantText[0] || '', // First important text block
      topics: extractTopics(headers.concat(importantText))
    };
  }

  function extractTopics(texts) {
    // Simple topic extraction (in production, use NLP)
    const commonTopics = {
      'technology': /\b(tech|software|computer|digital|app|web|internet|code|programming)\b/i,
      'business': /\b(business|company|market|finance|money|investment|startup|entrepreneur)\b/i,
      'health': /\b(health|medical|doctor|medicine|fitness|wellness|disease|treatment)\b/i,
      'education': /\b(education|learn|study|school|university|course|tutorial|teach)\b/i,
      'entertainment': /\b(movie|film|music|game|video|entertainment|show|series)\b/i,
      'news': /\b(news|breaking|update|report|announcement|latest|today|yesterday)\b/i,
      'shopping': /\b(buy|shop|product|price|deal|discount|sale|cart|order)\b/i,
      'social': /\b(social|friend|share|like|comment|post|profile|follow)\b/i
    };

    const detectedTopics = [];
    const fullText = texts.join(' ').toLowerCase();

    for (const [topic, pattern] of Object.entries(commonTopics)) {
      if (pattern.test(fullText)) {
        detectedTopics.push(topic);
      }
    }

    return detectedTopics;
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Analyze page content after load
  window.addEventListener('load', () => {
    const pageAnalysis = {
      metadata: analyzePageContent(),
      topics: getPageTopics(),
      timestamp: new Date().toISOString()
    };

    sendToBackground('track_page_analysis', pageAnalysis);
  });

})();