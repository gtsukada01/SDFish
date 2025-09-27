/**
 * Feature Flags Configuration (Production)
 * Mirrors dev flags so prod bundle honors the same toggles.
 */

const featureFlags = {
  USE_NEW_API_CLIENT: true,
  USE_NEW_STATE: true,
  ENABLE_PERFORMANCE_MONITORING: true,
  ENABLE_DETAILED_ERROR_LOGGING: true,
  ENABLE_FETCH_ABORT: true,
  ENABLE_STATE_PERSISTENCE: true,
  API_TIMEOUT_MS: 10000,
  IS_DEVELOPMENT: typeof window !== 'undefined' && window.location.hostname === 'localhost',
};

export function isFeatureEnabled(flagName) {
  return featureFlags[flagName] === true;
}

export function getFeatureFlag(flagName, defaultValue = false) {
  return featureFlags[flagName] !== undefined ? featureFlags[flagName] : defaultValue;
}

export function setFeatureFlag(flagName, value) {
  if (featureFlags.IS_DEVELOPMENT) {
    featureFlags[flagName] = value;
  }
}

export default featureFlags;

if (featureFlags.IS_DEVELOPMENT && typeof window !== 'undefined') {
  window.__featureFlags = {
    flags: featureFlags,
    toggle: setFeatureFlag,
    check: isFeatureEnabled,
    get: getFeatureFlag,
  };
}
