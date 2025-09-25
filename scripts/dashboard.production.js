/**
 * Production Dashboard Entry Point
 * Direct Supabase connection for Vercel deployment
 */

import supabaseClient from './supabaseClient.js';

// Simple state management
let currentData = {
  trips: [],
  stats: {},
  landings: []
};

/**
 * Initialize the dashboard
 */
async function initDashboard() {
  console.log('🚀 Starting SD Fishing Intelligence Dashboard');

  try {
    // Show loading state
    showLoading();

    // Load data from Supabase
    await loadData();

    // Render components
    renderNavigation();
    renderStats();
    renderRecentTrips();

    console.log('✅ Dashboard loaded successfully');

  } catch (error) {
    console.error('❌ Dashboard initialization failed:', error);
    showError(error.message);
  }
}

/**
 * Load all data from Supabase
 */
async function loadData() {
  try {
    console.log('📊 Loading data from Supabase...');

    // Load in parallel
    const [trips, stats, landings] = await Promise.all([
      supabaseClient.getFishingTrips({ limit: 50 }),
      supabaseClient.getStats(),
      supabaseClient.getBoatLandings()
    ]);

    currentData = { trips, stats, landings };
    console.log('✅ Data loaded:', {
      trips: trips.length,
      landings: landings.length,
      totalTrips: stats.total_trips
    });

  } catch (error) {
    console.error('❌ Failed to load data:', error);
    throw error;
  }
}

/**
 * Render navigation with landings
 */
function renderNavigation() {
  const sanDiegoSection = document.getElementById('sanDiegoSection');
  if (!sanDiegoSection) return;

  const html = currentData.landings
    .map(landing => `
      <div class="nav-item hover:bg-accent hover:text-accent-foreground" data-landing-id="${landing.landing_id}">
        <div class="nav-item-content">
          <span class="text-foreground">${landing.landing_name}</span>
          <span class="text-muted-foreground text-xs">${landing.city || ''}</span>
        </div>
      </div>
    `).join('');

  sanDiegoSection.innerHTML = html;

  // Add click handlers
  sanDiegoSection.addEventListener('click', async (e) => {
    const navItem = e.target.closest('.nav-item');
    if (navItem) {
      const landingId = navItem.dataset.landingId;
      await filterByLanding(landingId);
    }
  });
}

/**
 * Render stats grid
 */
function renderStats() {
  const container = document.getElementById('statsGridContainer');
  if (!container) return;

  const { stats } = currentData;

  container.innerHTML = `
    <div class="dashboard-section">
      <h2 class="text-xl font-semibold mb-4">Overview</h2>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-number">${(stats.total_trips || 0).toLocaleString()}</div>
          <div class="stat-label">Total Trips</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${(stats.total_anglers || 0).toLocaleString()}</div>
          <div class="stat-label">Total Anglers</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${(stats.total_fish || 0).toLocaleString()}</div>
          <div class="stat-label">Fish Caught</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${(stats.unique_species || 0)}</div>
          <div class="stat-label">Species</div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Render recent trips table
 */
function renderRecentTrips() {
  const container = document.getElementById('recentTripsContainer');
  if (!container) return;

  const { trips } = currentData;

  const tableRows = trips.slice(0, 20).map(trip => {
    const totalCatch = trip.catches?.reduce((sum, c) => sum + (c.count || 0), 0) || 0;
    const species = trip.catches?.map(c => c.species_name).join(', ') || 'No catch data';

    return `
      <tr>
        <td class="table-cell">${formatDate(trip.trip_date)}</td>
        <td class="table-cell">${trip.boat_landings?.landing_name || 'Unknown'}</td>
        <td class="table-cell">${trip.boat_name || 'Unknown Boat'}</td>
        <td class="table-cell">${trip.anglers || 0}</td>
        <td class="table-cell">${totalCatch}</td>
        <td class="table-cell max-w-xs truncate" title="${species}">${species}</td>
      </tr>
    `;
  }).join('');

  container.innerHTML = `
    <div class="dashboard-section">
      <h2 class="text-xl font-semibold mb-4">Recent Trips</h2>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th class="table-header">Date</th>
              <th class="table-header">Landing</th>
              <th class="table-header">Boat</th>
              <th class="table-header">Anglers</th>
              <th class="table-header">Total Catch</th>
              <th class="table-header">Species</th>
            </tr>
          </thead>
          <tbody>
            ${tableRows}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

/**
 * Filter trips by landing
 */
async function filterByLanding(landingId) {
  try {
    showLoading();

    // Update active state
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.remove('active');
    });
    document.querySelector(`[data-landing-id="${landingId}"]`)?.classList.add('active');

    // Load filtered data
    const trips = await supabaseClient.getFishingTrips({ landing_id: landingId });
    currentData.trips = trips;

    // Re-render
    renderRecentTrips();

  } catch (error) {
    console.error('❌ Failed to filter by landing:', error);
    showError(error.message);
  }
}

/**
 * Show loading state
 */
function showLoading() {
  const containers = ['statsGridContainer', 'recentTripsContainer'];
  containers.forEach(id => {
    const container = document.getElementById(id);
    if (container) {
      container.innerHTML = '<div class="loading-spinner">Loading...</div>';
    }
  });
}

/**
 * Show error state
 */
function showError(message) {
  const containers = ['statsGridContainer', 'recentTripsContainer'];
  containers.forEach(id => {
    const container = document.getElementById(id);
    if (container) {
      container.innerHTML = `<div class="error-message">Error: ${message}</div>`;
    }
  });
}

/**
 * Format date for display
 */
function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboard);
} else {
  initDashboard();
}

export default {
  initDashboard,
  loadData,
  filterByLanding
};