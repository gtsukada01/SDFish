/**
 * Rollback Manager - Emergency Fallbacks and Recovery
 * Provides comprehensive rollback procedures for production failures
 */

import { isFeatureEnabled } from './config/featureFlags.js';
import { logError, ERROR_CATEGORIES, ERROR_LEVELS } from './errorBoundary.js';
import performanceMonitor from './performanceMonitor.js';

/**
 * Rollback state management
 */
const rollbackState = {
  snapshots: new Map(),
  fallbackComponents: new Map(),
  emergencyMode: false,
  rollbackHistory: [],
  maxSnapshots: 5,
  lastSuccessfulState: null
};

/**
 * Rollback types
 */
export const ROLLBACK_TYPES = {
  COMPONENT: 'component',
  API: 'api',
  STATE: 'state',
  FULL_SYSTEM: 'full_system',
  DATA: 'data',
  UI: 'ui'
};

/**
 * Emergency modes
 */
export const EMERGENCY_MODES = {
  DEGRADED: 'degraded',
  MINIMAL: 'minimal',
  OFFLINE: 'offline',
  SAFE_MODE: 'safe_mode'
};

/**
 * Initialize rollback manager
 */
export function initializeRollbackManager() {
  // Create initial system snapshot
  createSystemSnapshot('initial');

  // Register critical error handlers
  if (typeof window !== 'undefined') {
    // Handle critical JavaScript errors
    window.addEventListener('error', (event) => {
      if (isCriticalError(event.error)) {
        triggerEmergencyFallback(EMERGENCY_MODES.DEGRADED, {
          trigger: 'critical_js_error',
          error: event.error.message,
          source: event.filename,
          line: event.lineno
        });
      }
    });

    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      if (isCriticalError(event.reason)) {
        triggerEmergencyFallback(EMERGENCY_MODES.DEGRADED, {
          trigger: 'unhandled_rejection',
          error: event.reason.message || event.reason
        });
      }
    });

    // Monitor API failures
    registerAPIFailureMonitor();

    // Register beforeunload cleanup
    window.addEventListener('beforeunload', () => {
      saveRollbackState();
    });
  }

  // Register periodic health checks
  startHealthCheckInterval();
}

/**
 * Create system snapshot for rollback
 */
export function createSystemSnapshot(name, includeDOM = false) {
  const snapshot = {
    name,
    timestamp: Date.now(),
    url: typeof window !== 'undefined' ? window.location.href : 'unknown',
    state: {},
    dom: null,
    featureFlags: {},
    apiHealth: null
  };

  try {
    // Capture current state if available
    if (typeof window !== 'undefined' && window.dashboardState) {
      snapshot.state = JSON.parse(JSON.stringify(window.dashboardState));
    }

    // Capture DOM snapshot if requested
    if (includeDOM && typeof document !== 'undefined') {
      snapshot.dom = {
        title: document.title,
        body: document.body.innerHTML,
        head: document.head.innerHTML
      };
    }

    // Capture feature flags state
    snapshot.featureFlags = {
      USE_NEW_API_CLIENT: isFeatureEnabled('USE_NEW_API_CLIENT'),
      USE_NEW_STATE: isFeatureEnabled('USE_NEW_STATE'),
      ENABLE_PERFORMANCE_MONITORING: isFeatureEnabled('ENABLE_PERFORMANCE_MONITORING')
    };

    // Test API health
    snapshot.apiHealth = checkAPIHealth();

    // Store snapshot
    rollbackState.snapshots.set(name, snapshot);

    // Maintain max snapshots limit
    if (rollbackState.snapshots.size > rollbackState.maxSnapshots) {
      const oldestKey = Array.from(rollbackState.snapshots.keys())[0];
      rollbackState.snapshots.delete(oldestKey);
    }

    // Update last successful state if this is a good snapshot
    if (snapshot.apiHealth?.healthy) {
      rollbackState.lastSuccessfulState = snapshot;
    }

    logError(`System snapshot created: ${name}`, {
      category: ERROR_CATEGORIES.SYSTEM,
      level: ERROR_LEVELS.LOW,
      context: 'rollback_snapshot',
      metadata: { snapshotName: name, includeDOM }
    });

    return snapshot;

  } catch (error) {
    logError(`Failed to create system snapshot: ${name}`, {
      category: ERROR_CATEGORIES.SYSTEM,
      level: ERROR_LEVELS.HIGH,
      context: 'rollback_snapshot_error',
      metadata: { snapshotName: name, error: error.message }
    });

    return null;
  }
}

/**
 * Execute rollback to previous snapshot
 */
export async function executeRollback(snapshotName, options = {}) {
  const {
    type = ROLLBACK_TYPES.COMPONENT,
    force = false,
    skipConfirmation = false
  } = options;

  const snapshot = rollbackState.snapshots.get(snapshotName);
  if (!snapshot) {
    throw new Error(`Snapshot not found: ${snapshotName}`);
  }

  // Confirmation check
  if (!skipConfirmation && !force && !confirm(`Execute rollback to ${snapshotName}?`)) {
    return { success: false, reason: 'User cancelled rollback' };
  }

  logError(`Executing rollback to: ${snapshotName}`, {
    category: ERROR_CATEGORIES.SYSTEM,
    level: ERROR_LEVELS.HIGH,
    context: 'rollback_execution',
    metadata: { snapshotName, type, force }
  });

  try {
    const rollbackStart = Date.now();

    // Execute rollback based on type
    switch (type) {
      case ROLLBACK_TYPES.STATE:
        await rollbackStateData(snapshot);
        break;

      case ROLLBACK_TYPES.COMPONENT:
        await rollbackComponents(snapshot);
        break;

      case ROLLBACK_TYPES.API:
        await rollbackAPIConfiguration(snapshot);
        break;

      case ROLLBACK_TYPES.UI:
        await rollbackUI(snapshot);
        break;

      case ROLLBACK_TYPES.FULL_SYSTEM:
        await rollbackFullSystem(snapshot);
        break;

      default:
        throw new Error(`Unknown rollback type: ${type}`);
    }

    const rollbackDuration = Date.now() - rollbackStart;

    // Record rollback in history
    rollbackState.rollbackHistory.push({
      timestamp: Date.now(),
      snapshotName,
      type,
      duration: rollbackDuration,
      success: true
    });

    // Create new snapshot after successful rollback
    createSystemSnapshot(`post_rollback_${Date.now()}`);

    return {
      success: true,
      duration: rollbackDuration,
      snapshot: snapshot.name
    };

  } catch (error) {
    logError(`Rollback failed: ${error.message}`, {
      category: ERROR_CATEGORIES.SYSTEM,
      level: ERROR_LEVELS.CRITICAL,
      context: 'rollback_failure',
      metadata: { snapshotName, type, error: error.message }
    });

    // Record failed rollback
    rollbackState.rollbackHistory.push({
      timestamp: Date.now(),
      snapshotName,
      type,
      success: false,
      error: error.message
    });

    throw error;
  }
}

/**
 * Trigger emergency fallback mode
 */
export function triggerEmergencyFallback(mode = EMERGENCY_MODES.DEGRADED, context = {}) {
  if (rollbackState.emergencyMode) {
    console.warn('Emergency mode already active');
    return;
  }

  rollbackState.emergencyMode = true;

  logError(`Emergency fallback triggered: ${mode}`, {
    category: ERROR_CATEGORIES.SYSTEM,
    level: ERROR_LEVELS.CRITICAL,
    context: 'emergency_fallback',
    metadata: { mode, context }
  });

  switch (mode) {
    case EMERGENCY_MODES.DEGRADED:
      activateDegradedMode(context);
      break;

    case EMERGENCY_MODES.MINIMAL:
      activateMinimalMode(context);
      break;

    case EMERGENCY_MODES.OFFLINE:
      activateOfflineMode(context);
      break;

    case EMERGENCY_MODES.SAFE_MODE:
      activateSafeMode(context);
      break;

    default:
      console.error(`Unknown emergency mode: ${mode}`);
      activateSafeMode(context);
  }
}

/**
 * Register component fallbacks
 */
export function registerFallback(componentName, fallbackRenderer, options = {}) {
  rollbackState.fallbackComponents.set(componentName, {
    renderer: fallbackRenderer,
    priority: options.priority || 1,
    conditions: options.conditions || [],
    metadata: options.metadata || {}
  });

  console.log(`📦 Fallback registered for ${componentName}`);
}

/**
 * Execute component fallback
 */
export function executeFallback(componentName, container, context = {}) {
  const fallback = rollbackState.fallbackComponents.get(componentName);

  if (!fallback) {
    // Generic fallback if no specific fallback registered
    return renderGenericFallback(componentName, container, context);
  }

  try {
    logError(`Executing fallback for: ${componentName}`, {
      category: ERROR_CATEGORIES.UI,
      level: ERROR_LEVELS.MEDIUM,
      context: 'component_fallback',
      metadata: { componentName, context }
    });

    return fallback.renderer(container, context);

  } catch (error) {
    logError(`Fallback execution failed for ${componentName}: ${error.message}`, {
      category: ERROR_CATEGORIES.UI,
      level: ERROR_LEVELS.HIGH,
      context: 'fallback_failure',
      metadata: { componentName, error: error.message }
    });

    return renderGenericFallback(componentName, container, { error: error.message });
  }
}

/**
 * Emergency mode implementations
 */
function activateDegradedMode(context) {
  console.warn('🚨 Activating Degraded Mode');

  // Disable non-essential features
  if (typeof window !== 'undefined') {
    window.featureFlags = {
      ...window.featureFlags,
      ENABLE_PERFORMANCE_MONITORING: false,
      ENABLE_ADVANCED_CHARTS: false,
      ENABLE_ANIMATIONS: false
    };
  }

  // Show degraded mode notification
  showEmergencyNotification('System running in degraded mode. Some features may be limited.', 'warning');

  // Attempt to use last successful state
  if (rollbackState.lastSuccessfulState) {
    setTimeout(() => {
      executeRollback(rollbackState.lastSuccessfulState.name, {
        type: ROLLBACK_TYPES.COMPONENT,
        skipConfirmation: true
      }).catch(() => {
        console.error('Failed to rollback to last successful state');
      });
    }, 1000);
  }
}

function activateMinimalMode(context) {
  console.warn('🚨 Activating Minimal Mode');

  // Show only essential UI elements
  const essentialElements = ['#header', '#filtersMount', '#statsGridContainer'];

  if (typeof document !== 'undefined') {
    // Hide non-essential elements
    document.querySelectorAll('body > *').forEach(element => {
      if (!essentialElements.some(selector => element.matches(selector))) {
        element.style.display = 'none';
      }
    });

    // Show minimal interface
    const minimalUI = createMinimalUI();
    document.body.appendChild(minimalUI);
  }

  showEmergencyNotification('System running in minimal mode. Full functionality will be restored shortly.', 'info');
}

function activateOfflineMode(context) {
  console.warn('🚨 Activating Offline Mode');

  // Show offline interface
  const offlineUI = createOfflineUI();
  if (typeof document !== 'undefined') {
    document.body.innerHTML = '';
    document.body.appendChild(offlineUI);
  }

  showEmergencyNotification('System is offline. Please check your connection and try again.', 'error');
}

function activateSafeMode(context) {
  console.warn('🚨 Activating Safe Mode');

  // Reset to absolute basics
  if (typeof document !== 'undefined') {
    document.body.innerHTML = createSafeModeHTML();
  }

  showEmergencyNotification('System running in safe mode. Contact support if problems persist.', 'error');
}

/**
 * Rollback type implementations
 */
async function rollbackStateData(snapshot) {
  if (typeof window !== 'undefined' && snapshot.state) {
    window.dashboardState = snapshot.state;
    console.log('✅ State rolled back successfully');
  }
}

async function rollbackComponents(snapshot) {
  // Re-render components using fallbacks
  const containers = ['statsGridContainer', 'chartsContainer', 'recentTripsContainer'];

  for (const containerId of containers) {
    const container = document.getElementById(containerId);
    if (container) {
      executeFallback(containerId, container, { rollback: true });
    }
  }

  console.log('✅ Components rolled back successfully');
}

async function rollbackAPIConfiguration(snapshot) {
  // Reset feature flags to snapshot state
  if (typeof window !== 'undefined' && snapshot.featureFlags) {
    window.featureFlags = { ...snapshot.featureFlags };
    console.log('✅ API configuration rolled back successfully');
  }
}

async function rollbackUI(snapshot) {
  if (typeof document !== 'undefined' && snapshot.dom) {
    document.title = snapshot.dom.title;
    document.body.innerHTML = snapshot.dom.body;
    console.log('✅ UI rolled back successfully');
  }
}

async function rollbackFullSystem(snapshot) {
  await rollbackStateData(snapshot);
  await rollbackAPIConfiguration(snapshot);
  await rollbackComponents(snapshot);
  console.log('✅ Full system rolled back successfully');
}

/**
 * UI creation helpers
 */
function createMinimalUI() {
  const div = document.createElement('div');
  div.className = 'minimal-mode';
  div.innerHTML = `
    <div class="minimal-interface">
      <h1>System Recovery Mode</h1>
      <p>The system is recovering from an error. Essential functions are available.</p>
      <button onclick="location.reload()" class="btn btn--primary">
        Reload Application
      </button>
    </div>
  `;
  return div;
}

function createOfflineUI() {
  const div = document.createElement('div');
  div.className = 'offline-mode';
  div.innerHTML = `
    <div class="offline-interface">
      <h1>Connection Lost</h1>
      <p>Unable to connect to the server. Please check your internet connection.</p>
      <button onclick="location.reload()" class="btn btn--primary">
        Try Again
      </button>
    </div>
  `;
  return div;
}

function createSafeModeHTML() {
  return `
    <div class="safe-mode">
      <h1>Safe Mode</h1>
      <p>The application encountered a critical error and is running in safe mode.</p>
      <ul>
        <li><a href="javascript:location.reload()">Reload Application</a></li>
        <li><a href="javascript:localStorage.clear();location.reload()">Clear Data & Reload</a></li>
        <li><a href="mailto:support@example.com">Contact Support</a></li>
      </ul>
    </div>
  `;
}

function renderGenericFallback(componentName, container, context) {
  const fallbackHTML = `
    <div class="component-fallback">
      <div class="fallback-content">
        <i data-lucide="alert-triangle"></i>
        <h3>Component Unavailable</h3>
        <p>${componentName} is temporarily unavailable.</p>
        ${context.error ? `<details><summary>Error Details</summary><pre>${context.error}</pre></details>` : ''}
        <button onclick="location.reload()" class="btn btn--secondary">
          Reload Page
        </button>
      </div>
    </div>
  `;

  if (container) {
    container.innerHTML = fallbackHTML;
  }

  return fallbackHTML;
}

/**
 * Utility functions
 */
function isCriticalError(error) {
  if (!error) return false;

  const criticalPatterns = [
    /cannot read property/i,
    /cannot access before initialization/i,
    /is not defined/i,
    /network error/i,
    /failed to fetch/i
  ];

  const errorMessage = error.message || error.toString();
  return criticalPatterns.some(pattern => pattern.test(errorMessage));
}

function checkAPIHealth() {
  // This would implement actual API health checks
  return { healthy: true, timestamp: Date.now() };
}

function registerAPIFailureMonitor() {
  let apiFailureCount = 0;
  const maxFailures = 3;

  // Monitor fetch failures
  if (typeof window !== 'undefined') {
    const originalFetch = window.fetch;

    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args);

        if (!response.ok) {
          apiFailureCount++;

          if (apiFailureCount >= maxFailures) {
            triggerEmergencyFallback(EMERGENCY_MODES.DEGRADED, {
              trigger: 'api_failure_threshold',
              failureCount: apiFailureCount
            });
          }
        } else {
          // Reset failure count on success
          apiFailureCount = Math.max(0, apiFailureCount - 1);
        }

        return response;
      } catch (error) {
        apiFailureCount++;

        if (apiFailureCount >= maxFailures) {
          triggerEmergencyFallback(EMERGENCY_MODES.OFFLINE, {
            trigger: 'network_failure',
            error: error.message
          });
        }

        throw error;
      }
    };
  }
}

function startHealthCheckInterval() {
  if (typeof window === 'undefined') return;

  setInterval(() => {
    // Perform basic health checks
    const memoryUsage = window.performance?.memory?.usedJSHeapSize || 0;
    const errorCount = rollbackState.rollbackHistory.filter(r => !r.success).length;

    // Check for deteriorating conditions
    if (memoryUsage > 100 * 1024 * 1024 || errorCount > 5) { // 100MB or 5+ errors
      console.warn('⚠️  System health degrading, creating recovery snapshot');
      createSystemSnapshot(`health_check_${Date.now()}`);
    }
  }, 60000); // Check every minute
}

function showEmergencyNotification(message, type = 'info') {
  if (typeof document === 'undefined') return;

  const notification = document.createElement('div');
  notification.className = `emergency-notification emergency-notification--${type}`;
  notification.innerHTML = `
    <div class="notification-content">
      <i data-lucide="${type === 'error' ? 'alert-circle' : type === 'warning' ? 'alert-triangle' : 'info'}"></i>
      <span>${message}</span>
      <button onclick="this.parentElement.parentElement.remove()" class="notification-close">
        <i data-lucide="x"></i>
      </button>
    </div>
  `;

  document.body.appendChild(notification);

  // Auto-remove after 10 seconds
  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 10000);
}

function saveRollbackState() {
  try {
    const stateToSave = {
      snapshots: Array.from(rollbackState.snapshots.entries()),
      rollbackHistory: rollbackState.rollbackHistory.slice(-10), // Keep last 10
      lastSuccessfulState: rollbackState.lastSuccessfulState
    };

    localStorage.setItem('rollback_state', JSON.stringify(stateToSave));
  } catch (error) {
    console.warn('Failed to save rollback state:', error.message);
  }
}

function loadRollbackState() {
  try {
    const saved = localStorage.getItem('rollback_state');
    if (saved) {
      const state = JSON.parse(saved);
      rollbackState.snapshots = new Map(state.snapshots || []);
      rollbackState.rollbackHistory = state.rollbackHistory || [];
      rollbackState.lastSuccessfulState = state.lastSuccessfulState;
    }
  } catch (error) {
    console.warn('Failed to load rollback state:', error.message);
  }
}

/**
 * Public API
 */
export const rollbackManager = {
  createSnapshot: createSystemSnapshot,
  rollback: executeRollback,
  registerFallback,
  executeFallback,
  triggerEmergency: triggerEmergencyFallback,
  getSnapshots: () => Array.from(rollbackState.snapshots.keys()),
  getHistory: () => [...rollbackState.rollbackHistory],
  isEmergencyMode: () => rollbackState.emergencyMode,
  exitEmergencyMode: () => {
    rollbackState.emergencyMode = false;
    console.log('✅ Emergency mode deactivated');
  }
};

// Auto-initialize when module loads
if (typeof window !== 'undefined') {
  loadRollbackState();
  initializeRollbackManager();
}