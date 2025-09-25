/**
 * Chart.js CDN Adapter
 * Provides ES module exports for the global Chart library loaded via CDN
 */

// Ensure Chart.js is available globally
if (typeof window.Chart === 'undefined') {
  throw new Error('Chart.js must be loaded via CDN before this adapter module');
}

// Export the Chart constructor
export const Chart = window.Chart;

// Export Chart.js components for direct access
export const {
  ArcElement,
  BarController,
  BarElement,
  BubbleController,
  CategoryScale,
  Decimation,
  DoughnutController,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  LogarithmicScale,
  PieController,
  PointElement,
  PolarAreaController,
  RadarController,
  RadialLinearScale,
  ScatterController,
  TimeScale,
  TimeSeriesScale,
  Title,
  Tooltip,
} = window.Chart;

// Default export
export default window.Chart;

// Helper to create a chart with defaults
export function createChart(ctx, config) {
  return new window.Chart(ctx, config);
}

// Helper to destroy all charts
export function destroyAllCharts() {
  Object.values(window.Chart.instances).forEach((chart) => {
    chart.destroy();
  });
}
