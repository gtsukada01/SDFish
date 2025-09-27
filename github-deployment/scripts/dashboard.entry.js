// Dashboard entry point - orchestrates navigation, filters, stats, charts, and tables

import * as apiClient from './apiClient.js';
import state from './state.js';
// Import debug helper (can be removed after stabilization)
import debugHelper from './debug.js';
const { dbg, updateDebugState, initDebug, checkMappings } = debugHelper;
import { createIcons } from './externals/lucide.js';
import { timeRender, timeStateUpdate } from './performanceMonitor.js';
import { withErrorBoundary, withUIErrorBoundary, logError, ERROR_CATEGORIES, ERROR_LEVELS } from './errorBoundary.js';
import './productionMonitor.js';
import './performanceValidator.js';
import './rollbackManager.js';
import { initializeNavigation, fetchFiltersForLanding } from './navigation.js';
import { renderStatsGrid, DEFAULT_STATS_CARDS, createChartCard } from './components/cards.js';
import {
  renderTable,
  DEFAULT_TRIPS_TABLE_CONFIG,
  updateTableBody,
  showTableLoading,
  showTableError,
} from './components/tables.js';
import {
  createSelect,
  createDateRangePicker,
  updateSelectOptions,
  showSelectLoading,
  showSelectError,
  clearSelectError,
  DEFAULT_FILTER_CONFIG,
} from './components/forms.js';
import {
  createDailyCatchesChart,
  createTopBoatsChart,
  createMoonPhaseChart,
  showChartLoading,
  showChartError,
  clearChartOverlays,
  observeChartContainer,
} from './charts.js';

const FILTER_SELECT_IDS = ['speciesFilter', 'durationFilter', 'boatFilter'];
let selectedLandingId = null;
let chartsInitialized = false;
let tableInitialized = false;

/**
 * Return default date range (Jan 1, 2025 to today)
 */
function getDefaultDateRange() {
  const endDate = new Date();
  const startDate = new Date('2025-01-01');
  return {
    start: startDate.toISOString().split('T')[0],
    end: endDate.toISOString().split('T')[0],
  };
}

/**
 * Render filter bar using shadcn form components
 */
const renderFilterBar = withUIErrorBoundary(function renderFilterBar({ start, end }) {
  const mount = document.getElementById('filtersMount');
  if (!mount) return;

  const speciesConfig = {
    ...DEFAULT_FILTER_CONFIG.species,
    options: [{ value: 'all', label: 'All Species' }],
  };
  const durationConfig = {
    ...DEFAULT_FILTER_CONFIG.duration,
    options: [{ value: 'all', label: 'All Durations' }],
  };
  const boatConfig = {
    ...DEFAULT_FILTER_CONFIG.boat,
    options: [{ value: 'all', label: 'All Boats' }],
  };

  const filtersMarkup = `
    <form id="filtersForm" class="filters-form flex flex-wrap items-end gap-4">
      <div class="filters-date-range">
        ${createDateRangePicker({
          startId: 'startDate',
          endId: 'endDate',
          startValue: start,
          endValue: end,
        })}
      </div>
      <div class="filters-selects flex flex-wrap gap-4">
        ${createSelect(speciesConfig)}
        ${createSelect(durationConfig)}
        ${createSelect(boatConfig)}
      </div>
    </form>
  `;

  mount.innerHTML = filtersMarkup;
}, { componentName: 'renderFilterBar', showRetry: false });

/**
 * Render stats grid placeholder
 */
function renderStatsSkeleton() {
  const container = document.getElementById('statsGridContainer');
  if (!container) return;

  const loadingCards = DEFAULT_STATS_CARDS.map((card) => ({
    ...card,
    value: '<span class="text-sm text-muted-foreground">Loading…</span>',
  }));

  timeRender(() => {
    renderStatsGrid(loadingCards, container);
    createIcons();
  }, 'renderStatsSkeleton');
}

/**
 * Render chart cards once
 */
function renderChartsShell() {
  if (chartsInitialized) return;

  const chartsContainer = document.getElementById('chartsContainer');
  if (!chartsContainer) return;

  const chartCards = [
    createChartCard({
      id: 'dailyCatchesCardContainer',
      title: 'Daily Catches',
      canvasId: 'dailyCatchesChart',
    }),
    createChartCard({
      id: 'topBoatsCardContainer',
      title: 'Top Boats',
      canvasId: 'topBoatsChart',
    }),
    createChartCard({
      id: 'moonPhaseCardContainer',
      title: 'Fishing Success by Moon Phase',
      canvasId: 'moonPhaseChart',
    }),
  ].join('');

  chartsContainer.innerHTML = chartCards;
  chartsInitialized = true;
}

/**
 * Render table card once
 */
function renderTableShell() {
  if (tableInitialized) return;

  const tableContainer = document.getElementById('recentTripsContainer');
  if (!tableContainer) return;

  renderTable(DEFAULT_TRIPS_TABLE_CONFIG, tableContainer);
  tableInitialized = true;
}

/**
 * Put selects into a temporary loading state
 */
function showFiltersLoading() {
  FILTER_SELECT_IDS.forEach((id) => showSelectLoading(id));
}

/**
 * Clear loading/disabled state for selects
 */
function clearFiltersDisabledState() {
  FILTER_SELECT_IDS.forEach((id) => {
    const select = document.getElementById(id);
    if (select) {
      select.disabled = false;
      clearSelectError(id);
    }
  });
}

/**
 * Update select options using fetched filter metadata
 */
function applyFiltersToSelects(filters) {
  updateSelectOptions('speciesFilter', filters.species ?? [], 'all', 'All Species');
  updateSelectOptions('durationFilter', filters.durations ?? [], 'all', 'All Durations');
  updateSelectOptions('boatFilter', filters.boats ?? [], 'all', 'All Boats');

  clearFiltersDisabledState();
}

/**
 * Gather current filter form values from DOM
 */
function getFilterValues() {
  const formValues = {
    startDate: document.getElementById('startDate')?.value || '',
    endDate: document.getElementById('endDate')?.value || '',
    species: document.getElementById('speciesFilter')?.value || 'all',
    duration: document.getElementById('durationFilter')?.value || 'all',
    boat: document.getElementById('boatFilter')?.value || 'all',
  };

  return formValues;
}

/**
 * Build API filters object when not using state module
 */
function buildApiFilters(values) {
  const filters = {};
  if (values.startDate) filters.startDate = values.startDate;
  if (values.endDate) filters.endDate = values.endDate;
  if (values.species !== 'all') filters.species = values.species;
  if (values.duration !== 'all') filters.duration = values.duration;
  if (values.boat !== 'all') filters.boat = values.boat;
  if (selectedLandingId) filters.landing = selectedLandingId;
  return filters;
}

/**
 * Synchronize filters to state module when enabled
 */
function syncFiltersToState(values) {
  if (!isFeatureEnabled('USE_NEW_STATE')) return;

  timeStateUpdate(() => {
    state.update({
      'filters.startDate': values.startDate || null,
      'filters.endDate': values.endDate || null,
      'filters.species': values.species,
      'filters.duration': values.duration,
      'filters.boat': values.boat,
    });
  }, 'updateFilters');
}

/**
 * Fetch filter metadata and update selects
 */
const refreshFilterOptions = withErrorBoundary(async function refreshFilterOptions(landingId) {
  showFiltersLoading();

  try {
    const filters = await fetchFilters(landingId);
    applyFiltersToSelects(filters);
    return filters;
  } catch (error) {
    if (error?.isCanceled) {
      return null;
    }

    showSelectError('speciesFilter', 'Failed to load species');
    showSelectError('durationFilter', 'Failed to load durations');
    showSelectError('boatFilter', 'Failed to load boats');

    if (isFeatureEnabled('ENABLE_DETAILED_ERROR_LOGGING')) {
      console.error('Error loading filter metadata:', error);
    }

    throw error;
  }
}, { category: ERROR_CATEGORIES.NETWORK, level: ERROR_LEVELS.MEDIUM, name: 'refreshFilterOptions' });

/**
 * Wrapper to fetch filters via API client or legacy fetch
 */
async function fetchFilters(landingId) {
  if (isFeatureEnabled('USE_NEW_API_CLIENT')) {
    return apiClient.fetchFilters(landingId, { cancelKey: 'filters' });
  }

  return fetchFiltersForLanding(landingId, { cancelPrevious: true, cancelKey: 'filters' });
}

/**
 * Render stats using fetched data
 */
function renderStats(data) {
  const cards = [
    {
      ...DEFAULT_STATS_CARDS[0],
      value: formatNumber(data.trips),
    },
    {
      ...DEFAULT_STATS_CARDS[1],
      value: formatNumber(data.fish),
    },
    {
      ...DEFAULT_STATS_CARDS[2],
      value: formatAverage(data.avgPerTrip),
    },
    {
      ...DEFAULT_STATS_CARDS[3],
      value: formatNumber(data.boats),
    },
  ];

  const container = document.getElementById('statsGridContainer');
  if (!container) return;

  timeRender(() => {
    renderStatsGrid(cards, container);
    createIcons();
  }, 'renderStats');
}

/**
 * Render stats error state
 */
function renderStatsError(message) {
  const cards = DEFAULT_STATS_CARDS.map((card) => ({
    ...card,
    value: `<span class="text-sm text-destructive">${message}</span>`,
  }));

  const container = document.getElementById('statsGridContainer');
  if (!container) return;

  renderStatsGrid(cards, container);
  createIcons();
}

/**
 * Load and render statistics
 */
const loadStats = withErrorBoundary(async function loadStats(filterValues, apiFilters) {
  renderStatsSkeleton();

  try {
    const stats = await fetchStats(filterValues.startDate, filterValues.endDate, apiFilters);
    renderStats(stats);

    if (isFeatureEnabled('USE_NEW_STATE')) {
      timeStateUpdate(() => state.set('ui.error', null), 'clearStatsError');
    }
  } catch (error) {
    if (error?.isCanceled) return;

    const message = error?.message || 'Failed to load statistics';
    renderStatsError(message);

    if (isFeatureEnabled('USE_NEW_STATE')) {
      timeStateUpdate(() => state.set('ui.error', message), 'setStatsError');
    }
  }
}, { category: ERROR_CATEGORIES.DATA, level: ERROR_LEVELS.MEDIUM, name: 'loadStats' });

/**
 * Fetch statistics via API client or legacy fetch
 */
async function fetchStats(startDate, endDate, filters) {
  if (isFeatureEnabled('USE_NEW_API_CLIENT')) {
    return apiClient.fetchStatsForDateRange(startDate, endDate, filters, { cancelKey: 'stats' });
  }

  const params = new URLSearchParams(filters);
  const query = params.toString();
  const queryString = query ? `?${query}` : '';

  const url =
    startDate && endDate
      ? `http://localhost:5001/api/stats/date-range/${startDate}/${endDate}${queryString}`
      : `http://localhost:5001/api/stats/last-30-days${queryString}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  return response.json();
}

/**
 * Load and render chart data
 */
async function loadCharts(filterValues, apiFilters) {
  if (!chartsInitialized) {
    renderChartsShell();
  }

  showChartLoading('dailyCatchesChart');
  showChartLoading('moonPhaseChart');

  // Check if boat filter is applied
  const isBoatFiltered = filterValues.boat && filterValues.boat !== 'all';

  // Show/hide top boats chart based on boat filter
  const topBoatsContainer = document.getElementById('topBoatsCardContainer');
  if (topBoatsContainer) {
    if (isBoatFiltered) {
      topBoatsContainer.style.display = 'none';
    } else {
      topBoatsContainer.style.display = '';
      showChartLoading('topBoatsChart');
    }
  }

  const dayCount = calculateDayRange(filterValues.startDate, filterValues.endDate);

  try {
    const dailyData = await fetchDailyCatches(dayCount, apiFilters);
    clearChartOverlays('dailyCatchesChart');
    createDailyCatchesChart(dailyData);
    observeChartContainer('dailyCatchesChart');
  } catch (error) {
    if (!error?.isCanceled) {
      const message = error?.message || 'Failed to load chart';
      showChartError('dailyCatchesChart', message);
      createIcons();
    }
  }

  // Only load top boats chart when not filtering by a specific boat
  if (!isBoatFiltered) {
    try {
      const topBoats = await fetchTopBoats(apiFilters);
      clearChartOverlays('topBoatsChart');
      createTopBoatsChart(topBoats);
      observeChartContainer('topBoatsChart');
    } catch (error) {
      if (!error?.isCanceled) {
        const message = error?.message || 'Failed to load chart';
        showChartError('topBoatsChart', message);
        createIcons();
      }
    }
  }

  try {
    const moonPhaseData = await fetchMoonPhaseData();
    clearChartOverlays('moonPhaseChart');
    createMoonPhaseChart(moonPhaseData);
    observeChartContainer('moonPhaseChart');
  } catch (error) {
    if (!error?.isCanceled) {
      const message = error?.message || 'Failed to load moon phase chart';
      showChartError('moonPhaseChart', message);
      createIcons();
    }
  }
}

/**
 * Fetch chart data via API client or legacy fetch
 */
async function fetchDailyCatches(days, filters) {
  if (isFeatureEnabled('USE_NEW_API_CLIENT')) {
    return apiClient.fetchDailyCatches(days, filters, { cancelKey: 'daily-catches' });
  }

  const params = new URLSearchParams(filters);
  const query = params.toString();
  const queryString = query ? `?${query}` : '';

  const response = await fetch(`http://localhost:5001/api/daily-catches/${days}${queryString}`);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  return response.json();
}

async function fetchTopBoats(filters) {
  if (isFeatureEnabled('USE_NEW_API_CLIENT')) {
    return apiClient.fetchTopBoats(10, filters, { cancelKey: 'top-boats' });
  }

  const params = new URLSearchParams(filters);
  const query = params.toString();
  const queryString = query ? `?${query}` : '';

  const response = await fetch(`http://localhost:5001/api/top-boats/10${queryString}`);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  return response.json();
}

async function fetchMoonPhaseData() {
  if (isFeatureEnabled('USE_NEW_API_CLIENT')) {
    return apiClient.fetchMoonPhaseData({ cancelKey: 'moon-phase' });
  }

  const response = await fetch('http://localhost:5001/api/moon-phase-data');
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  return response.json();
}

/**
 * Load and render recent trips table
 */
async function loadRecentTrips(apiFilters) {
  if (!tableInitialized) {
    renderTableShell();
  }

  const columns = DEFAULT_TRIPS_TABLE_CONFIG.columns;
  showTableLoading('recentTripsTable', columns);

  try {
    const trips = await fetchRecentTrips(apiFilters);
    const formatted = trips.map((trip) => ({
      date: trip.date,
      boat: trip.boat,
      landing: trip.landing,
      duration: trip.duration,
      anglers: trip.anglers,
      fishCount: trip.fishCount,
      topSpecies: trip.topSpecies || 'N/A',
    }));

    updateTableBody('recentTripsTable', columns, formatted, 'No recent trips found');
  } catch (error) {
    if (error?.isCanceled) return;

    const message = error?.message || 'Failed to load trips';
    showTableError('recentTripsTable', columns, message);
    createIcons();
  }
}

/**
 * Fetch recent trips via API client or legacy fetch
 */
async function fetchRecentTrips(filters) {
  if (isFeatureEnabled('USE_NEW_API_CLIENT')) {
    return apiClient.fetchRecentTrips(10, filters, { cancelKey: 'recent-trips' });
  }

  const params = new URLSearchParams(filters);
  const query = params.toString();
  const queryString = query ? `?${query}` : '';

  const response = await fetch(`http://localhost:5001/api/recent-trips/10${queryString}`);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  return response.json();
}

/**
 * Calculate inclusive day range between two ISO strings
 */
function calculateDayRange(startDate, endDate) {
  if (!startDate || !endDate) return 30;
  const start = new Date(startDate);
  const end = new Date(endDate);
  const diff = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
  return Number.isFinite(diff) && diff > 0 ? diff : 30;
}

/**
 * Entry point to load all dashboard data
 */
async function loadDashboardData() {
  const filterValues = getFilterValues();
  syncFiltersToState(filterValues);

  const apiFilters = isFeatureEnabled('USE_NEW_STATE')
    ? state.getApiFilters()
    : buildApiFilters(filterValues);

  await loadStats(filterValues, apiFilters);
  await loadCharts(filterValues, apiFilters);
  await loadRecentTrips(apiFilters);
}

/**
 * Handle filter input changes
 */
async function handleFilterChange() {
  await loadDashboardData();
}

/**
 * Attach event listeners for filter controls
 */
function attachFilterListeners() {
  const form = document.getElementById('filtersForm');
  if (!form) return;

  form.addEventListener('change', (event) => {
    if (event.target.matches('select, input[type="date"]')) {
      handleFilterChange();
    }
  });
}

/**
 * Handle landing selection emitted by navigation module
 */
async function handleLandingSelected(event) {
  selectedLandingId = event.detail.landingId ? event.detail.landingId.toString() : null;

  try {
    await refreshFilterOptions(selectedLandingId);
  } catch (error) {
    if (error?.isCanceled) {
      return;
    }
  }

  await loadDashboardData();
}

/**
 * Format helper for numeric metrics
 */
function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '0';
  }
  return Number(value).toLocaleString('en-US');
}

function formatAverage(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '0.0';
  }
  return Number(value).toLocaleString('en-US', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

/**
 * Initialize dashboard
 */
async function initializeDashboard() {
  // Initialize debug mode if enabled
  initDebug();
  dbg('initializeDashboard() starting...');

  const defaultDates = getDefaultDateRange();

  renderFilterBar(defaultDates);
  renderStatsSkeleton();
  renderChartsShell();
  renderTableShell();
  createIcons();
  attachFilterListeners();

  try {
    const filters = await refreshFilterOptions(null);
    await initializeNavigation({ filters });
  } catch (error) {
    if (error?.isCanceled) {
      return;
    }
    // Navigation module already handled rendering an error state
  }

  await loadDashboardData();

  // Check boat mapping after first load and warn if empty
  setTimeout(() => {
    const boatMap = window.boatNameToIdMap || {};
    if (Object.keys(boatMap).length === 0) {
      console.warn('[mapping] boatNameToIdMap is empty after first load - boat filtering may not work correctly');
      console.warn('[mapping] Quick check: Object.entries(window.boatNameToIdMap || {}).slice(0,5)');
    } else {
      console.log('[mapping] Boat mappings loaded:', Object.keys(boatMap).length, 'boats');
      dbg('Sample boat mappings:', Object.entries(boatMap).slice(0, 5));
    }
  }, 100);

  document.addEventListener('landingSelected', handleLandingSelected);
}

// Bootstrap when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // CRITICAL FIX: Event Delegation Pattern - attach to document to survive DOM replacements
  // This ensures filter changes always work regardless of when the form is created
  // Production-safe, always-on delegation logs
  console.log('[filters] Delegation attach: start');

  // Use capture=true to avoid being blocked and survive innerHTML replacements
  document.addEventListener('change', (event) => {
    const form = event.target.closest('#filtersForm');
    if (form && event.target.matches('select, input[type="date"]')) {
      console.log('[filters] Delegation change:', event.target.name, '=', event.target.value);

      // Update debug state if available
      if (typeof updateDebugState === 'function') {
        updateDebugState('filterChange', {
          field: event.target.name,
          value: event.target.value,
          source: 'event_delegation'
        });
      }

      // Call the filter change handler if it exists
      if (typeof handleFilterChange === 'function') {
        handleFilterChange();
      } else if (typeof loadDashboardData === 'function') {
        // Fallback: directly call loadDashboardData if handleFilterChange is missing
        console.warn('handleFilterChange not defined, falling back to loadDashboardData()');
        loadDashboardData();
      } else {
        console.error('Neither handleFilterChange nor loadDashboardData function defined!');
      }
    }
  }, true); // capture=true to survive innerHTML replacements

  console.log('[filters] Delegation attach: ready');

  // Initialize dashboard
  initializeDashboard().catch((error) => {
    console.error('Failed to initialize dashboard:', error);
  });
});
