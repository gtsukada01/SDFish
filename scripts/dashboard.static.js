/**
 * Static Dashboard with Sample Data for Vercel
 * Shows working dashboard with realistic fishing data
 */

// Sample fishing data based on your actual database structure
const SAMPLE_DATA = {
  stats: {
    total_trips: 7954,
    total_anglers: 45230,
    total_fish: 156847,
    unique_species: 47
  },
  landings: [
    { id: 1, name: 'Dana Point Harbor', city: 'Dana Point' },
    { id: 2, name: 'Newport Beach', city: 'Newport Beach' },
    { id: 3, name: 'Mission Bay', city: 'San Diego' },
    { id: 4, name: 'Point Loma Sportfishing', city: 'San Diego' },
    { id: 5, name: 'Seaforth Landing', city: 'San Diego' },
    { id: 6, name: 'H&M Landing', city: 'San Diego' },
    { id: 7, name: 'Fisherman\'s Landing', city: 'San Diego' },
    { id: 8, name: 'Marina del Rey', city: 'Marina del Rey' }
  ],
  trips: [
    {
      id: 1,
      trip_date: '2025-09-23',
      boat_name: 'Grande',
      landing_name: 'H&M Landing',
      anglers: 28,
      total_catch: 142,
      species: 'Yellowtail, Rockfish, Lingcod'
    },
    {
      id: 2,
      trip_date: '2025-09-22',
      boat_name: 'New Seaforth',
      landing_name: 'Seaforth Landing',
      anglers: 35,
      total_catch: 89,
      species: 'Yellowfin Tuna, Skipjack'
    },
    {
      id: 3,
      trip_date: '2025-09-22',
      boat_name: 'Qualifier 105',
      landing_name: 'Fisherman\'s Landing',
      anglers: 45,
      total_catch: 278,
      species: 'Bluefin Tuna, Yellowfin Tuna'
    },
    {
      id: 4,
      trip_date: '2025-09-21',
      boat_name: 'Pacific Queen',
      landing_name: 'Seaforth Landing',
      anglers: 22,
      total_catch: 156,
      species: 'Rockfish, Lingcod, Sand Bass'
    },
    {
      id: 5,
      trip_date: '2025-09-21',
      boat_name: 'Tribute',
      landing_name: 'Point Loma Sportfishing',
      anglers: 40,
      total_catch: 201,
      species: 'Yellowtail, Calico Bass'
    },
    {
      id: 6,
      trip_date: '2025-09-20',
      boat_name: 'Liberty',
      landing_name: 'Fisherman\'s Landing',
      anglers: 35,
      total_catch: 189,
      species: 'Yellowfin Tuna, Dorado'
    },
    {
      id: 7,
      trip_date: '2025-09-20',
      boat_name: 'San Diego',
      landing_name: 'H&M Landing',
      anglers: 30,
      total_catch: 124,
      species: 'Rockfish, Sand Bass, Sculpin'
    },
    {
      id: 8,
      trip_date: '2025-09-19',
      boat_name: 'Excalibur',
      landing_name: 'Seaforth Landing',
      anglers: 18,
      total_catch: 67,
      species: 'Halibut, Sand Bass, Rockfish'
    },
    {
      id: 9,
      trip_date: '2025-09-19',
      boat_name: 'New Lo-An',
      landing_name: 'Point Loma Sportfishing',
      anglers: 25,
      total_catch: 95,
      species: 'Yellowtail, Bonito'
    },
    {
      id: 10,
      trip_date: '2025-09-18',
      boat_name: 'Horizon',
      landing_name: 'H&M Landing',
      anglers: 42,
      total_catch: 234,
      species: 'Bluefin Tuna, Yellowfin Tuna'
    }
  ]
};

// Current filtered data
let currentData = {
  trips: SAMPLE_DATA.trips,
  stats: SAMPLE_DATA.stats,
  landings: SAMPLE_DATA.landings
};

/**
 * Initialize the dashboard
 */
async function initDashboard() {
  console.log('🚀 Starting SD Fishing Intelligence Dashboard (Static Mode)');

  try {
    // Show loading briefly
    showLoading();

    // Simulate loading delay
    await new Promise(resolve => setTimeout(resolve, 500));

    // Render components with sample data
    renderNavigation();
    renderStats();
    renderRecentTrips();

    console.log('✅ Dashboard loaded successfully with sample data');

  } catch (error) {
    console.error('❌ Dashboard initialization failed:', error);
    showError(error.message);
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
      <div class="nav-item hover:bg-accent hover:text-accent-foreground" data-landing-id="${landing.id}">
        <div class="nav-item-content">
          <span class="text-foreground">${landing.name}</span>
          <span class="text-muted-foreground text-xs">${landing.city || ''}</span>
        </div>
      </div>
    `).join('');

  sanDiegoSection.innerHTML = html;

  // Add click handlers
  sanDiegoSection.addEventListener('click', async (e) => {
    const navItem = e.target.closest('.nav-item');
    if (navItem) {
      const landingId = parseInt(navItem.dataset.landingId);
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
          <div class="stat-number">${stats.total_trips.toLocaleString()}</div>
          <div class="stat-label">Total Trips</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${stats.total_anglers.toLocaleString()}</div>
          <div class="stat-label">Total Anglers</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${stats.total_fish.toLocaleString()}</div>
          <div class="stat-label">Fish Caught</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${stats.unique_species}</div>
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

  const tableRows = trips.map(trip => `
    <tr>
      <td class="table-cell">${formatDate(trip.trip_date)}</td>
      <td class="table-cell">${trip.landing_name}</td>
      <td class="table-cell">${trip.boat_name}</td>
      <td class="table-cell">${trip.anglers}</td>
      <td class="table-cell">${trip.total_catch}</td>
      <td class="table-cell max-w-xs truncate" title="${trip.species}">${trip.species}</td>
    </tr>
  `).join('');

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
    // Update active state
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.remove('active');
    });
    document.querySelector(`[data-landing-id="${landingId}"]`)?.classList.add('active');

    // Filter trips by landing
    const landingName = currentData.landings.find(l => l.id === landingId)?.name;
    const filteredTrips = SAMPLE_DATA.trips.filter(trip => trip.landing_name === landingName);

    // Update current data
    currentData.trips = filteredTrips;

    // Calculate filtered stats
    const filteredStats = {
      total_trips: filteredTrips.length,
      total_anglers: filteredTrips.reduce((sum, trip) => sum + trip.anglers, 0),
      total_fish: filteredTrips.reduce((sum, trip) => sum + trip.total_catch, 0),
      unique_species: new Set(filteredTrips.flatMap(trip => trip.species.split(', '))).size
    };
    currentData.stats = filteredStats;

    // Re-render
    renderStats();
    renderRecentTrips();

    console.log(`Filtered by ${landingName}: ${filteredTrips.length} trips`);

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
  filterByLanding
};