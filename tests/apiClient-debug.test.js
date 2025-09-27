import assert from 'node:assert/strict';

// --- minimal browser-like environment setup ---
const storage = new Map([
  ['debug', '1'],
]);

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

const elements = new Map();
elements.set('debug-close', { addEventListener() {} });
const debugContent = { innerHTML: '' };
elements.set('debug-content', debugContent);
elements.set('debug-overlay', { remove() {} });

const documentStub = {
  getElementById(id) {
    return elements.get(id) || null;
  },
  createElement() {
    const el = {
      style: {},
      children: [],
      _id: null,
      innerHTML: '',
      appendChild(child) {
        this.children.push(child);
      },
      remove() {},
      addEventListener() {},
      set id(value) {
        this._id = value;
        elements.set(value, this);
      },
      get id() {
        return this._id;
      },
    };
    return el;
  },
  body: {
    appendChild(node) {
      if (node && node.id) {
        elements.set(node.id, node);
      }
    },
  },
};

globalThis.document = documentStub;

globalThis.window = {
  location: {
    origin: 'https://prod.example.com',
    hostname: 'prod.example.com',
  },
  performance: {
    now: () => 0,
  },
};

let capturedRequest;

globalThis.fetch = async (url, options = {}) => {
  capturedRequest = { url, options };
  return new Response(
    JSON.stringify({ data: [{ id: 1, name: 'Liberty Trip' }] }),
    {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'X-Request-Id': 'server-123',
      },
    }
  );
};

window.fetch = globalThis.fetch;

const debugModule = await import('../github-deployment/scripts/debug.js');
const apiClient = await import('../github-deployment/scripts/apiClient.js');

// Exercise the instrumented path
const result = await apiClient.fetchFilters('12');

assert.ok(Array.isArray(result.data));
assert.equal(result.data.length, 1);
assert.ok(capturedRequest);
assert.ok(capturedRequest.options.headers['X-Client-Request-Id']);

const state = debugModule.getDebugState();

assert.equal(state.lastRequest.url, '/api/filters?landing=12');
assert.equal(state.lastRequest.params.landing, '12');
assert.equal(state.lastResponse.status, 200);
assert.equal(state.lastResponse.rowCount, 1);
assert.equal(state.lastResponse.serverRequestId, 'server-123');

console.log('API client debug instrumentation test passed');
