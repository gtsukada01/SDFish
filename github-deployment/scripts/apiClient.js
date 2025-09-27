/* global AbortController, setTimeout, clearTimeout */

/**
 * API Client Module
 * Centralizes all fetch logic with query-string building and error normalization
 */

import performanceMonitor from './performanceMonitor.js';
import { isFeatureEnabled } from './config/featureFlags.js';

const BASE_URL = '/api';

/**
 * Build query string from parameters object
 * @param {Object} params - Parameters to convert to query string
 * @returns {string} - Query string with ? prefix if params exist
 */
function buildQueryString(params = {}) {
  const filtered = Object.entries(params)
    .filter(([, value]) => value !== null && value !== undefined && value !== 'all')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`);

  return filtered.length > 0 ? '?' + filtered.join('&') : '';
}

// AbortController registry keyed by request intent (e.g., 'stats', 'daily-catches')
const abortControllers = new Map();

/**
 * Cancel pending requests by key or all requests
 * @param {string|null} key - Optional cancellation key
 */
export function cancelPendingRequests(key = null) {
  if (key) {
    const controller = abortControllers.get(key);
    if (controller) {
      controller.abort();
      abortControllers.delete(key);
    }
    return;
  }

  abortControllers.forEach((controller) => controller.abort());
  abortControllers.clear();
}

/**
 * Standardized fetch wrapper with error handling and retry logic
 * @param {string} url - URL to fetch
 * @param {Object} options - Behavioural options (cancelKey, timeout, etc.)
 * @returns {Promise<Object>} - Parsed JSON response
 */
async function fetchWithErrorHandling(url, options = {}) {
  const {
    fetchOptions = {},
    cancelKey = null,
    cancelPrevious = true,
    timeout = 10000,
    retries = 3,
    retryDelay = 1000,
    backoffMultiplier = 2
  } = options;

  // Start performance timer if enabled
  const endTimer = isFeatureEnabled('ENABLE_PERFORMANCE_MONITORING')
    ? performanceMonitor.startTimer(`api:${url.replace(BASE_URL, '')}`)
    : () => {};

  const controller = new AbortController();

  if (cancelKey) {
    if (cancelPrevious) {
      cancelPendingRequests(cancelKey);
    }
    abortControllers.set(cancelKey, controller);
  }

  let didTimeout = false;
  const timeoutId =
    typeof timeout === 'number'
      ? setTimeout(() => {
          didTimeout = true;
          controller.abort();
        }, timeout)
      : null;

  const clearController = () => {
    if (cancelKey) {
      const tracked = abortControllers.get(cancelKey);
      if (tracked === controller) {
        abortControllers.delete(cancelKey);
      }
    }
  };

  // Retry logic with exponential backoff
  let lastError = null;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
      });

      if (timeoutId) clearTimeout(timeoutId);

      if (!response.ok) {
        const error = new Error(`API Error: ${response.status} ${response.statusText}`);
        error.status = response.status;

        // Don't retry client errors (4xx)
        if (response.status >= 400 && response.status < 500) {
          throw error;
        }

        // Retry server errors (5xx) and network issues
        if (attempt === retries) {
          throw error;
        }

        lastError = error;
        await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(backoffMultiplier, attempt)));
        continue;
      }

      const data = await response.json();

      // Record performance metric
      const duration = endTimer();
      if (isFeatureEnabled('ENABLE_PERFORMANCE_MONITORING') && duration > 500) {
        performanceMonitor.checkThreshold(`api:${url.replace(BASE_URL, '')}`, duration, 500);
      }

      return data;
    } catch (error) {
      if (timeoutId) clearTimeout(timeoutId);

      if (error.name === 'AbortError') {
        endTimer();

        if (didTimeout) {
          const timeoutError = new Error('Request timeout: API took too long to respond');
          timeoutError.name = 'TimeoutError';
          throw timeoutError;
        }

        const cancelError = new Error('Request cancelled');
        cancelError.name = 'AbortError';
        cancelError.isCanceled = true;
        throw cancelError;
      }

      // Don't retry on abort or client errors
      if (error.name === 'AbortError' || (error.status >= 400 && error.status < 500)) {
        endTimer();
        const apiError = new Error(error.message || 'Network error occurred');
        apiError.status = error.status || 'unknown';
        apiError.timestamp = new Date().toISOString();
        throw apiError;
      }

      // Store error for potential retry
      lastError = error;

      // If this is the last attempt, throw the error
      if (attempt === retries) {
        endTimer();
        const apiError = new Error(error.message || 'Network error occurred');
        apiError.status = error.status || 'unknown';
        apiError.timestamp = new Date().toISOString();
        apiError.attempts = retries + 1;
        throw apiError;
      }

      // Wait before retry with exponential backoff
      await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(backoffMultiplier, attempt)));
    }
  }

  // This should never be reached, but just in case
  clearController();
  endTimer();
  throw lastError || new Error('Unknown error occurred during retries');
}

/**
 * Fetch filter options (landings, species, durations, boats)
 * @param {string|null} landingId - Optional landing ID to filter by
 * @param {boolean} cancelPrevious - Whether to cancel previous requests
 * @returns {Promise<Object>} - Filter data
 */
export async function fetchFilters(landingId = null, options = {}) {
  const params = landingId ? { landing: landingId } : {};
  const queryString = buildQueryString(params);
  return fetchWithErrorHandling(`${BASE_URL}/filters${queryString}`, {
    cancelKey: options.cancelKey ?? 'filters',
    cancelPrevious: options.cancelPrevious ?? true,
    timeout: options.timeout,
    fetchOptions: options.fetchOptions,
  });
}

/**
 * Fetch statistics for date range
 * @param {string} startDate - Start date (YYYY-MM-DD)
 * @param {string} endDate - End date (YYYY-MM-DD)
 * @param {Object} filters - Additional filters
 * @param {boolean} cancelPrevious - Whether to cancel previous requests
 * @returns {Promise<Object>} - Statistics data
 */
export async function fetchStatsForDateRange(startDate, endDate, filters = {}, options = {}) {
  const queryString = buildQueryString(filters);

  if (startDate && endDate) {
    return fetchWithErrorHandling(
      `${BASE_URL}/stats/date-range/${startDate}/${endDate}${queryString}`,
      {
        cancelKey: options.cancelKey ?? 'stats',
        cancelPrevious: options.cancelPrevious ?? true,
        timeout: options.timeout,
        fetchOptions: options.fetchOptions,
      }
    );
  } else {
    return fetchWithErrorHandling(`${BASE_URL}/stats/last-30-days${queryString}`, {
      cancelKey: options.cancelKey ?? 'stats',
      cancelPrevious: options.cancelPrevious ?? true,
      timeout: options.timeout,
      fetchOptions: options.fetchOptions,
    });
  }
}

/**
 * Fetch daily catches data
 * @param {number} days - Number of days to fetch
 * @param {Object} filters - Additional filters
 * @param {boolean} cancelPrevious - Whether to cancel previous requests
 * @returns {Promise<Object>} - Daily catches chart data
 */
export async function fetchDailyCatches(days, filters = {}, options = {}) {
  const queryString = buildQueryString(filters);
  return fetchWithErrorHandling(`${BASE_URL}/daily-catches/${days}${queryString}`, {
    cancelKey: options.cancelKey ?? 'daily-catches',
    cancelPrevious: options.cancelPrevious ?? true,
    timeout: options.timeout,
    fetchOptions: options.fetchOptions,
  });
}

/**
 * Fetch top boats data
 * @param {number} limit - Maximum number of boats to return
 * @param {Object} filters - Additional filters
 * @param {boolean} cancelPrevious - Whether to cancel previous requests
 * @returns {Promise<Object>} - Top boats chart data
 */
export async function fetchTopBoats(limit = 10, filters = {}, options = {}) {
  const queryString = buildQueryString(filters);
  return fetchWithErrorHandling(`${BASE_URL}/top-boats/${limit}${queryString}`, {
    cancelKey: options.cancelKey ?? 'top-boats',
    cancelPrevious: options.cancelPrevious ?? true,
    timeout: options.timeout,
    fetchOptions: options.fetchOptions,
  });
}

/**
 * Fetch recent trips
 * @param {number} limit - Maximum number of trips to return
 * @param {Object} filters - Additional filters
 * @param {boolean} cancelPrevious - Whether to cancel previous requests
 * @returns {Promise<Array>} - Recent trips data
 */
export async function fetchRecentTrips(limit = 10, filters = {}, options = {}) {
  const queryString = buildQueryString(filters);
  return fetchWithErrorHandling(`${BASE_URL}/recent-trips/${limit}${queryString}`, {
    cancelKey: options.cancelKey ?? 'recent-trips',
    cancelPrevious: options.cancelPrevious ?? true,
    timeout: options.timeout,
    fetchOptions: options.fetchOptions,
  });
}

/**
 * Fetch moon phase aggregated fishing data
 * @param {Object} options - Request options
 * @param {string} options.cancelKey - Request cancellation key
 * @param {boolean} options.cancelPrevious - Whether to cancel previous requests
 * @param {number} options.timeout - Request timeout in milliseconds
 * @param {Object} options.fetchOptions - Additional fetch options
 * @returns {Promise<Object>} - Moon phase chart data
 */
export async function fetchMoonPhaseData(options = {}) {
  return fetchWithErrorHandling(`${BASE_URL}/moon-phase-data`, {
    cancelKey: options.cancelKey ?? 'moon-phase-data',
    cancelPrevious: options.cancelPrevious ?? true,
    timeout: options.timeout,
    fetchOptions: options.fetchOptions,
  });
}

/**
 * Health check endpoint
 * @returns {Promise<Object>} - API health status
 */
export async function checkHealth(options = {}) {
  return fetchWithErrorHandling(`${BASE_URL}/health`, {
    cancelKey: options.cancelKey ?? null,
    cancelPrevious: options.cancelPrevious ?? false,
    timeout: options.timeout,
    fetchOptions: options.fetchOptions,
  });
}

// Export utility for creating standardized error responses
export function createErrorResponse(error) {
  return {
    status: 'error',
    message: error.message || 'An error occurred',
    timestamp: new Date().toISOString(),
    data: null,
  };
}

// Export utility for creating standardized success responses
export function createSuccessResponse(data) {
  return {
    status: 'success',
    data: data,
    timestamp: new Date().toISOString(),
  };
}
