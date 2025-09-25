/**
 * Performance Validation and Optimization
 * Provides comprehensive performance monitoring and validation
 */

import { isFeatureEnabled } from './config/featureFlags.js';
import { logError, ERROR_CATEGORIES, ERROR_LEVELS } from './errorBoundary.js';
import performanceMonitor from './performanceMonitor.js';

/**
 * Performance thresholds in milliseconds
 */
export const PERFORMANCE_THRESHOLDS = {
  // Component rendering thresholds
  CARD_RENDER: 50,
  TABLE_RENDER: 100,
  CHART_RENDER: 200,
  FORM_RENDER: 30,

  // API response thresholds
  API_FILTERS: 500,
  API_STATS: 1000,
  API_CHARTS: 1500,
  API_TRIPS: 800,

  // DOM operation thresholds
  DOM_QUERY: 10,
  DOM_UPDATE: 50,
  DOM_LARGE_UPDATE: 200,

  // Critical user interaction thresholds
  FILTER_RESPONSE: 300,
  NAVIGATION_RESPONSE: 200,
  ERROR_DISPLAY: 100,

  // Memory thresholds (in MB)
  MEMORY_USAGE: 50,
  MEMORY_LEAK_THRESHOLD: 10
};

/**
 * Performance metrics tracking
 */
const performanceMetrics = {
  measurements: new Map(),
  trends: new Map(),
  violations: new Map(),
  memoryBaseline: null,
  lastGCTime: Date.now()
};

/**
 * Initialize performance validation
 */
export function initializePerformanceValidator() {
  if (!isFeatureEnabled('ENABLE_PERFORMANCE_MONITORING')) {
    return;
  }

  // Set memory baseline
  if (typeof window !== 'undefined' && window.performance && window.performance.memory) {
    performanceMetrics.memoryBaseline = window.performance.memory.usedJSHeapSize;
  }

  // Monitor resource loading
  if (typeof window !== 'undefined' && window.PerformanceObserver) {
    try {
      // Monitor navigation timing
      const navObserver = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.entryType === 'navigation') {
            recordMetric('page_load', entry.loadEventEnd - entry.navigationStart);
            recordMetric('dom_content_loaded', entry.domContentLoadedEventEnd - entry.navigationStart);
            recordMetric('first_paint', entry.loadEventEnd - entry.responseStart);
          }
        });
      });
      navObserver.observe({ entryTypes: ['navigation'] });

      // Monitor resource timing
      const resourceObserver = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.entryType === 'resource') {
            recordMetric(`resource_${getResourceType(entry.name)}`, entry.duration);
          }
        });
      });
      resourceObserver.observe({ entryTypes: ['resource'] });

    } catch (error) {
      console.warn('Performance Observer not supported:', error);
    }
  }

  // Start memory monitoring interval
  startMemoryMonitoring();

  // Register cleanup on page unload
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', () => {
      generatePerformanceReport();
    });
  }
}

/**
 * Record performance metric
 */
export function recordMetric(name, duration, context = {}) {
  const timestamp = Date.now();
  const metric = {
    name,
    duration,
    timestamp,
    context
  };

  // Store measurement
  if (!performanceMetrics.measurements.has(name)) {
    performanceMetrics.measurements.set(name, []);
  }
  performanceMetrics.measurements.get(name).push(metric);

  // Check threshold violations
  checkThresholdViolation(name, duration, context);

  // Update trends
  updatePerformanceTrend(name, duration);

  // Log to performance monitor if enabled
  if (isFeatureEnabled('ENABLE_PERFORMANCE_MONITORING')) {
    performanceMonitor.record(name, duration);
  }
}

/**
 * Validate component performance
 */
export async function validateComponentPerformance(componentName, renderFn, expectedThreshold) {
  const startTime = performance.now();

  try {
    const result = await renderFn();
    const duration = Math.round(performance.now() - startTime);

    recordMetric(`component_${componentName}`, duration);

    if (duration > expectedThreshold) {
      const violation = {
        component: componentName,
        duration,
        threshold: expectedThreshold,
        timestamp: Date.now()
      };

      recordThresholdViolation(`component_${componentName}`, violation);

      logError(`Performance violation: ${componentName} took ${duration}ms (threshold: ${expectedThreshold}ms)`, {
        category: ERROR_CATEGORIES.PERFORMANCE,
        level: ERROR_LEVELS.MEDIUM,
        context: 'component_performance',
        metadata: violation
      });
    }

    return { result, duration, passed: duration <= expectedThreshold };
  } catch (error) {
    const duration = Math.round(performance.now() - startTime);
    recordMetric(`component_${componentName}_error`, duration);

    logError(error, {
      category: ERROR_CATEGORIES.PERFORMANCE,
      level: ERROR_LEVELS.HIGH,
      context: 'component_performance_error',
      metadata: { component: componentName, duration }
    });

    throw error;
  }
}

/**
 * Validate API performance
 */
export async function validateApiPerformance(endpoint, requestFn, expectedThreshold) {
  const endpointName = endpoint.replace(/[^a-zA-Z0-9]/g, '_');
  const startTime = performance.now();

  try {
    const result = await requestFn();
    const duration = Math.round(performance.now() - startTime);

    recordMetric(`api_${endpointName}`, duration, { endpoint });

    if (duration > expectedThreshold) {
      const violation = {
        endpoint,
        duration,
        threshold: expectedThreshold,
        timestamp: Date.now()
      };

      recordThresholdViolation(`api_${endpointName}`, violation);

      // Log warning for API performance issues
      console.warn(`⚠️  API Performance: ${endpoint} took ${duration}ms (threshold: ${expectedThreshold}ms)`);
    }

    return { result, duration, passed: duration <= expectedThreshold };
  } catch (error) {
    const duration = Math.round(performance.now() - startTime);
    recordMetric(`api_${endpointName}_error`, duration, { endpoint, error: error.message });

    throw error;
  }
}

/**
 * Monitor DOM operation performance
 */
export function validateDOMPerformance(operationName, domFn, expectedThreshold) {
  return new Promise((resolve, reject) => {
    const startTime = performance.now();

    // Use requestAnimationFrame to measure actual DOM operations
    requestAnimationFrame(() => {
      try {
        const result = domFn();
        const duration = Math.round(performance.now() - startTime);

        recordMetric(`dom_${operationName}`, duration);

        if (duration > expectedThreshold) {
          console.warn(`⚠️  DOM Performance: ${operationName} took ${duration}ms (threshold: ${expectedThreshold}ms)`);
        }

        resolve({ result, duration, passed: duration <= expectedThreshold });
      } catch (error) {
        const duration = Math.round(performance.now() - startTime);
        recordMetric(`dom_${operationName}_error`, duration);
        reject(error);
      }
    });
  });
}

/**
 * Memory usage validation
 */
export function validateMemoryUsage() {
  if (typeof window === 'undefined' || !window.performance || !window.performance.memory) {
    return { supported: false };
  }

  const memory = window.performance.memory;
  const currentUsage = memory.usedJSHeapSize / 1024 / 1024; // Convert to MB
  const totalHeap = memory.totalJSHeapSize / 1024 / 1024;
  const heapLimit = memory.jsHeapSizeLimit / 1024 / 1024;

  const baseline = performanceMetrics.memoryBaseline ?
    (performanceMetrics.memoryBaseline / 1024 / 1024) : currentUsage;
  const memoryIncrease = currentUsage - baseline;

  const result = {
    supported: true,
    currentUsage: Math.round(currentUsage * 100) / 100,
    totalHeap: Math.round(totalHeap * 100) / 100,
    heapLimit: Math.round(heapLimit * 100) / 100,
    baseline: Math.round(baseline * 100) / 100,
    increase: Math.round(memoryIncrease * 100) / 100,
    utilizationPercent: Math.round((currentUsage / heapLimit) * 100),
    violations: []
  };

  // Check for memory violations
  if (currentUsage > PERFORMANCE_THRESHOLDS.MEMORY_USAGE) {
    result.violations.push({
      type: 'high_usage',
      threshold: PERFORMANCE_THRESHOLDS.MEMORY_USAGE,
      current: result.currentUsage
    });
  }

  if (memoryIncrease > PERFORMANCE_THRESHOLDS.MEMORY_LEAK_THRESHOLD) {
    result.violations.push({
      type: 'potential_leak',
      threshold: PERFORMANCE_THRESHOLDS.MEMORY_LEAK_THRESHOLD,
      increase: result.increase
    });
  }

  // Log memory violations
  result.violations.forEach(violation => {
    logError(`Memory violation: ${violation.type}`, {
      category: ERROR_CATEGORIES.PERFORMANCE,
      level: ERROR_LEVELS.HIGH,
      context: 'memory_validation',
      metadata: violation
    });
  });

  recordMetric('memory_usage', result.currentUsage);

  return result;
}

/**
 * Run comprehensive performance audit
 */
export async function runPerformanceAudit() {
  console.group('🔍 Performance Audit');

  const audit = {
    timestamp: new Date().toISOString(),
    metrics: {},
    violations: {},
    memory: {},
    trends: {},
    recommendations: []
  };

  try {
    // Memory validation
    audit.memory = validateMemoryUsage();
    console.log('💾 Memory Usage:', `${audit.memory.currentUsage}MB (${audit.memory.utilizationPercent}%)`);

    // Get performance metrics summary
    audit.metrics = getPerformanceMetricsSummary();
    console.log('📊 Metrics Collected:', Object.keys(audit.metrics).length);

    // Get threshold violations
    audit.violations = getThresholdViolations();
    console.log('⚠️  Violations:', Object.keys(audit.violations).length);

    // Get performance trends
    audit.trends = getPerformanceTrends();
    console.log('📈 Trends:', Object.keys(audit.trends).length);

    // Generate recommendations
    audit.recommendations = generatePerformanceRecommendations(audit);
    console.log('💡 Recommendations:', audit.recommendations.length);

    if (audit.recommendations.length > 0) {
      console.group('💡 Performance Recommendations:');
      audit.recommendations.forEach((rec, index) => {
        console.log(`${index + 1}. ${rec.category}: ${rec.description}`);
      });
      console.groupEnd();
    }

  } finally {
    console.groupEnd();
  }

  return audit;
}

/**
 * Get performance metrics summary
 */
function getPerformanceMetricsSummary() {
  const summary = {};

  for (const [name, measurements] of performanceMetrics.measurements.entries()) {
    if (measurements.length === 0) continue;

    const durations = measurements.map(m => m.duration);
    const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
    const min = Math.min(...durations);
    const max = Math.max(...durations);

    summary[name] = {
      count: measurements.length,
      average: Math.round(avg * 100) / 100,
      min,
      max,
      latest: durations[durations.length - 1]
    };
  }

  return summary;
}

/**
 * Get threshold violations summary
 */
function getThresholdViolations() {
  const violations = {};

  for (const [name, violationList] of performanceMetrics.violations.entries()) {
    violations[name] = {
      count: violationList.length,
      latest: violationList[violationList.length - 1],
      frequency: violationList.length / (performanceMetrics.measurements.get(name)?.length || 1)
    };
  }

  return violations;
}

/**
 * Get performance trends
 */
function getPerformanceTrends() {
  const trends = {};

  for (const [name, trend] of performanceMetrics.trends.entries()) {
    trends[name] = {
      direction: trend.slope > 0 ? 'increasing' : trend.slope < 0 ? 'decreasing' : 'stable',
      slope: Math.round(trend.slope * 1000) / 1000,
      confidence: trend.confidence,
      dataPoints: trend.dataPoints
    };
  }

  return trends;
}

/**
 * Generate performance recommendations
 */
function generatePerformanceRecommendations(audit) {
  const recommendations = [];

  // Memory recommendations
  if (audit.memory.violations?.length > 0) {
    audit.memory.violations.forEach(violation => {
      if (violation.type === 'high_usage') {
        recommendations.push({
          category: 'Memory',
          priority: 'high',
          description: `Memory usage is ${violation.current}MB, exceeding threshold of ${violation.threshold}MB. Consider implementing object pooling or cleanup routines.`
        });
      }
      if (violation.type === 'potential_leak') {
        recommendations.push({
          category: 'Memory',
          priority: 'critical',
          description: `Potential memory leak detected. Memory increased by ${violation.increase}MB. Review event listeners and object references for cleanup.`
        });
      }
    });
  }

  // Performance trend recommendations
  for (const [name, trend] of Object.entries(audit.trends)) {
    if (trend.direction === 'increasing' && trend.confidence > 0.7) {
      recommendations.push({
        category: 'Performance Trend',
        priority: 'medium',
        description: `${name} performance is degrading over time (slope: ${trend.slope}). Consider optimization or refactoring.`
      });
    }
  }

  // Violation frequency recommendations
  for (const [name, violation] of Object.entries(audit.violations)) {
    if (violation.frequency > 0.5) {
      recommendations.push({
        category: 'Threshold Violation',
        priority: 'high',
        description: `${name} frequently exceeds performance thresholds (${Math.round(violation.frequency * 100)}% of operations). Optimization required.`
      });
    }
  }

  return recommendations.sort((a, b) => {
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });
}

/**
 * Helper functions
 */
function checkThresholdViolation(name, duration, context) {
  const threshold = getThresholdForMetric(name);
  if (threshold && duration > threshold) {
    recordThresholdViolation(name, { duration, threshold, context, timestamp: Date.now() });
  }
}

function recordThresholdViolation(name, violation) {
  if (!performanceMetrics.violations.has(name)) {
    performanceMetrics.violations.set(name, []);
  }
  performanceMetrics.violations.get(name).push(violation);
}

function updatePerformanceTrend(name, duration) {
  if (!performanceMetrics.trends.has(name)) {
    performanceMetrics.trends.set(name, {
      dataPoints: [],
      slope: 0,
      confidence: 0
    });
  }

  const trend = performanceMetrics.trends.get(name);
  trend.dataPoints.push({ timestamp: Date.now(), value: duration });

  // Keep only last 20 data points for trend calculation
  if (trend.dataPoints.length > 20) {
    trend.dataPoints = trend.dataPoints.slice(-20);
  }

  // Calculate linear regression for trend
  if (trend.dataPoints.length >= 5) {
    const regression = calculateLinearRegression(trend.dataPoints);
    trend.slope = regression.slope;
    trend.confidence = regression.confidence;
  }
}

function calculateLinearRegression(dataPoints) {
  const n = dataPoints.length;
  const x = dataPoints.map((_, i) => i);
  const y = dataPoints.map(p => p.value);

  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
  const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);

  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  // Calculate R-squared for confidence
  const yMean = sumY / n;
  const ssRes = y.reduce((sum, yi, i) => sum + Math.pow(yi - (slope * x[i] + intercept), 2), 0);
  const ssTot = y.reduce((sum, yi) => sum + Math.pow(yi - yMean, 2), 0);
  const rSquared = 1 - (ssRes / ssTot);

  return { slope, intercept, confidence: Math.max(0, rSquared) };
}

function getThresholdForMetric(name) {
  // Map metric names to thresholds
  const thresholdMap = {
    'component_card': PERFORMANCE_THRESHOLDS.CARD_RENDER,
    'component_table': PERFORMANCE_THRESHOLDS.TABLE_RENDER,
    'component_chart': PERFORMANCE_THRESHOLDS.CHART_RENDER,
    'component_form': PERFORMANCE_THRESHOLDS.FORM_RENDER,
    'api_filters': PERFORMANCE_THRESHOLDS.API_FILTERS,
    'api_stats': PERFORMANCE_THRESHOLDS.API_STATS,
    'api_charts': PERFORMANCE_THRESHOLDS.API_CHARTS,
    'api_trips': PERFORMANCE_THRESHOLDS.API_TRIPS,
    'dom_query': PERFORMANCE_THRESHOLDS.DOM_QUERY,
    'dom_update': PERFORMANCE_THRESHOLDS.DOM_UPDATE
  };

  // Find matching threshold by prefix
  for (const [prefix, threshold] of Object.entries(thresholdMap)) {
    if (name.startsWith(prefix)) {
      return threshold;
    }
  }

  return null;
}

function getResourceType(url) {
  if (url.includes('.js')) return 'script';
  if (url.includes('.css')) return 'stylesheet';
  if (url.includes('.json')) return 'json';
  if (url.includes('/api/')) return 'api';
  return 'other';
}

function startMemoryMonitoring() {
  if (typeof window === 'undefined') return;

  setInterval(() => {
    const memoryInfo = validateMemoryUsage();
    if (memoryInfo.supported) {
      // Suggest garbage collection if memory usage is high
      if (memoryInfo.utilizationPercent > 80) {
        console.warn('⚠️  High memory usage detected. Consider manual cleanup.');

        // Trigger GC if available (Chrome DevTools)
        if (window.gc && Date.now() - performanceMetrics.lastGCTime > 30000) {
          window.gc();
          performanceMetrics.lastGCTime = Date.now();
          console.log('🗑️  Manual garbage collection triggered');
        }
      }
    }
  }, 30000); // Check every 30 seconds
}

function generatePerformanceReport() {
  if (!isFeatureEnabled('ENABLE_PERFORMANCE_MONITORING')) return;

  const report = {
    timestamp: new Date().toISOString(),
    metrics: getPerformanceMetricsSummary(),
    violations: getThresholdViolations(),
    memory: validateMemoryUsage(),
    trends: getPerformanceTrends()
  };

  console.log('📊 Performance Report:', report);
  return report;
}

// Auto-initialize when module loads
if (typeof window !== 'undefined') {
  initializePerformanceValidator();
}