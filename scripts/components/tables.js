/**
 * Table Components - shadcn/ui Table System
 * Provides reusable table components following shadcn design patterns
 */

import { timeRender } from '../performanceMonitor.js';

/**
 * Create table with shadcn Table components
 * @param {Object} tableConfig - Table configuration object
 * @param {string} tableConfig.id - Table container ID
 * @param {string} tableConfig.title - Table title
 * @param {Array} tableConfig.columns - Column definitions
 * @param {Array} tableConfig.data - Table data
 * @param {string} tableConfig.emptyMessage - Message for empty state
 * @returns {string} - HTML string with shadcn classes
 */
export function createTable({ id, title, columns, data, emptyMessage = 'No data available' }) {
  const tableHeader = createTableHeader(columns);
  const tableBody =
    data.length > 0
      ? createTableBody(columns, data)
      : createEmptyTableBody(columns.length, emptyMessage);

  return `
    <div class="table-card" id="${id}">
      <div class="table-header">
        <h3>${title}</h3>
      </div>
      <div class="table-content">
        <div class="table-scroll">
          <table class="data-table">
            <thead>
              ${tableHeader}
            </thead>
            <tbody id="${id}Body">
              ${tableBody}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

/**
 * Create table header with shadcn styling
 * @param {Array} columns - Column definitions
 * @returns {string} - HTML string for table header
 */
function createTableHeader(columns) {
  const headerCells = columns
    .map((col) => {
      const alignment = col.align || 'left';
      return `
        <th style="text-align: ${alignment};">
          ${col.header}
        </th>
      `;
    })
    .join('');

  return `<tr>${headerCells}</tr>`;
}

/**
 * Create table body with shadcn styling
 * @param {Array} columns - Column definitions
 * @param {Array} data - Table data
 * @returns {string} - HTML string for table body
 */
function createTableBody(columns, data) {
  return data
    .map((row) => {
      const cells = columns
        .map((col) => {
          const value = col.accessor ? row[col.accessor] : row[col.key];
          const formattedValue = col.formatter ? col.formatter(value, row) : value;
          const alignment = col.align || 'left';

          return `
            <td style="text-align: ${alignment};">
              ${formattedValue}
            </td>
          `;
        })
        .join('');

      return `<tr>${cells}</tr>`;
    })
    .join('');
}

/**
 * Create empty table body state
 * @param {number} columnCount - Number of columns
 * @param {string} message - Empty state message
 * @returns {string} - HTML string for empty state
 */
function createEmptyTableBody(columnCount, message) {
  return `
    <tr>
      <td colspan="${columnCount}" class="table-empty">
        <i data-lucide="inbox"></i>
        <p>${message}</p>
      </td>
    </tr>
  `;
}

/**
 * Create loading table body state
 * @param {number} columnCount - Number of columns
 * @returns {string} - HTML string for loading state
 */
function createLoadingTableBody(columnCount) {
  return `
    <tr>
      <td colspan="${columnCount}" class="table-loading">
        <div class="loading-state">
          <div class="loading-spinner"></div>
          <span>Loading...</span>
        </div>
      </td>
    </tr>
  `;
}

/**
 * Create error table body state
 * @param {number} columnCount - Number of columns
 * @param {string} errorMessage - Error message to display
 * @returns {string} - HTML string for error state
 */
function createErrorTableBody(columnCount, errorMessage = 'Failed to load data') {
  return `
    <tr>
      <td colspan="${columnCount}" class="table-error">
        <div class="card-error">
          <i data-lucide="alert-circle"></i>
          <span>${errorMessage}</span>
        </div>
      </td>
    </tr>
  `;
}

/**
 * Update table body with new data
 * @param {string} tableId - Table container ID
 * @param {Array} columns - Column definitions
 * @param {Array} data - New table data
 * @param {string} emptyMessage - Empty state message
 */
export function updateTableBody(tableId, columns, data, emptyMessage = 'No data available') {
  const tableBody = document.getElementById(`${tableId}Body`);
  if (!tableBody) return;

  timeRender(() => {
    const newBody =
      data.length > 0
        ? createTableBody(columns, data)
        : createEmptyTableBody(columns.length, emptyMessage);

    tableBody.innerHTML = newBody;
  }, `updateTableBody:${tableId}`);
}

/**
 * Show loading state for table
 * @param {string} tableId - Table container ID
 * @param {Array} columns - Column definitions
 */
export function showTableLoading(tableId, columns) {
  const tableBody = document.getElementById(`${tableId}Body`);
  if (tableBody) {
    timeRender(() => {
      tableBody.innerHTML = createLoadingTableBody(columns.length);
    }, `showTableLoading:${tableId}`);
  }
}

/**
 * Show error state for table
 * @param {string} tableId - Table container ID
 * @param {Array} columns - Column definitions
 * @param {string} errorMessage - Error message
 */
export function showTableError(tableId, columns, errorMessage = 'Failed to load data') {
  const tableBody = document.getElementById(`${tableId}Body`);
  if (tableBody) {
    timeRender(() => {
      tableBody.innerHTML = createErrorTableBody(columns.length, errorMessage);
    }, `showTableError:${tableId}`);
  }
}

/**
 * Render complete table with data
 * @param {Object} tableConfig - Complete table configuration
 * @param {HTMLElement} container - Container element
 */
export function renderTable(tableConfig, container) {
  if (!container) {
    console.error('Container element not provided for table');
    return;
  }

  timeRender(() => {
    container.innerHTML = createTable(tableConfig);
  }, `renderTable:${tableConfig.id}`);
}

/**
 * Date formatter for table cells
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date
 */
export function formatDate(dateString) {
  if (!dateString) return '';

  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return dateString;
  }
}

/**
 * Number formatter for table cells
 * @param {number} value - Numeric value
 * @param {number} decimals - Number of decimal places
 * @returns {string} - Formatted number
 */
export function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined) return '';

  try {
    return Number(value).toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  } catch {
    return value.toString();
  }
}

/**
 * Badge formatter for table cells
 * @param {string} text - Badge text
 * @param {string} variant - Badge variant (default, secondary, destructive, outline)
 * @returns {string} - HTML for badge
 */
export function formatBadge(text, variant = 'default') {
  const variantClass =
    {
      default: 'badge--default',
      secondary: 'badge--secondary',
      destructive: 'badge--destructive',
      outline: 'badge--outline',
    }[variant] || 'badge--default';

  return `<span class="badge ${variantClass}">${text}</span>`;
}

/**
 * Default column configuration for fishing trips table
 */
export const TRIPS_TABLE_COLUMNS = [
  {
    key: 'date',
    header: 'Date',
    align: 'left',
    formatter: formatDate,
  },
  {
    key: 'boat',
    header: 'Boat',
    align: 'left',
  },
  {
    key: 'landing',
    header: 'Landing',
    align: 'left',
  },
  {
    key: 'duration',
    header: 'Duration',
    align: 'left',
  },
  {
    key: 'anglers',
    header: 'Anglers',
    align: 'center',
    formatter: (value) => formatNumber(value),
  },
  {
    key: 'fishCount',
    header: 'Fish',
    align: 'center',
    formatter: (value) => formatNumber(value),
  },
  {
    key: 'topSpecies',
    header: 'Top Species',
    align: 'left',
    formatter: (value) => value || 'N/A',
  },
];

/**
 * Default table configuration for recent trips
 */
export const DEFAULT_TRIPS_TABLE_CONFIG = {
  id: 'recentTripsTable',
  title: 'Recent Trips',
  columns: TRIPS_TABLE_COLUMNS,
  data: [],
  emptyMessage: 'No recent trips found',
};
