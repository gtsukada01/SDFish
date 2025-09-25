/**
 * Stats Card Components - shadcn/ui Card System
 * Provides reusable card components following shadcn design patterns
 */

import { timeRender } from '../performanceMonitor.js';

/**
 * Create a stats card with shadcn Card components
 * @param {Object} cardData - Card configuration object
 * @param {string} cardData.id - Card container ID
 * @param {string} cardData.title - Card title
 * @param {string} cardData.value - Card value/metric
 * @param {string} cardData.icon - Lucide icon name
 * @param {string} cardData.description - Optional description
 * @param {Object} cardData.trend - Optional trend data
 * @returns {string} - HTML string with shadcn classes
 */
export function createStatsCard({ id, title, value, icon, description = null, trend = null }) {
  const trendElement = trend
    ? `<div class="card-trend ${trend.isPositive ? 'card-trend--positive' : 'card-trend--negative'}">
         <i data-lucide="${trend.isPositive ? 'trending-up' : 'trending-down'}" class="card-trend-icon"></i>
         <span>${trend.value}</span>
       </div>`
    : '';

  const descriptionElement = description ? `<p class="card-description">${description}</p>` : '';

  return `
    <div class="card stats-card" id="${id}">
      <div class="card-header stats-card-header">
        <h3 class="card-title">${title}</h3>
      </div>
      <div class="card-content stats-card-content">
        <div class="card-value" id="${id}Value">${value}</div>
        ${trendElement}
        ${descriptionElement}
      </div>
    </div>
  `;
}

/**
 * Create a chart card container with shadcn Card components
 * @param {Object} cardData - Chart card configuration
 * @param {string} cardData.id - Card container ID
 * @param {string} cardData.title - Chart title
 * @param {string} cardData.canvasId - Canvas element ID for chart
 * @param {string} cardData.description - Optional description
 * @returns {string} - HTML string with shadcn classes
 */
export function createChartCard({ id, title, canvasId, description = null }) {
  const descriptionElement = description ? `<p class="chart-description">${description}</p>` : '';

  return `
    <div class="card chart-card" id="${id}">
      <div class="card-header chart-card-header">
        <h3 class="card-title">${title}</h3>
        ${descriptionElement}
      </div>
      <div class="card-content chart-card-content">
        <div class="chart-container">
          <canvas id="${canvasId}"></canvas>
        </div>
      </div>
    </div>
  `;
}

/**
 * Create a loading card state
 * @param {string} id - Card container ID
 * @param {string} title - Card title
 * @returns {string} - HTML string with loading state
 */
export function createLoadingCard(id, title) {
  return `
    <div class="card stats-card" id="${id}">
      <div class="card-header stats-card-header">
        <h3 class="card-title">${title}</h3>
      </div>
      <div class="card-content stats-card-content">
        <div class="loading-state">
          <div class="loading-spinner"></div>
          <span>Loading...</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Create an error card state
 * @param {string} id - Card container ID
 * @param {string} title - Card title
 * @param {string} errorMessage - Error message to display
 * @returns {string} - HTML string with error state
 */
export function createErrorCard(id, title, errorMessage = 'Failed to load data') {
  return `
    <div class="card stats-card stats-card--error" id="${id}">
      <div class="card-header stats-card-header">
        <h3 class="card-title">${title}</h3>
      </div>
      <div class="card-content stats-card-content">
        <div class="card-error">
          <i data-lucide="alert-circle"></i>
          <span>${errorMessage}</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Render stats grid with shadcn Card components
 * @param {Array} statsData - Array of stats card configurations
 * @param {HTMLElement} container - Container element
 */
export function renderStatsGrid(statsData, container) {
  if (!container) {
    console.error('Container element not provided for stats grid');
    return;
  }

  timeRender(() => {
    // Create document fragment for performance
    const fragment = document.createDocumentFragment();

    // Create grid container
    const gridDiv = document.createElement('div');
    gridDiv.className = 'stats-grid';

    statsData.forEach((cardConfig) => {
      const cardDiv = document.createElement('div');
      cardDiv.innerHTML = createStatsCard(cardConfig);
      gridDiv.appendChild(cardDiv.firstElementChild);
    });

    fragment.appendChild(gridDiv);

    container.innerHTML = '';
    container.appendChild(fragment);
  }, 'renderStatsGrid');
}

/**
 * Update stats card value with animation
 * @param {string} cardId - Card ID
 * @param {string} newValue - New value to display
 * @param {boolean} animate - Whether to animate the change
 */
export function updateCardValue(cardId, newValue, animate = true) {
  const valueElement = document.getElementById(`${cardId}Value`);
  if (!valueElement) return;

  if (animate && typeof window !== 'undefined' && window.setTimeout) {
    // Add subtle animation class
    valueElement.classList.add('opacity-50', 'transition-opacity', 'duration-200');

    window.setTimeout(() => {
      valueElement.textContent = newValue;
      valueElement.classList.remove('opacity-50');
    }, 100);
  } else {
    valueElement.textContent = newValue;
  }
}

/**
 * Show loading state for a card
 * @param {string} cardId - Card ID
 * @param {string} title - Card title
 */
export function showCardLoading(cardId, title) {
  const cardElement = document.getElementById(cardId);
  if (cardElement) {
    timeRender(() => {
      cardElement.outerHTML = createLoadingCard(cardId, title);
    }, `showCardLoading:${cardId}`);
  }
}

/**
 * Show error state for a card
 * @param {string} cardId - Card ID
 * @param {string} title - Card title
 * @param {string} errorMessage - Error message
 */
export function showCardError(cardId, title, errorMessage = 'Failed to load data') {
  const cardElement = document.getElementById(cardId);
  if (cardElement) {
    timeRender(() => {
      cardElement.outerHTML = createErrorCard(cardId, title, errorMessage);
    }, `showCardError:${cardId}`);
  }
}

/**
 * Default stats card configurations for the fishing dashboard
 */
export const DEFAULT_STATS_CARDS = [
  {
    id: 'totalTripsCard',
    title: 'Total Trips',
    value: '0',
    icon: 'ship',
  },
  {
    id: 'totalFishCard',
    title: 'Total Fish',
    value: '0',
    icon: 'fish',
  },
  {
    id: 'avgPerTripCard',
    title: 'Avg Per Trip',
    value: '0.0',
    icon: 'trending-up',
  },
  {
    id: 'totalBoatsCard',
    title: 'Total Boats',
    value: '0',
    icon: 'anchor',
  },
];

/**
 * Default chart card configurations
 */
export const DEFAULT_CHART_CARDS = [
  {
    id: 'dailyCatchesCardContainer',
    title: 'Daily Catches',
    canvasId: 'dailyCatchesChart',
  },
  {
    id: 'topBoatsCardContainer',
    title: 'Top Boats',
    canvasId: 'topBoatsChart',
  },
];
