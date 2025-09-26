// Dashboard entry point - orchestrates navigation, filters, stats, charts, and tables

import * as apiClient from './apiClient.js';
import state from './state.js';
import { isFeatureEnabled } from './config/featureFlags.js';
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
    // Get comprehensive trips data to extract filter options
    const response = await fetch('/api/trips?limit=500');
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    const result = await response.json();
    const trips = result.success ? result.data : result;

    // Extract filter options from trips data
    const filters = generateFilterOptionsFromTrips(trips, landingId);
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

// Helper function to generate filter options from trips data
function generateFilterOptionsFromTrips(trips, landingId) {
  const species = new Set();
  const durations = new Set();
  const boats = new Set();

  trips.forEach(trip => {
    // Filter by landing if specified
    if (landingId && landingId !== 'all' && trip.boat?.landing_id !== parseInt(landingId)) {
      return;
    }

    // Extract species from catches
    if (trip.catches && Array.isArray(trip.catches)) {
      trip.catches.forEach(catch_ => {
        if (catch_.species_name || catch_.species) {
          species.add(catch_.species_name || catch_.species);
        }
      });
    }

    // Extract durations
    if (trip.trip_duration) {
      durations.add(trip.trip_duration);
    }

    // Extract boat names
    if (trip.boat?.name) {
      boats.add(trip.boat.name);
    }
  });

  return {
    species: Array.from(species).sort().map(name => ({ value: name, label: name })),
    durations: Array.from(durations).sort().map(duration => ({ value: duration, label: duration })),
    boats: Array.from(boats).sort().map(name => ({ value: name, label: name }))
  };
}

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
    // Use the simple /api/stats endpoint that already works
    return apiClient.fetchStats(filters, { cancelKey: 'stats' });
  }

  // Fallback to direct API call to working /api/stats endpoint
  const response = await fetch('/api/stats');
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
    // Use existing /api/trips and aggregate by date
    return apiClient.fetchTrips(null, filters, { cancelKey: 'daily-catches' })
      .then(trips => aggregateDailyCatches(trips, days));
  }

  // Fallback: use /api/trips and aggregate daily catches
  const response = await fetch('/api/trips?limit=500');
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  const result = await response.json();

  const trips = result.success ? result.data : result;
  return aggregateDailyCatches(trips, days);
}

// Helper function to aggregate daily catches from trip data
function aggregateDailyCatches(trips, days) {
  const dailyStats = {};
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);

  trips.forEach(trip => {
    const tripDate = new Date(trip.trip_date);
    if (tripDate >= cutoffDate) {
      const dateKey = trip.trip_date;
      if (!dailyStats[dateKey]) {
        dailyStats[dateKey] = { date: dateKey, catches: 0 };
      }
      dailyStats[dateKey].catches += trip.total_fish || 0;
    }
  });

  const sortedData = Object.values(dailyStats).sort((a, b) => new Date(a.date) - new Date(b.date));

  // Transform to chart format: { labels: [...], fish: [...] }
  return {
    labels: sortedData.map(d => d.date),
    fish: sortedData.map(d => d.catches)
  };
}

async function fetchTopBoats(filters) {
  if (isFeatureEnabled('USE_NEW_API_CLIENT')) {
    // Use existing /api/trips and calculate top boats
    return apiClient.fetchTrips(null, filters, { cancelKey: 'top-boats' })
      .then(trips => calculateTopBoats(trips));
  }

  // Fallback: use /api/trips and calculate top boats
  const response = await fetch('/api/trips?limit=500');
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  const result = await response.json();

  const trips = result.success ? result.data : result;
  return calculateTopBoats(trips);
}

// Helper function to calculate top boats from trip data
function calculateTopBoats(trips) {
  const boatStats = {};

  trips.forEach(trip => {
    const boatName = trip.boat?.name || 'Unknown';
    if (!boatStats[boatName]) {
      boatStats[boatName] = {
        name: boatName,
        totalFish: 0,
        tripCount: 0
      };
    }
    boatStats[boatName].totalFish += trip.total_fish || 0;
    boatStats[boatName].tripCount += 1;
  });

  const sortedBoats = Object.values(boatStats)
    .map(boat => ({ ...boat, avgPerTrip: Math.round(boat.totalFish / boat.tripCount) }))
    .sort((a, b) => b.totalFish - a.totalFish)
    .slice(0, 10);

  // Transform to chart format: { labels: [...], fish: [...] }
  return {
    labels: sortedBoats.map(boat => boat.name),
    fish: sortedBoats.map(boat => boat.totalFish)
  };
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
      date: trip.trip_date || trip.date,
      boat: trip.boat?.name || trip.boat || 'Unknown',
      landing: trip.boat?.landing?.name || trip.landing || 'Unknown',
      duration: trip.trip_duration || trip.duration || 'N/A',
      anglers: trip.anglers || 'N/A',
      fishCount: trip.total_fish || trip.fishCount || 0,
      topSpecies: (trip.catches && trip.catches.length > 0)
        ? trip.catches[0].species_name || trip.catches[0].species || 'N/A'
        : trip.topSpecies || 'N/A',
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
    // Use existing /api/trips endpoint and get first 10 trips
    return apiClient.fetchTrips(10, filters, { cancelKey: 'recent-trips' });
  }

  // Fallback to direct API call to working /api/trips endpoint
  const response = await fetch('/api/trips?limit=50');
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  const result = await response.json();

  // Extract trips from API response and limit to 10
  const trips = result.success ? result.data : result;
  return Array.isArray(trips) ? trips.slice(0, 10) : [];
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
  const defaultDates = getDefaultDateRange();

  renderFilterBar(defaultDates);
  renderStatsSkeleton();
  renderChartsShell();
  renderTableShell();
  createIcons();
  attachFilterListeners();

  try {
    // Get filter options for dropdowns
    const filters = await refreshFilterOptions(null);

    // Get landing locations for navigation (separate API call)
    const landingsResponse = await fetch('/api/filters');
    let landingsData = null;
    if (landingsResponse.ok) {
      const result = await landingsResponse.json();
      landingsData = result.success ? result.data : result;
    }

    await initializeNavigation({ filters: landingsData });
  } catch (error) {
    if (error?.isCanceled) {
      return;
    }
    // Navigation module already handled rendering an error state
  }

  await loadDashboardData();

  document.addEventListener('landingSelected', handleLandingSelected);
}

// Bootstrap when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  initializeDashboard().catch((error) => {
    console.error('Failed to initialize dashboard:', error);
  });
});
