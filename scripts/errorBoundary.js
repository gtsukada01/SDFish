/**
 * Error Boundary System - Production Error Handling
 * Provides comprehensive error boundaries and graceful degradation
 */

import { isFeatureEnabled } from './config/featureFlags.js';
import performanceMonitor from './performanceMonitor.js';

/**
 * Global error tracking
 */
const errorRegistry = new Map();
const errorListeners = new Set();

/**
 * Error severity levels
 */
export const ERROR_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

/**
 * Error categories
 */
export const ERROR_CATEGORIES = {
  NETWORK: 'network',
  DATA: 'data',
  UI: 'ui',
  PERFORMANCE: 'performance',
  SYSTEM: 'system'
};

/**
 * Register global error handlers
 */
export function initializeErrorBoundary() {
  // Catch unhandled promise rejections
  if (typeof window !== 'undefined') {
    window.addEventListener('unhandledrejection', (event) => {
      logError(event.reason, {
        category: ERROR_CATEGORIES.SYSTEM,
        level: ERROR_LEVELS.HIGH,
        context: 'unhandledrejection',
        source: 'global'
      });
    });

    // Catch JavaScript errors
    window.addEventListener('error', (event) => {
      logError(event.error || event.message, {
        category: ERROR_CATEGORIES.SYSTEM,
        level: ERROR_LEVELS.CRITICAL,
        context: 'javascript',
        source: event.filename,
        line: event.lineno,
        column: event.colno
      });
    });
  }
}

/**
 * Log error with context and metadata
 * @param {Error|string} error - Error object or message
 * @param {Object} context - Error context
 */
export function logError(error, context = {}) {
  const errorId = generateErrorId();
  const timestamp = new Date().toISOString();

  const errorRecord = {
    id: errorId,
    timestamp,
    message: typeof error === 'string' ? error : error.message,
    stack: error.stack || null,
    category: context.category || ERROR_CATEGORIES.SYSTEM,
    level: context.level || ERROR_LEVELS.MEDIUM,
    context: context.context || 'unknown',
    source: context.source || 'unknown',
    metadata: {
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'server',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown',
      ...context.metadata
    }
  };

  // Store error
  errorRegistry.set(errorId, errorRecord);

  // Notify listeners
  errorListeners.forEach(listener => {
    try {
      listener(errorRecord);
    } catch (listenerError) {
      console.error('Error in error listener:', listenerError);
    }
  });

  // Log to console in development
  if (isFeatureEnabled('ENABLE_DEBUG_LOGGING')) {
    console.group(`🚨 Error [${errorRecord.level.toUpperCase()}]`);
    console.error('Message:', errorRecord.message);
    console.error('Category:', errorRecord.category);
    console.error('Context:', errorRecord.context);
    if (errorRecord.stack) console.error('Stack:', errorRecord.stack);
    console.error('Metadata:', errorRecord.metadata);
    console.groupEnd();
  }

  return errorId;
}

/**
 * Add error listener
 * @param {Function} listener - Error listener function
 * @returns {Function} - Unsubscribe function
 */
export function addErrorListener(listener) {
  errorListeners.add(listener);
  return () => errorListeners.delete(listener);
}

/**
 * Get error by ID
 * @param {string} errorId - Error ID
 * @returns {Object|null} - Error record
 */
export function getError(errorId) {
  return errorRegistry.get(errorId) || null;
}

/**
 * Get errors by category
 * @param {string} category - Error category
 * @returns {Array} - Array of error records
 */
export function getErrorsByCategory(category) {
  return Array.from(errorRegistry.values()).filter(error => error.category === category);
}

/**
 * Clear errors older than specified time
 * @param {number} maxAge - Maximum age in milliseconds (default: 1 hour)
 */
export function cleanupOldErrors(maxAge = 60 * 60 * 1000) {
  const cutoff = Date.now() - maxAge;

  for (const [id, error] of errorRegistry.entries()) {
    if (new Date(error.timestamp).getTime() < cutoff) {
      errorRegistry.delete(id);
    }
  }
}

/**
 * Async error boundary wrapper
 * @param {Function} asyncFn - Async function to wrap
 * @param {Object} context - Error context
 * @returns {Function} - Wrapped function
 */
export function withErrorBoundary(asyncFn, context = {}) {
  return async (...args) => {
    try {
      return await asyncFn(...args);
    } catch (error) {
      const errorId = logError(error, {
        category: context.category || ERROR_CATEGORIES.SYSTEM,
        level: context.level || ERROR_LEVELS.MEDIUM,
        context: context.name || asyncFn.name || 'anonymous',
        source: context.source || 'wrapped_function',
        metadata: context.metadata || {}
      });

      // Re-throw with error ID for tracking
      const wrappedError = new Error(error.message);
      wrappedError.errorId = errorId;
      wrappedError.originalError = error;
      throw wrappedError;
    }
  };
}

/**
 * UI Component error boundary
 * @param {Function} renderFn - Render function
 * @param {Object} fallbackOptions - Fallback options
 * @returns {Function} - Safe render function
 */
export function withUIErrorBoundary(renderFn, fallbackOptions = {}) {
  return (...args) => {
    try {
      return renderFn(...args);
    } catch (error) {
      logError(error, {
        category: ERROR_CATEGORIES.UI,
        level: ERROR_LEVELS.MEDIUM,
        context: fallbackOptions.componentName || 'ui_component',
        source: 'render_function'
      });

      // Return fallback UI
      return createErrorFallback(error, fallbackOptions);
    }
  };
}

/**
 * Create error fallback UI
 * @param {Error} error - Error that occurred
 * @param {Object} options - Fallback options
 * @returns {string} - HTML for error fallback
 */
export function createErrorFallback(error, options = {}) {
  const {
    title = 'Something went wrong',
    message = 'An error occurred while loading this component.',
    showRetry = true,
    componentId = null
  } = options;

  const retryButton = showRetry ? `
    <button class="btn btn--secondary error-retry" ${componentId ? `data-component="${componentId}"` : ''}>
      <i data-lucide="refresh-cw"></i>
      Try Again
    </button>
  ` : '';

  return `
    <div class="error-boundary">
      <div class="error-boundary__content">
        <i data-lucide="alert-triangle" class="error-boundary__icon"></i>
        <h3 class="error-boundary__title">${title}</h3>
        <p class="error-boundary__message">${message}</p>
        ${retryButton}
        ${isFeatureEnabled('ENABLE_DEBUG_LOGGING') ? `
          <details class="error-boundary__details">
            <summary>Technical Details</summary>
            <pre class="error-boundary__stack">${error.stack || error.message}</pre>
          </details>
        ` : ''}
      </div>
    </div>
  `;
}

/**
 * Network error handler with automatic retry
 * @param {Error} error - Network error
 * @param {Object} options - Retry options
 * @returns {Object} - Error info with retry function
 */
export function handleNetworkError(error, options = {}) {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    backoffMultiplier = 2
  } = options;

  logError(error, {
    category: ERROR_CATEGORIES.NETWORK,
    level: ERROR_LEVELS.HIGH,
    context: 'network_request',
    metadata: { maxRetries, retryDelay }
  });

  let retryCount = 0;

  const retry = async (originalFn) => {
    if (retryCount >= maxRetries) {
      throw new Error(`Network request failed after ${maxRetries} retries: ${error.message}`);
    }

    retryCount++;
    const delay = retryDelay * Math.pow(backoffMultiplier, retryCount - 1);

    await new Promise(resolve => setTimeout(resolve, delay));

    try {
      return await originalFn();
    } catch (retryError) {
      return retry(originalFn);
    }
  };

  return {
    error,
    retry,
    retryCount: () => retryCount,
    canRetry: () => retryCount < maxRetries
  };
}

/**
 * Performance error handler
 * @param {string} operation - Operation name
 * @param {number} duration - Operation duration in ms
 * @param {number} threshold - Performance threshold
 */
export function handlePerformanceError(operation, duration, threshold) {
  if (duration > threshold) {
    logError(`Performance threshold exceeded: ${operation} took ${duration}ms (threshold: ${threshold}ms)`, {
      category: ERROR_CATEGORIES.PERFORMANCE,
      level: duration > threshold * 2 ? ERROR_LEVELS.HIGH : ERROR_LEVELS.MEDIUM,
      context: 'performance_monitoring',
      metadata: { operation, duration, threshold }
    });
  }
}

/**
 * Generate unique error ID
 * @returns {string} - Unique error ID
 */
function generateErrorId() {
  return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Get error summary statistics
 * @returns {Object} - Error statistics
 */
export function getErrorStats() {
  const errors = Array.from(errorRegistry.values());
  const now = Date.now();
  const hourAgo = now - (60 * 60 * 1000);

  return {
    total: errors.length,
    lastHour: errors.filter(e => new Date(e.timestamp).getTime() > hourAgo).length,
    byCategory: errors.reduce((acc, error) => {
      acc[error.category] = (acc[error.category] || 0) + 1;
      return acc;
    }, {}),
    byLevel: errors.reduce((acc, error) => {
      acc[error.level] = (acc[error.level] || 0) + 1;
      return acc;
    }, {})
  };
}

/**
 * Initialize cleanup interval for old errors
 */
if (typeof window !== 'undefined') {
  setInterval(() => {
    cleanupOldErrors();
  }, 15 * 60 * 1000); // Clean up every 15 minutes
}

// Auto-initialize when module loads
if (typeof window !== 'undefined') {
  initializeErrorBoundary();
}