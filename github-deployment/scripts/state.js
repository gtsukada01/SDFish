/**
 * State Management Module
 * Manages application state with event emission for subscribers
 */

class StateManager {
  constructor() {
    this.state = {
      selectedLanding: null,
      filters: {
        startDate: null,
        endDate: null,
        species: 'all',
        duration: 'all',
        boat: 'all',
      },
      starredLandings: [],
      landingsData: {},
      landingIdToNameMap: {},
      boatNameToIdMap: {},
      charts: {
        dailyCatchesData: null,
        topBoatsData: null,
      },
      ui: {
        isLoading: false,
        error: null,
      },
    };

    this.subscribers = new Map();
    this.initializeFromStorage();
  }

  /**
   * Initialize state from localStorage
   */
  initializeFromStorage() {
    try {
      const stored = localStorage.getItem('starredLandings');
      if (stored) {
        this.state.starredLandings = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load starred landings from storage:', error);
    }

    // Set default date range (January 1, 2025 to today)
    const today = new Date();
    const startOfYear = new Date('2025-01-01');
    this.state.filters.startDate = startOfYear.toISOString().split('T')[0];
    this.state.filters.endDate = today.toISOString().split('T')[0];
  }

  /**
   * Get current state or specific property
   * @param {string} path - Dot notation path to property (e.g., 'filters.species')
   * @returns {*} - State value
   */
  get(path = null) {
    if (!path) return { ...this.state };

    return path.split('.').reduce((obj, key) => obj?.[key], this.state);
  }

  /**
   * Set state property and notify subscribers
   * @param {string} path - Dot notation path to property
   * @param {*} value - New value
   */
  set(path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    const target = keys.reduce((obj, key) => {
      if (!obj[key]) obj[key] = {};
      return obj[key];
    }, this.state);

    const oldValue = target[lastKey];
    target[lastKey] = value;

    // Notify subscribers
    this.emit(path, { path, value, oldValue });

    // Special handling for starred landings
    if (path === 'starredLandings' || path.startsWith('starredLandings')) {
      this.persistStarredLandings();
    }
  }

  /**
   * Update multiple state properties at once
   * @param {Object} updates - Object with paths as keys and new values
   */
  update(updates) {
    Object.entries(updates).forEach(([path, value]) => {
      this.set(path, value);
    });
  }

  /**
   * Subscribe to state changes
   * @param {string} path - Path to watch (or '*' for all changes)
   * @param {Function} callback - Function to call on changes
   * @returns {Function} - Unsubscribe function
   */
  subscribe(path, callback) {
    if (!this.subscribers.has(path)) {
      this.subscribers.set(path, new Set());
    }
    this.subscribers.get(path).add(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.subscribers.get(path);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this.subscribers.delete(path);
        }
      }
    };
  }

  /**
   * Emit event to subscribers
   * @param {string} path - Path that changed
   * @param {Object} data - Change data
   */
  emit(path, data) {
    // Notify specific path subscribers
    const pathSubscribers = this.subscribers.get(path);
    if (pathSubscribers) {
      pathSubscribers.forEach((callback) => callback(data));
    }

    // Notify wildcard subscribers
    const wildcardSubscribers = this.subscribers.get('*');
    if (wildcardSubscribers) {
      wildcardSubscribers.forEach((callback) => callback(data));
    }

    // Notify parent path subscribers (e.g., 'filters' when 'filters.species' changes)
    const parentPath = path.substring(0, path.lastIndexOf('.'));
    if (parentPath && this.subscribers.has(parentPath)) {
      this.subscribers.get(parentPath).forEach((callback) => callback(data));
    }
  }

  /**
   * Persist starred landings to localStorage
   */
  persistStarredLandings() {
    try {
      localStorage.setItem('starredLandings', JSON.stringify(this.state.starredLandings));
    } catch (error) {
      console.error('Failed to save starred landings:', error);
    }
  }

  /**
   * Toggle starred status for a landing
   * @param {string} landingId - Landing ID to toggle
   * @returns {boolean} - New starred status
   */
  toggleStarred(landingId) {
    const index = this.state.starredLandings.indexOf(landingId);
    if (index === -1) {
      this.state.starredLandings.push(landingId);
    } else {
      this.state.starredLandings.splice(index, 1);
    }

    this.emit('starredLandings', {
      path: 'starredLandings',
      value: [...this.state.starredLandings],
    });

    this.persistStarredLandings();
    return index === -1; // Return true if now starred, false if unstarred
  }

  /**
   * Check if landing is starred
   * @param {string} landingId - Landing ID to check
   * @returns {boolean} - Starred status
   */
  isStarred(landingId) {
    return this.state.starredLandings.includes(landingId);
  }

  /**
   * Get current filter values for API calls
   * @returns {Object} - Filter object for API
   */
  getApiFilters() {
    const filters = {};
    const { filters: stateFilters, selectedLanding, boatNameToIdMap } = this.state;

    if (stateFilters.startDate) filters.startDate = stateFilters.startDate;
    if (stateFilters.endDate) filters.endDate = stateFilters.endDate;

    if (stateFilters.species !== 'all') {
      filters.species = stateFilters.species;
    }

    if (stateFilters.duration !== 'all') {
      filters.duration = stateFilters.duration;
    }

    if (stateFilters.boat !== 'all') {
      filters.boat = stateFilters.boat;
      const resolvedBoatId = boatNameToIdMap?.[stateFilters.boat];
      if (resolvedBoatId) {
        filters.boat_id = resolvedBoatId;
      }
    }

    if (selectedLanding) {
      filters.landing_id = selectedLanding;
    }

    return filters;
  }

  /**
   * Persist landing mapping for downstream lookups
   * @param {Object} mapping - Map of landing_id -> landing_name
   */
  setLandingMapping(mapping = {}) {
    this.state.landingIdToNameMap = { ...mapping };
  }

  /**
   * Persist boat mapping for downstream lookups
   * @param {Object} mapping - Map of boat_name -> boat_id
   */
  setBoatMapping(mapping = {}) {
    this.state.boatNameToIdMap = { ...mapping };
  }

  /**
   * Set loading state
   * @param {boolean} isLoading - Loading status
   */
  setLoading(isLoading) {
    this.set('ui.isLoading', isLoading);
  }

  /**
   * Set error state
   * @param {string|null} error - Error message or null
   */
  setError(error) {
    this.set('ui.error', error);
  }

  /**
   * Reset all filters to defaults
   */
  resetFilters() {
    this.update({
      'filters.species': 'all',
      'filters.duration': 'all',
      'filters.boat': 'all',
      selectedLanding: null,
    });
  }

  /**
   * Clear all state (except starred landings)
   */
  clear() {
    const starred = [...this.state.starredLandings];
    this.state = {
      selectedLanding: null,
      filters: {
        startDate: this.state.filters.startDate,
        endDate: this.state.filters.endDate,
        species: 'all',
        duration: 'all',
        boat: 'all',
      },
      starredLandings: starred,
      landingsData: {},
      landingIdToNameMap: {},
      boatNameToIdMap: {},
      charts: {
        dailyCatchesData: null,
        topBoatsData: null,
      },
      ui: {
        isLoading: false,
        error: null,
      },
    };
    this.emit('*', { path: '*', value: this.state });
  }
}

// Create and export singleton instance
const state = new StateManager();
export default state;

// Export class for testing purposes
export { StateManager };
