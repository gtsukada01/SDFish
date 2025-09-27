import assert from 'node:assert/strict';

// Minimal localStorage mock for StateManager initialization
const storage = new Map();
globalThis.localStorage = {
  getItem(key) {
    return storage.has(key) ? storage.get(key) : null;
  },
  setItem(key, value) {
    storage.set(key, value);
  },
  removeItem(key) {
    storage.delete(key);
  },
};

const { StateManager } = await import('../github-deployment/scripts/state.js');

function runTests() {
  testIncludesServerReadyFilters();
  testOmitsIdsWhenUnknown();
  testRetainsUiValues();
  console.log('All state.getApiFilters diagnostics passed');
}

function testIncludesServerReadyFilters() {
  const manager = new StateManager();

  manager.set('filters.startDate', '2025-08-01');
  manager.set('filters.endDate', '2025-08-31');
  manager.set('filters.boat', 'Liberty');
  manager.set('selectedLanding', '12');
  manager.setBoatMapping({ Liberty: '71' });

  const filters = manager.getApiFilters();

  assert.equal(filters.startDate, '2025-08-01');
  assert.equal(filters.endDate, '2025-08-31');
  assert.equal(filters.boat, 'Liberty');
  assert.equal(filters.boat_id, '71');
  assert.equal(filters.landing_id, '12');
}

function testOmitsIdsWhenUnknown() {
  const manager = new StateManager();

  manager.set('filters.boat', 'Unknown Boat');
  manager.set('selectedLanding', null);

  const filters = manager.getApiFilters();

  assert.equal(filters.boat, 'Unknown Boat');
  assert.ok(!('boat_id' in filters));
  assert.ok(!('landing_id' in filters));
}

function testRetainsUiValues() {
  const manager = new StateManager();

  manager.set('filters.species', 'yellowtail');
  manager.set('filters.duration', 'full-day');

  const filters = manager.getApiFilters();

  assert.equal(filters.species, 'yellowtail');
  assert.equal(filters.duration, 'full-day');
}

runTests();
