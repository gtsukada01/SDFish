/**
 * Navigation Module - shadcn/ui Components
 * Renders navigation sections using shadcn Button, Badge, and Card components
 */

import { createIcons } from './externals/lucide.js';
import { timeRender, timeStateUpdate } from './performanceMonitor.js';
import { isFeatureEnabled } from './config/featureFlags.js';
import * as apiClient from './apiClient.js';
import state from './state.js';

// Navigation data structure
export const navigationData = {
  landingsByRegion: { 'san-diego': [] },
  activeItem: null,
};

let pinnedSectionEl = null;
let sanDiegoSectionEl = null;
let navigationHandlersAttached = false;

/**
 * Create navigation item with shadcn styling
 * @param {Object} landing - Landing data object
 * @returns {string} - HTML string with shadcn classes
 */
function createNavItem(landing) {
  const isStarred = landing.starred ? 'starred' : '';

  return `
    <div class="nav-item flex items-center justify-between p-2 rounded-md text-sm cursor-pointer transition-colors hover:bg-accent hover:text-accent-foreground group"
         data-landing-id="${landing.id}">
      <div class="nav-item-content flex items-center gap-2">
        <span class="text-foreground">${landing.name}</span>
      </div>
      <button class="star-icon ${isStarred}"
              data-landing-id="${landing.id}"
              aria-label="Toggle favorite">
        <i data-lucide="star"></i>
      </button>
    </div>
  `;
}

// Removed createEmptyState - navigation sections stay empty when no data

/**
 * Initialize navigation with API data
 * @param {Object} options - Initialization options
 * @param {Object|null} options.filters - Optional pre-fetched filter payload
 * @returns {Promise<Object|null>} - Filters payload used for initialization
 */
export async function initializeNavigation({ filters = null } = {}) {
  pinnedSectionEl = document.getElementById('pinnedSection');
  sanDiegoSectionEl = document.getElementById('sanDiegoSection');

  if (!pinnedSectionEl || !sanDiegoSectionEl) {
    console.error('Navigation sections not found in DOM');
    return null;
  }

  try {
    const filtersData =
      filters ?? (await fetchFiltersForLanding(null, { cancelKey: 'navigation-init' }));

    // Handle API response structure: { success: true, data: { landings: [...] } }
    const landings = filtersData.data?.landings || filtersData.landings || [];
    navigationData.landingsByRegion['san-diego'] = landings.map((landing) => ({
      id: landing.id,
      name: landing.name,
      count: landing.count ?? 0,
      starred: false,
    }));

    applyStarredFlags();

    const persistedLanding = isFeatureEnabled('USE_NEW_STATE')
      ? state.get('selectedLanding')
      : null;
    navigationData.activeItem = persistedLanding ? persistedLanding.toString() : null;

    renderNavigation();
    attachNavigationEventHandlers();

    return filtersData;
  } catch (error) {
    if (error?.isCanceled) {
      return null;
    }

    if (isFeatureEnabled('ENABLE_DETAILED_ERROR_LOGGING')) {
      console.error('Error loading navigation:', error);
    }

    // Clear navigation sections on error
    if (pinnedSectionEl) pinnedSectionEl.innerHTML = '';
    if (sanDiegoSectionEl) sanDiegoSectionEl.innerHTML = '';

    throw error;
  }
}

/**
 * Render navigation sections using current module state
 */
function renderNavigation() {
  if (!pinnedSectionEl || !sanDiegoSectionEl) return;

  const starred = navigationData.landingsByRegion['san-diego'].filter((landing) => landing.starred);

  timeRender(() => {
    renderNavigationSections(pinnedSectionEl, sanDiegoSectionEl, starred);
    applyActiveState();
  }, 'renderNavigation');
}

/**
 * Apply starred flags from state/localStorage
 */
function applyStarredFlags() {
  const starredIds = getStoredStarredLandingIds();
  navigationData.landingsByRegion['san-diego'].forEach((landing) => {
    landing.starred = starredIds.includes(landing.id.toString());
  });
}

/**
 * Get starred landing IDs from state or storage
 * @returns {Array<string>} - Array of starred landing IDs
 */
function getStoredStarredLandingIds() {
  if (isFeatureEnabled('USE_NEW_STATE')) {
    const starred = state.get('starredLandings');
    return Array.isArray(starred) ? starred.map(String) : [];
  }

  try {
    const stored = localStorage.getItem('starredLandings');
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Failed to load starred landings from storage:', error);
    return [];
  }
}

/**
 * Render navigation sections using DOM fragments for performance
 * @param {HTMLElement} pinnedSection - Pinned section element
 * @param {HTMLElement} sanDiegoSection - San Diego section element
 * @param {Array} starred - Array of starred landings
 */
function renderNavigationSections(pinnedSection, sanDiegoSection, starred) {
  // Create fragments to avoid layout thrash
  const pinnedFragment = document.createDocumentFragment();
  const sanDiegoFragment = document.createDocumentFragment();

  // Render pinned section content
  if (starred.length > 0) {
    const pinnedDiv = document.createElement('div');
    pinnedDiv.innerHTML = starred.map((landing) => createNavItem(landing)).join('');
    pinnedFragment.appendChild(pinnedDiv);
  }
  // Leave empty when no pinned items

  // Render San Diego section content (exclude starred items)
  const unstarredLandings = navigationData.landingsByRegion['san-diego'].filter((landing) => !landing.starred);
  const sanDiegoDiv = document.createElement('div');
  sanDiegoDiv.innerHTML = unstarredLandings
    .map((landing) => createNavItem(landing))
    .join('');
  sanDiegoFragment.appendChild(sanDiegoDiv);

  // Atomic DOM updates
  pinnedSection.innerHTML = '';
  sanDiegoSection.innerHTML = '';
  pinnedSection.appendChild(pinnedFragment);
  sanDiegoSection.appendChild(sanDiegoFragment);

  // Re-initialize Lucide icons after DOM update
  timeRender(() => createIcons(), 'initializeLucideIcons');
}

/**
 * Attach navigation event handlers using event delegation
 */
function attachNavigationEventHandlers() {
  if (navigationHandlersAttached) return;

  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;

  sidebar.addEventListener('click', (event) => {
    const starButton = event.target.closest('.star-icon');
    if (starButton) {
      event.preventDefault();
      const landingId = starButton.dataset.landingId;
      if (landingId) {
        toggleStar(landingId.toString());
      }
      return;
    }

    const navItem = event.target.closest('.nav-item');
    if (navItem && navItem.dataset.landingId) {
      selectLanding(navItem.dataset.landingId.toString());
    }
  });

  navigationHandlersAttached = true;
}

/**
 * Toggle starred status for a landing
 * @param {string} landingId - Landing ID to toggle
 */
function toggleStar(landingId) {
  let wasStarred = false;

  if (isFeatureEnabled('USE_NEW_STATE')) {
    timeStateUpdate(() => state.toggleStarred(landingId), `toggleStar:${landingId}`);
  } else {
    const starredIds = getStoredStarredLandingIds();
    const index = starredIds.indexOf(landingId);
    if (index === -1) {
      starredIds.push(landingId);
      wasStarred = false; // Just starred it
    } else {
      starredIds.splice(index, 1);
      wasStarred = true; // Just unstarred it
    }

    try {
      localStorage.setItem('starredLandings', JSON.stringify(starredIds));
    } catch (error) {
      console.error('Failed to persist starred landings:', error);
    }
  }

  applyStarredFlags();
  renderNavigation();

  // Auto-select the landing when pinning it
  const starredIds = getStoredStarredLandingIds();
  const isNowStarred = starredIds.includes(landingId);

  if (isNowStarred) {
    // Landing was just pinned - auto-select it
    selectLanding(landingId);
  } else if (wasStarred && navigationData.activeItem === landingId) {
    // Landing was unpinned and was currently selected - go back to "All Landings"
    selectLanding('all');
  }
}

/**
 * Select a landing and update active state
 * @param {string} landingId - Landing ID to select ('all' for all landings)
 */
function selectLanding(landingId) {
  const normalizedLanding = landingId === 'all' ? null : landingId;
  navigationData.activeItem = normalizedLanding;

  applyActiveState();

  if (isFeatureEnabled('USE_NEW_STATE')) {
    timeStateUpdate(
      () => state.set('selectedLanding', normalizedLanding),
      `selectLanding:${normalizedLanding ?? 'all'}`
    );
  }

  // Trigger data reload (handled by dashboard module)
  const event = new window.CustomEvent('landingSelected', {
    detail: { landingId: normalizedLanding },
  });
  document.dispatchEvent(event);
}

/**
 * Apply active state styling to navigation items
 */
function applyActiveState() {
  const activeId = navigationData.activeItem ? navigationData.activeItem.toString() : 'all';
  const navItems = document.querySelectorAll('.sidebar .nav-item');

  navItems.forEach((item) => {
    const isActive = item.dataset.landingId === activeId;

    if (isActive) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });
}

/**
 * Fetch filters for landing (shared helper)
 * @param {string|null} landingId - Landing ID or null for all
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} - Filters payload
 */
export async function fetchFiltersForLanding(landingId, options = {}) {
  if (isFeatureEnabled('USE_NEW_API_CLIENT')) {
    return apiClient.fetchFilters(landingId, options);
  }

  const queryString = landingId ? `?landing=${landingId}` : '';
  const response = await fetch(`http://localhost:5001/api/filters${queryString}`);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  return response.json();
}

/**
 * Get current navigation state
 * @returns {Object} - Navigation state object
 */
export function getNavigationState() {
  return {
    activeItem: navigationData.activeItem,
    landingsCount: navigationData.landingsByRegion['san-diego'].length,
    starredCount: navigationData.landingsByRegion['san-diego'].filter((l) => l.starred).length,
  };
}
