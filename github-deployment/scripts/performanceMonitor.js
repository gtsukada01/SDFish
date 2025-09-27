/**
 * Performance Monitoring Module (Production)
 * Mirrors the dev helper so instrumentation stays consistent in the static bundle.
 */

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

  recordMetric(operation, duration) {
    if (!isBrowser) return;

    const metric = {
      operation,
      duration,
      timestamp: new Date().toISOString(),
    };

    if (operation.includes('api') || operation.includes('fetch')) {
      this.metrics.apiCalls.push(metric);
    } else if (operation.includes('state')) {
      this.metrics.stateUpdates.push(metric);
    } else if (operation.includes('render')) {
      this.metrics.renderTimes.push(metric);
    }

    this.metrics.apiCalls = this.metrics.apiCalls.slice(-100);
    this.metrics.stateUpdates = this.metrics.stateUpdates.slice(-100);
    this.metrics.renderTimes = this.metrics.renderTimes.slice(-100);
  }

  getAverageTime(category) {
    const metrics = this.metrics[category] || [];
    if (metrics.length === 0) return 0;

    const sum = metrics.reduce((acc, m) => acc + m.duration, 0);
    return sum / metrics.length;
  }

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

  checkThreshold(operation, duration, threshold) {
    if (!isBrowser || duration <= threshold) return;
    console.warn(
      `Performance warning: ${operation} took ${duration.toFixed(2)}ms (threshold: ${threshold}ms)`
    );
  }

  clear() {
    this.metrics = {
      apiCalls: [],
      stateUpdates: [],
      renderTimes: [],
    };
  }

  setEnabled(enabled) {
    this.enabled = enabled;
  }

  record(operation, duration) {
    this.recordMetric(operation, duration);
  }
}

const performanceMonitor = new PerformanceMonitor();
export default performanceMonitor;

if (isBrowser && window.location.hostname === 'localhost') {
  window.__performanceMonitor = performanceMonitor;
  window.__perfSummary = () => {
    const summary = performanceMonitor.getSummary();
    console.warn('Performance summary', summary);
    return summary;
  };
}

export function timeStateUpdate(stateUpdateFn, operation) {
  const endTimer = performanceMonitor.startTimer(`state:${operation}`);
  const result = stateUpdateFn();
  endTimer();
  return result;
}

export function timeRender(renderFn, operation) {
  const endTimer = performanceMonitor.startTimer(`render:${operation}`);
  const result = renderFn();
  endTimer();
  return result;
}
