/**
 * Temporary Debug Helper Module
 * Enable: localStorage.setItem('debug', '1')
 * Disable: localStorage.removeItem('debug')
 *
 * This module can be completely removed after stabilization
 */

// Check if debug mode is enabled
function isDebugEnabled() {
  return localStorage.getItem('debug') === '1' || window.__DEBUG === true;
}

// Debug logging helper - only logs when debug is enabled
export function dbg(...args) {
  if (isDebugEnabled()) {
    const timestamp = new Date().toISOString().split('T')[1].slice(0, 12);
    console.log(`[DEBUG ${timestamp}]`, ...args);
  }
}

// Generate client request ID
export function generateRequestId() {
  return 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Track debug state
let debugState = {
  lastFilterChange: null,
  lastRequest: null,
  lastResponse: null,
  mappingStatus: {
    boatNameToIdMap: false,
    landingIdToNameMap: false
  },
  activeFilters: {},
  requestHistory: []
};

// Update debug state
export function updateDebugState(type, data) {
  if (!isDebugEnabled()) return;

  switch (type) {
    case 'filterChange':
      debugState.lastFilterChange = {
        ...data,
        timestamp: new Date().toISOString()
      };
      debugState.activeFilters = data.filters || {};
      dbg('Filter Change:', data);
      break;

    case 'request':
      debugState.lastRequest = {
        ...data,
        timestamp: new Date().toISOString(),
        requestId: data.requestId || generateRequestId()
      };
      debugState.requestHistory.push(debugState.lastRequest);
      if (debugState.requestHistory.length > 10) {
        debugState.requestHistory.shift(); // Keep only last 10
      }
      dbg('API Request:', data.url, data.params);
      break;

    case 'response':
      debugState.lastResponse = {
        ...data,
        timestamp: new Date().toISOString()
      };
      dbg('API Response:', data.status, `${data.rowCount} rows`, `${data.duration}ms`);
      break;

    case 'mapping':
      debugState.mappingStatus = {
        ...debugState.mappingStatus,
        ...data
      };
      dbg('Mapping Status:', data);
      break;
  }

  updateDebugOverlay();
}

// Create debug overlay panel
function createDebugOverlay() {
  if (!isDebugEnabled()) return;

  // Check if overlay already exists
  if (document.getElementById('debug-overlay')) return;

  const overlay = document.createElement('div');
  overlay.id = 'debug-overlay';
  overlay.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 350px;
    max-height: 400px;
    background: rgba(0, 0, 0, 0.9);
    color: #0f0;
    font-family: monospace;
    font-size: 11px;
    padding: 10px;
    border: 1px solid #0f0;
    border-radius: 5px;
    z-index: 99999;
    overflow-y: auto;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  `;

  overlay.innerHTML = `
    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
      <strong style="color: #0f0;">🔍 DEBUG MODE</strong>
      <button id="debug-close" style="background: transparent; color: #f00; border: none; cursor: pointer;">✕</button>
    </div>
    <div id="debug-content"></div>
  `;

  document.body.appendChild(overlay);

  // Add close button handler
  document.getElementById('debug-close').addEventListener('click', () => {
    overlay.remove();
  });

  updateDebugOverlay();
}

// Update debug overlay content
function updateDebugOverlay() {
  if (!isDebugEnabled()) return;

  const content = document.getElementById('debug-content');
  if (!content) {
    createDebugOverlay();
    return;
  }

  const state = debugState;

  content.innerHTML = `
    <div style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #0f0;">
      <strong>Mappings:</strong><br>
      Boat Map: ${state.mappingStatus.boatNameToIdMap ? '✅' : '❌'}
      ${state.mappingStatus.boatCount || 0} boats<br>
      Landing Map: ${state.mappingStatus.landingIdToNameMap ? '✅' : '❌'}
      ${state.mappingStatus.landingCount || 0} landings
    </div>

    ${state.lastFilterChange ? `
    <div style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #0f0;">
      <strong>Last Filter Change:</strong><br>
      ${new Date(state.lastFilterChange.timestamp).toLocaleTimeString()}<br>
      ${Object.entries(state.activeFilters)
        .filter(([k, v]) => v && v !== 'all')
        .map(([k, v]) => `${k}: ${v}`)
        .join('<br>') || 'No active filters'}
    </div>
    ` : ''}

    ${state.lastRequest ? `
    <div style="margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #0f0;">
      <strong>Last Request:</strong><br>
      ${state.lastRequest.method || 'GET'} ${state.lastRequest.url?.split('?')[0]}<br>
      <small style="color: #888;">ID: ${state.lastRequest.requestId}</small><br>
      <details style="margin-top: 5px;">
        <summary style="cursor: pointer;">Parameters</summary>
        <pre style="margin: 5px 0; color: #0a0; font-size: 10px;">${JSON.stringify(state.lastRequest.params, null, 2)}</pre>
      </details>
    </div>
    ` : ''}

    ${state.lastResponse ? `
    <div style="margin-bottom: 10px;">
      <strong>Last Response:</strong><br>
      Status: ${state.lastResponse.status}<br>
      Rows: ${state.lastResponse.rowCount || 0}<br>
      Duration: ${state.lastResponse.duration}ms<br>
      ${state.lastResponse.error ? `<span style="color: #f00;">Error: ${state.lastResponse.error}</span>` : ''}
    </div>
    ` : ''}

    <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #0f0;">
      <small style="color: #888;">
        Disable: localStorage.removeItem('debug')<br>
        Then reload page
      </small>
    </div>
  `;
}

// Wrap fetch to add diagnostics
export function wrapFetch(originalFetch) {
  return async function diagnosticFetch(url, options = {}) {
    if (!isDebugEnabled()) {
      return originalFetch(url, options);
    }

    const requestId = generateRequestId();
    const startTime = Date.now();

    // Parse URL to get params
    const urlObj = new URL(url, window.location.origin);
    const params = Object.fromEntries(urlObj.searchParams);

    // Log request
    updateDebugState('request', {
      url: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      params,
      requestId
    });

    // Add request ID header
    options.headers = {
      ...options.headers,
      'X-Client-Request-Id': requestId
    };

    try {
      const response = await originalFetch(url, options);
      const duration = Date.now() - startTime;

      // Clone response to read it
      const cloned = response.clone();
      let rowCount = 0;

      try {
        const data = await cloned.json();
        if (data.data && Array.isArray(data.data)) {
          rowCount = data.data.length;
        } else if (Array.isArray(data)) {
          rowCount = data.length;
        }
      } catch (e) {
        // Not JSON or error reading
      }

      // Log response
      updateDebugState('response', {
        status: response.status,
        rowCount,
        duration,
        requestId,
        serverRequestId: response.headers.get('X-Request-Id')
      });

      return response;
    } catch (error) {
      const duration = Date.now() - startTime;

      updateDebugState('response', {
        status: 'error',
        error: error.message,
        duration,
        requestId
      });

      throw error;
    }
  };
}

// Check mapping population
export function checkMappings() {
  if (!isDebugEnabled()) return;

  const boatMap = window.boatNameToIdMap || {};
  const landingMap = window.landingIdToNameMap || {};

  const status = {
    boatNameToIdMap: Object.keys(boatMap).length > 0,
    boatCount: Object.keys(boatMap).length,
    landingIdToNameMap: Object.keys(landingMap).length > 0,
    landingCount: Object.keys(landingMap).length
  };

  updateDebugState('mapping', status);

  if (!status.boatNameToIdMap) {
    console.warn('[DEBUG] boatNameToIdMap is empty!');
  }
  if (!status.landingIdToNameMap) {
    console.warn('[DEBUG] landingIdToNameMap is empty!');
  }

  return status;
}

// Initialize debug mode if enabled
export function initDebug() {
  if (isDebugEnabled()) {
    console.log('%c🔍 DEBUG MODE ENABLED', 'background: #0f0; color: #000; padding: 5px 10px; font-weight: bold;');
    console.log('Disable with: localStorage.removeItem("debug"); location.reload()');

    // Create overlay
    createDebugOverlay();

    // Wrap fetch
    if (typeof window.fetch !== 'undefined' && !window.fetch.__wrapped) {
      const originalFetch = window.fetch;
      window.fetch = wrapFetch(originalFetch);
      window.fetch.__wrapped = true;
    }

    // Check mappings after a delay
    setTimeout(checkMappings, 2000);

    return true;
  }
  return false;
}

// Export debug state for external access
export function getDebugState() {
  return debugState;
}

// Clean up debug mode
export function cleanupDebug() {
  const overlay = document.getElementById('debug-overlay');
  if (overlay) {
    overlay.remove();
  }

  // Restore original fetch if wrapped
  if (window.fetch && window.fetch.__wrapped) {
    // Note: This is tricky to properly unwrap, usually requires page reload
    console.log('[DEBUG] Fetch wrapper removed (reload recommended)');
  }
}