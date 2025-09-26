/**
 * Production Monitor - Comprehensive Production Monitoring and Logging
 * Provides real-time monitoring, alerting, and operational insights
 */

import { isFeatureEnabled } from './config/featureFlags.js';
import { logError, getErrorStats, ERROR_CATEGORIES, ERROR_LEVELS } from './errorBoundary.js';
import { validateMemoryUsage, runPerformanceAudit } from './performanceValidator.js';
import { rollbackManager } from './rollbackManager.js';

/**
 * Monitoring state
 */
const monitorState = {
  metrics: new Map(),
  alerts: new Map(),
  healthChecks: new Map(),
  operationalData: {
    uptime: Date.now(),
    sessionId: generateSessionId(),
    deploymentVersion: '4.0.0-hardened',
    environment: 'production'
  },
  monitoring: {
    active: false,
    interval: null,
    reportingInterval: null,
    lastReport: null
  }
};

/**
 * Alert severity levels
 */
export const ALERT_LEVELS = {
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical'
};

/**
 * Metric types
 */
export const METRIC_TYPES = {
  COUNTER: 'counter',
  GAUGE: 'gauge',
  HISTOGRAM: 'histogram',
  TIMER: 'timer'
};

/**
 * Health check status
 */
export const HEALTH_STATUS = {
  HEALTHY: 'healthy',
  DEGRADED: 'degraded',
  UNHEALTHY: 'unhealthy',
  UNKNOWN: 'unknown'
};

/**
 * Initialize production monitoring
 */
export function initializeProductionMonitor(options = {}) {
  const {
    enableRealTimeMonitoring = true,
    reportingIntervalMs = 300000, // 5 minutes
    monitoringIntervalMs = 30000, // 30 seconds
    enableAlerts = true,
    enableHealthChecks = true
  } = options;

  if (!isFeatureEnabled('ENABLE_PERFORMANCE_MONITORING')) {
    console.log('📊 Production monitoring disabled via feature flag');
    return;
  }

  console.log('📊 Initializing Production Monitor...');

  // Initialize core metrics
  initializeCoreMetrics();

  // Register health checks
  if (enableHealthChecks) {
    registerHealthChecks();
  }

  // Start monitoring intervals
  if (enableRealTimeMonitoring) {
    startMonitoring(monitoringIntervalMs);
  }

  // Start reporting interval
  if (reportingIntervalMs > 0) {
    startReporting(reportingIntervalMs);
  }

  // Register event listeners
  registerEventListeners();

  monitorState.monitoring.active = true;

  console.log('✅ Production Monitor initialized');
  recordMetric('system.initialization', 1, METRIC_TYPES.COUNTER);
}

/**
 * Record metric value
 */
export function recordMetric(name, value, type = METRIC_TYPES.GAUGE, tags = {}) {
  const timestamp = Date.now();
  const metric = {
    name,
    value,
    type,
    timestamp,
    tags,
    sessionId: monitorState.operationalData.sessionId
  };

  // Store metric
  if (!monitorState.metrics.has(name)) {
    monitorState.metrics.set(name, []);
  }

  const metrics = monitorState.metrics.get(name);
  metrics.push(metric);

  // Maintain metric history (keep last 100 points per metric)
  if (metrics.length > 100) {
    metrics.splice(0, metrics.length - 100);
  }

  // Check for alert conditions
  checkMetricAlerts(name, value, metric);

  // Log significant metrics
  if (type === METRIC_TYPES.COUNTER || shouldLogMetric(name, value)) {
    console.log(`📈 Metric: ${name} = ${value} (${type})`);
  }
}

/**
 * Create alert condition
 */
export function createAlert(name, condition, severity = ALERT_LEVELS.WARNING, options = {}) {
  const alert = {
    name,
    condition,
    severity,
    enabled: true,
    fired: false,
    lastFired: null,
    fireCount: 0,
    cooldownMs: options.cooldownMs || 300000, // 5 minutes default
    description: options.description || `Alert condition for ${name}`,
    actions: options.actions || []
  };

  monitorState.alerts.set(name, alert);
  console.log(`🔔 Alert registered: ${name} (${severity})`);

  return alert;
}

/**
 * Register health check
 */
export function registerHealthCheck(name, checkFunction, options = {}) {
  const healthCheck = {
    name,
    checkFunction,
    enabled: true,
    lastRun: null,
    lastResult: null,
    status: HEALTH_STATUS.UNKNOWN,
    intervalMs: options.intervalMs || 60000, // 1 minute default
    timeoutMs: options.timeoutMs || 5000, // 5 seconds default
    retries: options.retries || 2,
    description: options.description || `Health check for ${name}`
  };

  monitorState.healthChecks.set(name, healthCheck);
  console.log(`🏥 Health check registered: ${name}`);

  return healthCheck;
}

/**
 * Get current system metrics
 */
export function getSystemMetrics() {
  const now = Date.now();
  const uptime = now - monitorState.operationalData.uptime;

  return {
    timestamp: now,
    uptime: Math.round(uptime / 1000), // in seconds
    sessionId: monitorState.operationalData.sessionId,
    version: monitorState.operationalData.deploymentVersion,
    environment: monitorState.operationalData.environment,

    // Performance metrics
    memory: validateMemoryUsage(),

    // Error metrics
    errors: getErrorStats(),

    // Custom metrics summary
    customMetrics: getMetricsSummary(),

    // Health status
    health: getHealthStatus(),

    // Alert status
    alerts: getActiveAlerts(),

    // Browser info
    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
    url: typeof window !== 'undefined' ? window.location.href : 'unknown',

    // Rollback status
    rollback: {
      emergencyMode: rollbackManager.isEmergencyMode(),
      snapshotCount: rollbackManager.getSnapshots().length,
      lastRollback: rollbackManager.getHistory().slice(-1)[0] || null
    }
  };
}

/**
 * Generate operational report
 */
export async function generateOperationalReport() {
  console.group('📊 Operational Report');

  const report = {
    timestamp: new Date().toISOString(),
    reportType: 'operational_summary',
    systemMetrics: getSystemMetrics(),
    performanceAudit: null,
    recommendations: [],
    alertSummary: getAlertSummary(),
    healthSummary: getHealthSummary(),
    incidentLog: getRecentIncidents()
  };

  try {
    // Include performance audit if available
    if (isFeatureEnabled('ENABLE_PERFORMANCE_MONITORING')) {
      report.performanceAudit = await runPerformanceAudit();
    }

    // Generate operational recommendations
    report.recommendations = generateOperationalRecommendations(report);

    // Log report summary
    console.log('⏱️  System Uptime:', formatUptime(report.systemMetrics.uptime));
    console.log('💾 Memory Usage:', `${report.systemMetrics.memory.currentUsage}MB`);
    console.log('🚨 Active Alerts:', report.alertSummary.active);
    console.log('🏥 Health Status:', report.healthSummary.overall);
    console.log('⚠️  Error Count (1h):', report.systemMetrics.errors.lastHour);

    if (report.recommendations.length > 0) {
      console.group('💡 Operational Recommendations:');
      report.recommendations.forEach((rec, index) => {
        console.log(`${index + 1}. [${rec.priority}] ${rec.category}: ${rec.description}`);
      });
      console.groupEnd();
    }

  } catch (error) {
    logError(`Failed to generate operational report: ${error.message}`, {
      category: ERROR_CATEGORIES.SYSTEM,
      level: ERROR_LEVELS.HIGH,
      context: 'operational_reporting'
    });
  } finally {
    console.groupEnd();
  }

  monitorState.monitoring.lastReport = report;
  return report;
}

/**
 * Initialize core metrics
 */
function initializeCoreMetrics() {
  // System metrics
  createAlert('memory_usage_high', (value) => value > 80, ALERT_LEVELS.WARNING, {
    description: 'Memory usage exceeds 80MB',
    cooldownMs: 60000
  });

  createAlert('memory_leak_detected', (value) => value > 20, ALERT_LEVELS.ERROR, {
    description: 'Memory leak detected (increase > 20MB)',
    cooldownMs: 300000
  });

  // Error rate alerts
  createAlert('error_rate_high', (value) => value > 10, ALERT_LEVELS.WARNING, {
    description: 'Error rate exceeds 10 errors per hour',
    cooldownMs: 180000
  });

  createAlert('critical_errors', (value) => value > 0, ALERT_LEVELS.CRITICAL, {
    description: 'Critical errors detected',
    cooldownMs: 60000
  });

  // Performance alerts
  createAlert('api_response_slow', (value) => value > 2000, ALERT_LEVELS.WARNING, {
    description: 'API responses slower than 2 seconds',
    cooldownMs: 120000
  });

  createAlert('component_render_slow', (value) => value > 500, ALERT_LEVELS.WARNING, {
    description: 'Component rendering slower than 500ms',
    cooldownMs: 180000
  });
}

/**
 * Register health checks
 */
function registerHealthChecks() {
  // API health check
  registerHealthCheck('api_connectivity', async () => {
    try {
      const response = await fetch('/api/health', {
        method: 'GET',
        timeout: 3000
      });
      return {
        status: response.ok ? HEALTH_STATUS.HEALTHY : HEALTH_STATUS.UNHEALTHY,
        details: { statusCode: response.status }
      };
    } catch (error) {
      return {
        status: HEALTH_STATUS.UNHEALTHY,
        details: { error: error.message }
      };
    }
  }, { intervalMs: 30000, description: 'API server connectivity' });

  // DOM health check
  registerHealthCheck('dom_integrity', async () => {
    try {
      const requiredElements = ['#filtersMount', '#statsGridContainer', '#chartsContainer'];
      const missing = requiredElements.filter(sel => !document.querySelector(sel));

      return {
        status: missing.length === 0 ? HEALTH_STATUS.HEALTHY : HEALTH_STATUS.DEGRADED,
        details: { missingElements: missing }
      };
    } catch (error) {
      return {
        status: HEALTH_STATUS.UNHEALTHY,
        details: { error: error.message }
      };
    }
  }, { intervalMs: 120000, description: 'DOM structure integrity' });

  // Memory health check
  registerHealthCheck('memory_health', async () => {
    const memory = validateMemoryUsage();

    let status = HEALTH_STATUS.HEALTHY;
    if (memory.utilizationPercent > 90) {
      status = HEALTH_STATUS.UNHEALTHY;
    } else if (memory.utilizationPercent > 70) {
      status = HEALTH_STATUS.DEGRADED;
    }

    return {
      status,
      details: {
        usage: memory.currentUsage,
        utilizationPercent: memory.utilizationPercent
      }
    };
  }, { intervalMs: 60000, description: 'Memory utilization health' });

  // Feature flags health check
  registerHealthCheck('feature_flags', async () => {
    try {
      const criticalFlags = ['USE_NEW_API_CLIENT', 'ENABLE_PERFORMANCE_MONITORING'];
      const flagStatus = criticalFlags.map(flag => ({
        flag,
        enabled: isFeatureEnabled(flag)
      }));

      return {
        status: HEALTH_STATUS.HEALTHY,
        details: { flags: flagStatus }
      };
    } catch (error) {
      return {
        status: HEALTH_STATUS.UNHEALTHY,
        details: { error: error.message }
      };
    }
  }, { intervalMs: 300000, description: 'Feature flags status' });
}

/**
 * Start monitoring loop
 */
function startMonitoring(intervalMs) {
  if (monitorState.monitoring.interval) {
    clearInterval(monitorState.monitoring.interval);
  }

  monitorState.monitoring.interval = setInterval(async () => {
    try {
      // Record system metrics
      const memory = validateMemoryUsage();
      if (memory.supported) {
        recordMetric('system.memory.usage', memory.currentUsage, METRIC_TYPES.GAUGE);
        recordMetric('system.memory.utilization', memory.utilizationPercent, METRIC_TYPES.GAUGE);

        if (memory.increase > 0) {
          recordMetric('system.memory.increase', memory.increase, METRIC_TYPES.GAUGE);
        }
      }

      // Record error metrics
      const errors = getErrorStats();
      recordMetric('system.errors.total', errors.total, METRIC_TYPES.GAUGE);
      recordMetric('system.errors.hourly', errors.lastHour, METRIC_TYPES.GAUGE);

      // Run health checks
      await runHealthChecks();

      // Check for emergency conditions
      checkEmergencyConditions();

    } catch (error) {
      logError(`Monitoring loop error: ${error.message}`, {
        category: ERROR_CATEGORIES.SYSTEM,
        level: ERROR_LEVELS.MEDIUM,
        context: 'monitoring_loop'
      });
    }
  }, intervalMs);
}

/**
 * Start reporting loop
 */
function startReporting(intervalMs) {
  if (monitorState.monitoring.reportingInterval) {
    clearInterval(monitorState.monitoring.reportingInterval);
  }

  monitorState.monitoring.reportingInterval = setInterval(() => {
    generateOperationalReport().catch(error => {
      console.error('Failed to generate operational report:', error);
    });
  }, intervalMs);
}

/**
 * Run all health checks
 */
async function runHealthChecks() {
  for (const [name, healthCheck] of monitorState.healthChecks.entries()) {
    if (!healthCheck.enabled) continue;

    const timeSinceLastRun = Date.now() - (healthCheck.lastRun || 0);
    if (timeSinceLastRun < healthCheck.intervalMs) continue;

    try {
      const startTime = Date.now();
      const result = await Promise.race([
        healthCheck.checkFunction(),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Health check timeout')), healthCheck.timeoutMs)
        )
      ]);

      healthCheck.lastRun = Date.now();
      healthCheck.lastResult = result;
      healthCheck.status = result.status;

      const duration = Date.now() - startTime;
      recordMetric(`health.${name}.duration`, duration, METRIC_TYPES.TIMER);
      recordMetric(`health.${name}.status`, result.status === HEALTH_STATUS.HEALTHY ? 1 : 0, METRIC_TYPES.GAUGE);

      if (result.status !== HEALTH_STATUS.HEALTHY) {
        logError(`Health check failed: ${name}`, {
          category: ERROR_CATEGORIES.SYSTEM,
          level: result.status === HEALTH_STATUS.UNHEALTHY ? ERROR_LEVELS.HIGH : ERROR_LEVELS.MEDIUM,
          context: 'health_check',
          metadata: { healthCheck: name, status: result.status, details: result.details }
        });
      }

    } catch (error) {
      healthCheck.lastRun = Date.now();
      healthCheck.status = HEALTH_STATUS.UNHEALTHY;
      healthCheck.lastResult = {
        status: HEALTH_STATUS.UNHEALTHY,
        details: { error: error.message }
      };

      logError(`Health check error: ${name} - ${error.message}`, {
        category: ERROR_CATEGORIES.SYSTEM,
        level: ERROR_LEVELS.HIGH,
        context: 'health_check_error',
        metadata: { healthCheck: name }
      });
    }
  }
}

/**
 * Utility functions
 */
function checkMetricAlerts(metricName, value, metric) {
  for (const [alertName, alert] of monitorState.alerts.entries()) {
    if (!alert.enabled) continue;

    const shouldFire = alert.condition(value, metric);
    const cooldownExpired = !alert.lastFired ||
      (Date.now() - alert.lastFired) > alert.cooldownMs;

    if (shouldFire && cooldownExpired) {
      fireAlert(alert, { metric: metricName, value, details: metric });
    }
  }
}

function fireAlert(alert, context) {
  alert.fired = true;
  alert.lastFired = Date.now();
  alert.fireCount++;

  const alertMessage = `🚨 ALERT [${alert.severity.toUpperCase()}]: ${alert.description}`;

  console.warn(alertMessage);
  console.log('Alert Context:', context);

  // Log alert
  logError(`Alert fired: ${alert.name}`, {
    category: ERROR_CATEGORIES.SYSTEM,
    level: alert.severity === ALERT_LEVELS.CRITICAL ? ERROR_LEVELS.CRITICAL : ERROR_LEVELS.HIGH,
    context: 'alert_fired',
    metadata: { alert: alert.name, severity: alert.severity, context }
  });

  // Execute alert actions
  if (alert.actions && alert.actions.length > 0) {
    alert.actions.forEach(action => {
      try {
        action(context, alert);
      } catch (error) {
        console.error(`Alert action failed for ${alert.name}:`, error);
      }
    });
  }

  // Create snapshot on critical alerts
  if (alert.severity === ALERT_LEVELS.CRITICAL) {
    rollbackManager.createSnapshot(`critical_alert_${alert.name}_${Date.now()}`);
  }
}

function checkEmergencyConditions() {
  const memory = validateMemoryUsage();
  const errors = getErrorStats();
  const activeAlerts = getActiveAlerts();

  // Check for emergency rollback conditions
  const criticalAlerts = activeAlerts.filter(a => a.severity === ALERT_LEVELS.CRITICAL);

  if (criticalAlerts.length > 2) {
    console.warn('🚨 Multiple critical alerts detected, considering emergency rollback');
    rollbackManager.createSnapshot(`emergency_${Date.now()}`);
  }

  if (memory.supported && memory.utilizationPercent > 95) {
    console.warn('🚨 Critical memory usage detected');
    rollbackManager.triggerEmergency('degraded', { trigger: 'critical_memory_usage' });
  }

  if (errors.lastHour > 50) {
    console.warn('🚨 High error rate detected');
    rollbackManager.createSnapshot(`high_errors_${Date.now()}`);
  }
}

function getMetricsSummary() {
  const summary = {};

  for (const [name, metrics] of monitorState.metrics.entries()) {
    if (metrics.length === 0) continue;

    const latest = metrics[metrics.length - 1];
    const values = metrics.map(m => m.value);

    summary[name] = {
      current: latest.value,
      type: latest.type,
      count: metrics.length,
      average: values.reduce((a, b) => a + b, 0) / values.length,
      min: Math.min(...values),
      max: Math.max(...values)
    };
  }

  return summary;
}

function getHealthStatus() {
  const statuses = Array.from(monitorState.healthChecks.values())
    .map(hc => hc.status)
    .filter(status => status !== HEALTH_STATUS.UNKNOWN);

  if (statuses.length === 0) return HEALTH_STATUS.UNKNOWN;
  if (statuses.some(s => s === HEALTH_STATUS.UNHEALTHY)) return HEALTH_STATUS.UNHEALTHY;
  if (statuses.some(s => s === HEALTH_STATUS.DEGRADED)) return HEALTH_STATUS.DEGRADED;
  return HEALTH_STATUS.HEALTHY;
}

function getActiveAlerts() {
  return Array.from(monitorState.alerts.values())
    .filter(alert => alert.fired && alert.enabled);
}

function getAlertSummary() {
  const alerts = Array.from(monitorState.alerts.values());
  return {
    total: alerts.length,
    active: alerts.filter(a => a.fired && a.enabled).length,
    bySeverity: alerts.reduce((acc, alert) => {
      acc[alert.severity] = (acc[alert.severity] || 0) + (alert.fired ? 1 : 0);
      return acc;
    }, {})
  };
}

function getHealthSummary() {
  const checks = Array.from(monitorState.healthChecks.values());
  return {
    total: checks.length,
    overall: getHealthStatus(),
    byStatus: checks.reduce((acc, check) => {
      acc[check.status] = (acc[check.status] || 0) + 1;
      return acc;
    }, {})
  };
}

function getRecentIncidents() {
  const recentErrors = getErrorStats();
  const recentAlerts = getActiveAlerts().slice(-10);
  const recentRollbacks = rollbackManager.getHistory().slice(-5);

  return {
    errors: recentErrors,
    alerts: recentAlerts.map(a => ({
      name: a.name,
      severity: a.severity,
      lastFired: a.lastFired,
      fireCount: a.fireCount
    })),
    rollbacks: recentRollbacks
  };
}

function generateOperationalRecommendations(report) {
  const recommendations = [];

  // Memory recommendations
  if (report.systemMetrics.memory.currentUsage > 40) {
    recommendations.push({
      category: 'Memory Management',
      priority: 'medium',
      description: `Consider memory optimization. Current usage: ${report.systemMetrics.memory.currentUsage}MB`
    });
  }

  // Error rate recommendations
  if (report.systemMetrics.errors.lastHour > 5) {
    recommendations.push({
      category: 'Error Management',
      priority: 'high',
      description: `High error rate detected: ${report.systemMetrics.errors.lastHour} errors in last hour`
    });
  }

  // Health check recommendations
  const unhealthyChecks = Object.entries(report.healthSummary.byStatus)
    .filter(([status]) => status === HEALTH_STATUS.UNHEALTHY || status === HEALTH_STATUS.DEGRADED);

  unhealthyChecks.forEach(([status, count]) => {
    recommendations.push({
      category: 'Health Monitoring',
      priority: status === HEALTH_STATUS.UNHEALTHY ? 'high' : 'medium',
      description: `${count} health checks are ${status}. Review system components.`
    });
  });

  return recommendations;
}

function registerEventListeners() {
  if (typeof window === 'undefined') return;

  // Track user interactions
  document.addEventListener('click', (event) => {
    recordMetric('user.clicks', 1, METRIC_TYPES.COUNTER, {
      element: event.target.tagName,
      id: event.target.id
    });
  });

  // Track page visibility changes
  document.addEventListener('visibilitychange', () => {
    recordMetric('user.visibility_change', document.hidden ? 0 : 1, METRIC_TYPES.GAUGE);
  });

  // Track page load performance
  window.addEventListener('load', () => {
    if (window.performance) {
      const navigation = window.performance.getEntriesByType('navigation')[0];
      if (navigation) {
        recordMetric('page.load_time', navigation.loadEventEnd - navigation.navigationStart, METRIC_TYPES.TIMER);
        recordMetric('page.dom_content_loaded', navigation.domContentLoadedEventEnd - navigation.navigationStart, METRIC_TYPES.TIMER);
      }
    }
  });
}

function shouldLogMetric(name, value) {
  // Log certain critical metrics always
  const criticalMetrics = [
    'system.memory.usage',
    'system.errors.total',
    'system.errors.hourly'
  ];

  return criticalMetrics.some(metric => name.startsWith(metric));
}

function formatUptime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  return `${hours}h ${minutes}m ${secs}s`;
}

function generateSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Public API
 */
export const productionMonitor = {
  initialize: initializeProductionMonitor,
  recordMetric,
  createAlert,
  registerHealthCheck,
  getSystemMetrics,
  generateReport: generateOperationalReport,
  isActive: () => monitorState.monitoring.active,
  stop: () => {
    if (monitorState.monitoring.interval) {
      clearInterval(monitorState.monitoring.interval);
    }
    if (monitorState.monitoring.reportingInterval) {
      clearInterval(monitorState.monitoring.reportingInterval);
    }
    monitorState.monitoring.active = false;
    console.log('📊 Production monitoring stopped');
  }
};

// Auto-initialize when module loads
if (typeof window !== 'undefined') {
  // Initialize with delay to allow other modules to load
  setTimeout(() => {
    initializeProductionMonitor();
  }, 2000);
}