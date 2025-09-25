/**
 * Lucide Icons CDN Adapter
 * Provides ES module exports for the global Lucide library loaded via CDN
 */

// Ensure Lucide is available globally
if (typeof window.lucide === 'undefined') {
  throw new Error('Lucide must be loaded via CDN before this adapter module');
}

// Export the main createIcons function
export const createIcons = window.lucide.createIcons;

// Export commonly used icon utilities
export const icons = window.lucide.icons;

// Default export for convenience
export default {
  createIcons: window.lucide.createIcons,
  icons: window.lucide.icons,
};

// Helper to initialize icons with specific options
export function initializeLucideIcons(options = {}) {
  const defaultOptions = {
    nameAttr: 'data-lucide',
    attrs: {},
  };
  window.lucide.createIcons({ ...defaultOptions, ...options });
}
