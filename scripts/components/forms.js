/**
 * Form Components - shadcn/ui Input and Select System
 * Provides reusable form components following shadcn design patterns
 */

import { timeRender } from '../performanceMonitor.js';

/**
 * Create shadcn Select component
 * @param {Object} selectConfig - Select configuration object
 * @param {string} selectConfig.id - Select element ID
 * @param {string} selectConfig.name - Select name attribute
 * @param {Array} selectConfig.options - Options array
 * @param {string} selectConfig.defaultValue - Default selected value
 * @param {string} selectConfig.placeholder - Placeholder text
 * @param {string} selectConfig.label - Label text (optional)
 * @param {boolean} selectConfig.required - Required field
 * @returns {string} - HTML string with shadcn classes
 */
export function createSelect({
  id,
  name,
  options,
  defaultValue = 'all',
  placeholder = 'Select option',
  label = null,
  required = false,
}) {
  const labelElement = label
    ? `<label for="${id}" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 mb-2 block">
         ${label}${required ? '<span class="text-destructive ml-1">*</span>' : ''}
       </label>`
    : '';

  const optionsHtml = options
    .map((option) => {
      const value = typeof option === 'object' ? option.value : option;
      const text = typeof option === 'object' ? option.label : option;
      const selected = value === defaultValue ? 'selected' : '';

      return `<option value="${value}" ${selected}>${text}</option>`;
    })
    .join('');

  return `
    <div class="form-field space-y-2">
      ${labelElement}
      <select
        id="${id}"
        name="${name}"
        class="filter-select flex h-9 w-full items-center rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        ${required ? 'required' : ''}
        aria-label="${label || placeholder}"
      >
        ${optionsHtml}
      </select>
    </div>
  `;
}

/**
 * Create shadcn Input component
 * @param {Object} inputConfig - Input configuration object
 * @param {string} inputConfig.id - Input element ID
 * @param {string} inputConfig.name - Input name attribute
 * @param {string} inputConfig.type - Input type
 * @param {string} inputConfig.value - Input value
 * @param {string} inputConfig.placeholder - Placeholder text
 * @param {string} inputConfig.label - Label text (optional)
 * @param {boolean} inputConfig.required - Required field
 * @returns {string} - HTML string with shadcn classes
 */
export function createInput({
  id,
  name,
  type = 'text',
  value = '',
  placeholder = '',
  label = null,
  required = false,
}) {
  const labelElement = label
    ? `<label for="${id}" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 mb-2 block">
         ${label}${required ? '<span class="text-destructive ml-1">*</span>' : ''}
       </label>`
    : '';

  return `
    <div class="form-field space-y-2">
      ${labelElement}
      <input
        id="${id}"
        name="${name}"
        type="${type}"
        value="${value}"
        placeholder="${placeholder}"
        class="filter-select flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        ${required ? 'required' : ''}
        aria-label="${label || placeholder}"
      />
    </div>
  `;
}

/**
 * Create shadcn Button component
 * @param {Object} buttonConfig - Button configuration object
 * @param {string} buttonConfig.id - Button element ID
 * @param {string} buttonConfig.text - Button text
 * @param {string} buttonConfig.variant - Button variant (default, destructive, outline, secondary, ghost, link)
 * @param {string} buttonConfig.size - Button size (default, sm, lg, icon)
 * @param {string} buttonConfig.type - Button type
 * @param {boolean} buttonConfig.disabled - Disabled state
 * @param {string} buttonConfig.icon - Lucide icon name (optional)
 * @returns {string} - HTML string with shadcn classes
 */
export function createButton({
  id,
  text,
  variant = 'default',
  size = 'default',
  type = 'button',
  disabled = false,
  icon = null,
}) {
  const variantClasses = {
    default: 'bg-primary text-primary-foreground shadow hover:bg-primary/90',
    destructive: 'bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90',
    outline:
      'border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground',
    secondary: 'bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80',
    ghost: 'hover:bg-accent hover:text-accent-foreground',
    link: 'text-primary underline-offset-4 hover:underline',
  };

  const sizeClasses = {
    default: 'h-9 px-4 py-2',
    sm: 'h-8 rounded-md px-3 text-xs',
    lg: 'h-10 rounded-md px-8',
    icon: 'h-9 w-9',
  };

  const baseClasses =
    'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50';
  const variantClass = variantClasses[variant] || variantClasses.default;
  const sizeClass = sizeClasses[size] || sizeClasses.default;

  const iconElement = icon
    ? `<i data-lucide="${icon}" class="w-4 h-4 ${text ? 'mr-2' : ''}"></i>`
    : '';

  return `
    <button
      id="${id}"
      type="${type}"
      class="${baseClasses} ${variantClass} ${sizeClass}"
      ${disabled ? 'disabled' : ''}
    >
      ${iconElement}${text}
    </button>
  `;
}

/**
 * Create date range picker with shadcn styling
 * @param {Object} dateRangeConfig - Date range configuration
 * @param {string} dateRangeConfig.startId - Start date input ID
 * @param {string} dateRangeConfig.endId - End date input ID
 * @param {string} dateRangeConfig.startValue - Start date value
 * @param {string} dateRangeConfig.endValue - End date value
 * @param {string} dateRangeConfig.label - Label text
 * @returns {string} - HTML string with shadcn classes
 */
export function createDateRangePicker({
  startId,
  endId,
  startValue = '',
  endValue = '',
  label = 'Date Range',
}) {
  return `
    <div class="form-field space-y-2">
      <div class="flex items-center space-x-2">
        <input
          id="${startId}"
          type="date"
          value="${startValue}"
          class="filter-select flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Start date"
        />
        <span class="text-muted-foreground px-2">to</span>
        <input
          id="${endId}"
          type="date"
          value="${endValue}"
          class="filter-select flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="End date"
        />
      </div>
    </div>
  `;
}

/**
 * Create form group with shadcn styling
 * @param {Object} groupConfig - Form group configuration
 * @param {string} groupConfig.title - Group title
 * @param {Array} groupConfig.fields - Array of field HTML strings
 * @param {string} groupConfig.className - Additional CSS classes
 * @returns {string} - HTML string with shadcn classes
 */
export function createFormGroup({ title, fields, className = '' }) {
  const fieldsHtml = fields.join('');

  return `
    <div class="form-group space-y-4 ${className}">
      ${title ? `<h4 class="text-sm font-medium text-foreground mb-3">${title}</h4>` : ''}
      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        ${fieldsHtml}
      </div>
    </div>
  `;
}

/**
 * Update select options dynamically
 * @param {string} selectId - Select element ID
 * @param {Array} options - New options array
 * @param {string} defaultValue - Value to select
 * @param {string} defaultLabel - Default option label
 */
export function updateSelectOptions(
  selectId,
  options,
  defaultValue = 'all',
  defaultLabel = 'All Options'
) {
  const select = document.getElementById(selectId);
  if (!select) return;

  timeRender(() => {
    const currentValue = select.value;

    // Create options HTML
    const optionsHtml = [`<option value="all">${defaultLabel}</option>`]
      .concat(
        options.map((option) => {
          const value = typeof option === 'object' ? option.value : option;
          const text = typeof option === 'object' ? option.label : option;
          return `<option value="${value}">${text}</option>`;
        })
      )
      .join('');

    select.innerHTML = optionsHtml;

    // Restore previous selection if still available
    if (options.some((opt) => (typeof opt === 'object' ? opt.value : opt) === currentValue)) {
      select.value = currentValue;
    } else {
      select.value = defaultValue;
    }
  }, `updateSelectOptions:${selectId}`);
}

/**
 * Show loading state for select
 * @param {string} selectId - Select element ID
 * @param {string} loadingText - Loading message
 */
export function showSelectLoading(selectId, loadingText = 'Loading...') {
  const select = document.getElementById(selectId);
  if (select) {
    const originalValue = select.value;
    select.innerHTML = `<option value="${originalValue}">${loadingText}</option>`;
    select.disabled = true;
  }
}

/**
 * Show error state for select
 * @param {string} selectId - Select element ID
 * @param {string} errorText - Error message
 */
export function showSelectError(selectId, errorText = 'Error loading options') {
  const select = document.getElementById(selectId);
  if (select) {
    select.innerHTML = `<option value="all">${errorText}</option>`;
    select.disabled = true;
    select.classList.add('border-destructive');
  }
}

/**
 * Clear select error state
 * @param {string} selectId - Select element ID
 */
export function clearSelectError(selectId) {
  const select = document.getElementById(selectId);
  if (select) {
    select.disabled = false;
    select.classList.remove('border-destructive');
  }
}

/**
 * Add form validation
 * @param {string} formId - Form element ID
 * @param {Object} validationRules - Validation rules object
 * @returns {Function} - Validation function
 */
export function addFormValidation(formId, validationRules) {
  const form = document.getElementById(formId);
  if (!form) return () => true;

  const validate = () => {
    let isValid = true;
    const errors = {};

    Object.entries(validationRules).forEach(([fieldId, rules]) => {
      const field = document.getElementById(fieldId);
      if (!field) return;

      const value = field.value.trim();
      const fieldErrors = [];

      // Check required
      if (rules.required && !value) {
        fieldErrors.push('This field is required');
      }

      // Check custom validators
      if (rules.validators && value) {
        rules.validators.forEach((validator) => {
          if (!validator.fn(value)) {
            fieldErrors.push(validator.message);
          }
        });
      }

      if (fieldErrors.length > 0) {
        isValid = false;
        errors[fieldId] = fieldErrors;
        showFieldError(fieldId, fieldErrors[0]);
      } else {
        clearFieldError(fieldId);
      }
    });

    return { isValid, errors };
  };

  // Add event listeners
  Object.keys(validationRules).forEach((fieldId) => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.addEventListener('blur', validate);
      field.addEventListener('input', () => clearFieldError(fieldId));
    }
  });

  return validate;
}

/**
 * Show field error
 * @param {string} fieldId - Field element ID
 * @param {string} errorMessage - Error message
 */
function showFieldError(fieldId, errorMessage) {
  const field = document.getElementById(fieldId);
  if (!field) return;

  // Add error styling
  field.classList.add('border-destructive');

  // Remove existing error message
  const existingError = field.parentNode.querySelector('.field-error');
  if (existingError) {
    existingError.remove();
  }

  // Add error message
  const errorElement = document.createElement('p');
  errorElement.className = 'field-error text-sm text-destructive mt-1';
  errorElement.textContent = errorMessage;
  field.parentNode.appendChild(errorElement);
}

/**
 * Clear field error
 * @param {string} fieldId - Field element ID
 */
function clearFieldError(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) return;

  field.classList.remove('border-destructive');
  const errorElement = field.parentNode.querySelector('.field-error');
  if (errorElement) {
    errorElement.remove();
  }
}

/**
 * Default filter form configuration for fishing dashboard
 */
export const DEFAULT_FILTER_CONFIG = {
  species: {
    id: 'speciesFilter',
    name: 'species',
    options: [],
    defaultValue: 'all',
    placeholder: 'All Species',
  },
  duration: {
    id: 'durationFilter',
    name: 'duration',
    options: [],
    defaultValue: 'all',
    placeholder: 'All Durations',
  },
  boat: {
    id: 'boatFilter',
    name: 'boat',
    options: [],
    defaultValue: 'all',
    placeholder: 'All Boats',
  },
};
