/**
 * Chart Management Module
 * Provides explicit init/destroy APIs for Chart.js instances with shadcn integration
 */

import { Chart } from './externals/chart.js';
import { timeRender } from './performanceMonitor.js';

// Chart instances registry
const chartInstances = new Map();

/**
 * Professional chart color palette following Chart.js best practices
 */
const CHART_COLORS = {
  blue: '#3b82f6',      // Primary data series
  emerald: '#10b981',   // Secondary series
  amber: '#f59e0b',     // Tertiary series
  red: '#ef4444',       // Alert/negative data
  gray: '#6b7280',      // Neutral/comparison data
  // Transparency variations
  blue20: '#3b82f633',  // 20% opacity
  emerald20: '#10b98133',
  blue80: '#3b82f6cc',  // 80% opacity
  gray60: '#6b728099',  // 60% opacity
};

/**
 * Chart configuration defaults with shadcn color scheme
 */
const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top',
      labels: {
        usePointStyle: true,
        padding: 16,
        font: {
          size: 12,
        },
        color: '#1f2937',
      },
    },
    tooltip: {
      backgroundColor: '#ffffff',
      titleColor: '#1f2937',
      bodyColor: '#1f2937',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      cornerRadius: 8,
      displayColors: true,
      usePointStyle: true,
    },
  },
  scales: {
    x: {
      grid: {
        color: '#f3f4f6',
        drawBorder: false,
      },
      ticks: {
        color: '#6b7280',
        font: {
          size: 11,
        },
      },
    },
    y: {
      grid: {
        color: '#f3f4f6',
        drawBorder: false,
      },
      ticks: {
        color: '#6b7280',
        font: {
          size: 11,
        },
      },
    },
  },
};

/**
 * Create or update daily catches chart
 * @param {Object} chartData - Chart data object
 * @param {Array} chartData.labels - Chart labels
 * @param {Array} chartData.fish - Fish count data
 * @param {Array} chartData.trips - Trips count data
 * @returns {Chart} - Chart.js instance
 */
export function createDailyCatchesChart(chartData) {
  const canvasId = 'dailyCatchesChart';
  const canvas = document.getElementById(canvasId);

  if (!canvas) {
    console.error(`Canvas element ${canvasId} not found`);
    return null;
  }

  // Destroy existing chart
  destroyChart(canvasId);

  const config = {
    type: 'line',
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: 'Fish Caught',
          data: chartData.fish,
          borderColor: CHART_COLORS.blue,
          backgroundColor: CHART_COLORS.blue20,
          borderWidth: 2,
          tension: 0.3,
          fill: true,
          pointBackgroundColor: CHART_COLORS.blue,
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          display: false,
        },
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          displayColors: false,
          callbacks: {
            title: function(context) {
              const dataIndex = context[0].dataIndex;
              const date = context[0].label;
              const moonPhase = chartData.moonPhases ? chartData.moonPhases[dataIndex] : null;

              // Get moon phase icon
              const getMoonIcon = (phase) => {
                switch (phase) {
                  case 'New Moon': return '🌑';
                  case 'Waxing Crescent': return '🌒';
                  case 'First Quarter': return '🌓';
                  case 'Waxing Gibbous': return '🌔';
                  case 'Full Moon': return '🌕';
                  case 'Waning Gibbous': return '🌖';
                  case 'Last Quarter': return '🌗';
                  case 'Waning Crescent': return '🌘';
                  default: return '';
                }
              };

              const moonIcon = moonPhase ? getMoonIcon(moonPhase) : '';
              return moonIcon ? `${date} ${moonIcon}` : date;
            },
            afterBody: function(context) {
              const dataIndex = context[0].dataIndex;
              const tripsCount = chartData.trips ? chartData.trips[dataIndex] : 'N/A';
              const moonPhase = chartData.moonPhases ? chartData.moonPhases[dataIndex] : 'N/A';

              const additionalInfo = [`Trips: ${tripsCount}`];
              if (chartData.moonPhases) {
                additionalInfo.push(`Moon Phase: ${moonPhase}`);
              }

              return additionalInfo;
            }
          }
        }
      },
      scales: {
        ...CHART_DEFAULTS.scales,
        y: {
          ...CHART_DEFAULTS.scales.y,
          beginAtZero: true,
          title: {
            display: true,
            text: 'Fish Count',
            color: '#6b7280',
            font: {
              size: 12,
              weight: 500,
            },
          },
        },
      },
    },
  };

  const chart = timeRender(() => {
    const ctx = canvas.getContext('2d');
    return new Chart(ctx, config);
  }, 'createDailyCatchesChart');

  // Register chart instance
  chartInstances.set(canvasId, chart);

  return chart;
}

/**
 * Create or update top boats chart
 * @param {Object} chartData - Chart data object
 * @param {Array} chartData.labels - Boat names
 * @param {Array} chartData.fish - Fish count data
 * @returns {Chart} - Chart.js instance
 */
export function createTopBoatsChart(chartData) {
  const canvasId = 'topBoatsChart';
  const canvas = document.getElementById(canvasId);

  if (!canvas) {
    console.error(`Canvas element ${canvasId} not found`);
    return null;
  }

  // Destroy existing chart
  destroyChart(canvasId);

  const config = {
    type: 'bar',
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: 'Total Fish',
          data: chartData.fish,
          backgroundColor: CHART_COLORS.blue80,
          borderColor: CHART_COLORS.blue,
          borderWidth: 1,
          borderRadius: 4,
          borderSkipped: false,
        },
      ],
    },
    options: {
      ...CHART_DEFAULTS,
      indexAxis: 'y', // Horizontal bar chart
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          display: false,
        },
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {
            label: function (context) {
              return `${context.parsed.x.toLocaleString()} fish`;
            },
          },
        },
      },
      scales: {
        x: {
          ...CHART_DEFAULTS.scales.x,
          beginAtZero: true,
          ticks: {
            ...CHART_DEFAULTS.scales.x.ticks,
            callback: function (value) {
              return value.toLocaleString();
            },
          },
        },
        y: {
          ...CHART_DEFAULTS.scales.y,
          ticks: {
            ...CHART_DEFAULTS.scales.y.ticks,
            autoSkip: false,
          },
          grid: {
            display: false,
          },
        },
      },
    },
  };

  const chart = timeRender(() => {
    const ctx = canvas.getContext('2d');
    return new Chart(ctx, config);
  }, 'createTopBoatsChart');

  // Register chart instance
  chartInstances.set(canvasId, chart);

  return chart;
}

/**
 * Create or update moon phase chart
 * @param {Object} chartData - Chart data object
 * @param {Array} chartData.labels - Moon phase names
 * @param {Array} chartData.fish - Fish count data per moon phase
 * @param {Array} chartData.trips - Trips count data per moon phase
 * @param {Array} chartData.avgPerTrip - Average fish per trip data
 * @returns {Chart} - Chart.js instance
 */
export function createMoonPhaseChart(chartData) {
  const canvasId = 'moonPhaseChart';
  const canvas = document.getElementById(canvasId);

  if (!canvas) {
    console.error(`Canvas element ${canvasId} not found`);
    return null;
  }

  // Destroy existing chart
  destroyChart(canvasId);

  // Create labels with moon phase icons
  const getMoonIcon = (phase) => {
    switch (phase) {
      case 'New Moon': return '🌑';
      case 'Waxing Crescent': return '🌒';
      case 'First Quarter': return '🌓';
      case 'Waxing Gibbous': return '🌔';
      case 'Full Moon': return '🌕';
      case 'Waning Gibbous': return '🌖';
      case 'Last Quarter': return '🌗';
      case 'Waning Crescent': return '🌘';
      default: return '';
    }
  };

  const labelsWithIcons = chartData.labels.map(phase => {
    const icon = getMoonIcon(phase);
    return `${icon} ${phase}`;
  });

  const config = {
    type: 'bar',
    data: {
      labels: labelsWithIcons,
      datasets: [
        {
          label: 'Total Fish Caught',
          data: chartData.fish,
          backgroundColor: CHART_COLORS.blue80,
          borderColor: CHART_COLORS.blue,
          borderWidth: 2,
          borderRadius: 4,
          borderSkipped: false,
        },
      ],
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: {
          display: false,
        },
        tooltip: {
          ...CHART_DEFAULTS.plugins.tooltip,
          callbacks: {
            title: function(context) {
              return `${context[0].label} Phase`;
            },
            afterBody: function(context) {
              const dataIndex = context[0].dataIndex;
              const trips = chartData.trips ? chartData.trips[dataIndex] : 'N/A';
              const avgPerTrip = chartData.avgPerTrip ? chartData.avgPerTrip[dataIndex] : 'N/A';

              return [
                `Total Trips: ${trips.toLocaleString()}`,
                `Average per Trip: ${avgPerTrip} fish`
              ];
            }
          }
        }
      },
      scales: {
        ...CHART_DEFAULTS.scales,
        x: {
          ...CHART_DEFAULTS.scales.x,
          ticks: {
            ...CHART_DEFAULTS.scales.x.ticks,
            maxRotation: 45,
            minRotation: 0,
          },
        },
        y: {
          ...CHART_DEFAULTS.scales.y,
          beginAtZero: true,
          title: {
            display: true,
            text: 'Total Fish Caught',
            color: '#6b7280',
            font: {
              size: 12,
              weight: 500,
            },
          },
          ticks: {
            ...CHART_DEFAULTS.scales.y.ticks,
            callback: function (value) {
              return value.toLocaleString();
            },
          },
        },
      },
    },
  };

  const chart = timeRender(() => {
    const ctx = canvas.getContext('2d');
    return new Chart(ctx, config);
  }, 'createMoonPhaseChart');

  // Register chart instance
  chartInstances.set(canvasId, chart);

  return chart;
}

/**
 * Destroy a specific chart instance
 * @param {string} canvasId - Canvas element ID
 */
export function destroyChart(canvasId) {
  const chart = chartInstances.get(canvasId);
  if (chart) {
    timeRender(() => {
      chart.destroy();
    }, `destroyChart:${canvasId}`);
    chartInstances.delete(canvasId);
  }
}

/**
 * Destroy all chart instances
 */
export function destroyAllCharts() {
  chartInstances.forEach((chart, canvasId) => {
    timeRender(() => {
      chart.destroy();
    }, `destroyChart:${canvasId}`);
  });
  chartInstances.clear();
}

/**
 * Update chart data without recreating the chart
 * @param {string} canvasId - Canvas element ID
 * @param {Object} newData - New chart data
 */
export function updateChartData(canvasId, newData) {
  const chart = chartInstances.get(canvasId);
  if (!chart) return;

  timeRender(() => {
    chart.data = newData;
    chart.update('active');
  }, `updateChartData:${canvasId}`);
}

/**
 * Show chart loading state
 * @param {string} canvasId - Canvas element ID
 */
export function showChartLoading(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const container = canvas.parentElement;
  if (container) {
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className =
      'chart-loading absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm rounded-lg';
    loadingOverlay.innerHTML = `
      <div class="flex items-center space-x-2">
        <div class="loading-spinner w-4 h-4 border-2 border-border border-t-primary rounded-full animate-spin"></div>
        <span class="text-sm text-muted-foreground">Loading chart...</span>
      </div>
    `;

    // Remove existing loading overlay
    const existingOverlay = container.querySelector('.chart-loading');
    if (existingOverlay) {
      existingOverlay.remove();
    }

    container.appendChild(loadingOverlay);
  }
}

/**
 * Hide chart loading state
 * @param {string} canvasId - Canvas element ID
 */
export function hideChartLoading(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const container = canvas.parentElement;
  if (container) {
    const loadingOverlay = container.querySelector('.chart-loading');
    if (loadingOverlay) {
      loadingOverlay.remove();
    }
  }
}

/**
 * Show chart error state
 * @param {string} canvasId - Canvas element ID
 * @param {string} errorMessage - Error message to display
 */
export function showChartError(canvasId, errorMessage = 'Failed to load chart') {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  // Destroy existing chart
  destroyChart(canvasId);

  const container = canvas.parentElement;
  if (container) {
    const errorOverlay = document.createElement('div');
    errorOverlay.className =
      'chart-error absolute inset-0 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm rounded-lg';
    errorOverlay.innerHTML = `
      <div class="flex flex-col items-center space-y-2 text-destructive">
        <i data-lucide="alert-circle" class="w-8 h-8"></i>
        <p class="text-sm text-center max-w-48">${errorMessage}</p>
      </div>
    `;

    // Remove existing overlays
    const existingOverlay = container.querySelector('.chart-loading, .chart-error');
    if (existingOverlay) {
      existingOverlay.remove();
    }

    container.appendChild(errorOverlay);
  }
}

/**
 * Clear chart overlays (loading/error states)
 * @param {string} canvasId - Canvas element ID
 */
export function clearChartOverlays(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const container = canvas.parentElement;
  if (container) {
    const overlays = container.querySelectorAll('.chart-loading, .chart-error');
    overlays.forEach((overlay) => overlay.remove());
  }
}

/**
 * Get chart instance
 * @param {string} canvasId - Canvas element ID
 * @returns {Chart|null} - Chart.js instance or null
 */
export function getChart(canvasId) {
  return chartInstances.get(canvasId) || null;
}

/**
 * Check if chart exists
 * @param {string} canvasId - Canvas element ID
 * @returns {boolean} - Whether chart exists
 */
export function hasChart(canvasId) {
  return chartInstances.has(canvasId);
}

/**
 * Get all chart instances
 * @returns {Map} - Map of canvas IDs to chart instances
 */
export function getAllCharts() {
  return new Map(chartInstances);
}

/**
 * Resize all charts (useful for responsive layouts)
 */
export function resizeAllCharts() {
  chartInstances.forEach((chart) => {
    timeRender(() => {
      chart.resize();
    }, 'resizeChart');
  });
}

/**
 * Chart configuration factory for common chart types
 */
export const ChartFactory = {
  /**
   * Create line chart configuration
   * @param {Object} data - Chart data
   * @param {Object} options - Chart options
   * @returns {Object} - Chart configuration
   */
  createLineChart(data, options = {}) {
    return {
      type: 'line',
      data,
      options: {
        ...CHART_DEFAULTS,
        ...options,
      },
    };
  },

  /**
   * Create bar chart configuration
   * @param {Object} data - Chart data
   * @param {Object} options - Chart options
   * @returns {Object} - Chart configuration
   */
  createBarChart(data, options = {}) {
    return {
      type: 'bar',
      data,
      options: {
        ...CHART_DEFAULTS,
        ...options,
      },
    };
  },

  /**
   * Create doughnut chart configuration
   * @param {Object} data - Chart data
   * @param {Object} options - Chart options
   * @returns {Object} - Chart configuration
   */
  createDoughnutChart(data, options = {}) {
    return {
      type: 'doughnut',
      data,
      options: {
        ...CHART_DEFAULTS,
        ...options,
        scales: undefined, // Doughnut charts don't use scales
      },
    };
  },
};

// Resize observer support for responsive charts
let resizeObserver = null;
let resizeDebounceHandle = null;

function ensureResizeObserver() {
  if (resizeObserver || typeof window === 'undefined' || !window.ResizeObserver) {
    return resizeObserver;
  }

  resizeObserver = new window.ResizeObserver(() => {
    if (chartInstances.size > 0) {
      window.clearTimeout(resizeDebounceHandle);
      resizeDebounceHandle = window.setTimeout(resizeAllCharts, 100);
    }
  });

  return resizeObserver;
}

/**
 * Observe a chart container for responsive resizing
 * @param {string} canvasId - Canvas element ID
 */
export function observeChartContainer(canvasId) {
  const observer = ensureResizeObserver();
  if (!observer) return;

  const canvas = document.getElementById(canvasId);
  if (canvas && canvas.parentElement) {
    observer.observe(canvas.parentElement);
  }
}
