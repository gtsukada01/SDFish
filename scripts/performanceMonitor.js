/**
 * Performance Monitoring Module
 * Tracks API response times, state updates, and performance metrics
 */

// Check if we're in a browser environment
const isBrowser = typeof window !== 'undefined' && typeof window.performance !== 'undefined';

class PerformanceMonitor {
  constructor() {
    this.metrics = {
      apiCalls: [],
      stateUpdates: [],
      renderTimes: [],
    };
    this.enabled = true;
  }

  /**
   * Start timing an operation
   * @param {string} operation - Operation name
   * @returns {Function} - End timer function
   */
  startTimer(operation) {
    if (!this.enabled || !isBrowser) return () => {};

    const startTime = window.performance.now();
    return () => {
      const endTime = window.performance.now();
      const duration = endTime - startTime;
      this.recordMetric(operation, duration);
      return duration;
    };
  }

  /**
   * Record a metric
   * @param {string} operation - Operation name
   * @param {number} duration - Duration in milliseconds
   */
  recordMetric(operation, duration) {
    if (!isBrowser) return;

    const metric = {
      operation,
      duration,
      timestamp: new Date().toISOString(),
    };

    // Categorize by operation type
    if (operation.includes('api') || operation.includes('fetch')) {
      this.metrics.apiCalls.push(metric);
    } else if (operation.includes('state')) {
      this.metrics.stateUpdates.push(metric);
    } else if (operation.includes('render')) {
      this.metrics.renderTimes.push(metric);
    }

    // Keep only last 100 metrics per category
    this.metrics.apiCalls = this.metrics.apiCalls.slice(-100);
    this.metrics.stateUpdates = this.metrics.stateUpdates.slice(-100);
    this.metrics.renderTimes = this.metrics.renderTimes.slice(-100);
  }

  /**
   * Get average duration for an operation type
   * @param {string} category - Metric category
   * @returns {number} - Average duration in ms
   */
  getAverageTime(category) {
    const metrics = this.metrics[category] || [];
    if (metrics.length === 0) return 0;

    const sum = metrics.reduce((acc, m) => acc + m.duration, 0);
    return sum / metrics.length;
  }

  /**
   * Get performance summary
   * @returns {Object} - Performance summary
   */
  getSummary() {
    return {
      apiCallsAvg: this.getAverageTime('apiCalls').toFixed(2),
      apiCallsCount: this.metrics.apiCalls.length,
      stateUpdatesAvg: this.getAverageTime('stateUpdates').toFixed(2),
      stateUpdatesCount: this.metrics.stateUpdates.length,
      renderTimesAvg: this.getAverageTime('renderTimes').toFixed(2),
      renderTimesCount: this.metrics.renderTimes.length,
    };
  }

  /**
   * Log performance warning if threshold exceeded
   * @param {string} operation - Operation name
   * @param {number} duration - Duration in ms
   * @param {number} threshold - Threshold in ms
   */
  checkThreshold(operation, duration, threshold) {
    if (!isBrowser || duration <= threshold) return;

    console.warn(
      `Performance warning: ${operation} took ${duration.toFixed(2)}ms (threshold: ${threshold}ms)`
    );
  }

  /**
   * Clear all metrics
   */
  clear() {
    this.metrics = {
      apiCalls: [],
      stateUpdates: [],
      renderTimes: [],
    };
  }

  /**
   * Enable or disable monitoring
   * @param {boolean} enabled - Enable state
   */
  setEnabled(enabled) {
    this.enabled = enabled;
  }

  /**
   * Record a performance metric (alias for recordMetric)
   * @param {string} operation - Operation name
   * @param {number} duration - Duration in milliseconds
   */
  record(operation, duration) {
    this.recordMetric(operation, duration);
  }
}

// Create singleton instance
const performanceMonitor = new PerformanceMonitor();

// Export for module usage
export default performanceMonitor;

// Expose to window for debugging in development (only in browser)
if (isBrowser && window.location.hostname === 'localhost') {
  window.__performanceMonitor = performanceMonitor;
  window.__perfSummary = () => {
    const summary = performanceMonitor.getSummary();
    console.warn('Performance summary', summary);
    return summary;
  };
}

/**
 * Helper to time state updates
 * @param {Function} stateUpdateFn - State update function
 * @param {string} operation - Operation name
 * @returns {*} - Result of state update function
 */
export function timeStateUpdate(stateUpdateFn, operation) {
  const endTimer = performanceMonitor.startTimer(`state:${operation}`);
  const result = stateUpdateFn();
  endTimer();
  return result;
}

/**
 * Helper to time render operations
 * @param {Function} renderFn - Render function
 * @param {string} operation - Operation name
 * @returns {*} - Result of render function
 */
export function timeRender(renderFn, operation) {
  const endTimer = performanceMonitor.startTimer(`render:${operation}`);
  const result = renderFn();
  endTimer();
  return result;
}
