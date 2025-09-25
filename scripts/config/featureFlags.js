/**
 * Feature Flags Configuration
 * Controls gradual adoption of new state management and API client
 */

const featureFlags = {
  // Enable new centralized API client
  USE_NEW_API_CLIENT: true,

  // Enable new state management system
  USE_NEW_STATE: true,

  // Enable performance monitoring
  ENABLE_PERFORMANCE_MONITORING: true,

  // Enable detailed error logging
  ENABLE_DETAILED_ERROR_LOGGING: true,

  // Enable fetch request abort controllers
  ENABLE_FETCH_ABORT: true,

  // Enable state persistence
  ENABLE_STATE_PERSISTENCE: true,

  // Maximum API timeout in milliseconds
  API_TIMEOUT_MS: 10000,

  // Enable development mode features
  IS_DEVELOPMENT: window.location.hostname === 'localhost',
};

/**
 * Check if a feature is enabled
 * @param {string} flagName - Feature flag name
 * @returns {boolean} - Whether feature is enabled
 */
export function isFeatureEnabled(flagName) {
  return featureFlags[flagName] === true;
}

/**
 * Get feature flag value
 * @param {string} flagName - Feature flag name
 * @param {*} defaultValue - Default value if flag not found
 * @returns {*} - Flag value
 */
export function getFeatureFlag(flagName, defaultValue = false) {
  return featureFlags[flagName] !== undefined ? featureFlags[flagName] : defaultValue;
}

/**
 * Toggle feature flag (development only)
 * @param {string} flagName - Feature flag name
 * @param {boolean} value - New value
 */
export function setFeatureFlag(flagName, value) {
  if (featureFlags.IS_DEVELOPMENT) {
    featureFlags[flagName] = value;
    // Feature flag change is silent to avoid console noise
    // Value can be inspected via window.__featureFlags in development
  }
}

// Export flags object for direct access
export default featureFlags;

// Expose to window for development debugging
if (featureFlags.IS_DEVELOPMENT && typeof window !== 'undefined') {
  window.__featureFlags = {
    flags: featureFlags,
    toggle: setFeatureFlag,
    check: isFeatureEnabled,
    get: getFeatureFlag,
  };
}
