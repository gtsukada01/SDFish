import { describe, it, expect, vi, afterEach } from "vitest";

interface WindowLike {
  addEventListener: (type: string, listener: (event: { type: string }) => void) => void;
  dispatchEvent: (event: { type: string }) => void;
}

interface NavigatorLike {
  onLine: boolean;
}

type InstrumentationModule = typeof import("../../scripts/api/instrumentation");

const ORIGINAL_FETCH = globalThis.fetch;
const ORIGINAL_WINDOW = (globalThis as any).window;
const ORIGINAL_NAVIGATOR_DESCRIPTOR = Object.getOwnPropertyDescriptor(globalThis, "navigator");
const listeners = new Map<string, Array<(event: { type: string }) => void>>();

function createWindowMock(): WindowLike {
  listeners.clear();
  return {
    addEventListener(type, listener) {
      const existing = listeners.get(type) ?? [];
      listeners.set(type, [...existing, listener]);
    },
    dispatchEvent(event) {
      const subs = listeners.get(event.type) ?? [];
      for (const listener of subs) {
        listener(event);
      }
    },
  };
}

function setupGlobals() {
  const windowMock = createWindowMock();
  const navigatorMock: NavigatorLike = { onLine: true };
  const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
    void _input;
    void init;
    return {
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => ({}),
    } as unknown as Response;
  });

  Object.defineProperty(globalThis, "window", {
    value: windowMock,
    configurable: true,
  });
  Object.defineProperty(globalThis, "navigator", {
    value: navigatorMock,
    configurable: true,
  });
  Object.defineProperty(globalThis, "fetch", {
    value: fetchMock,
    configurable: true,
    writable: true,
  });

  const infoSpy = vi.spyOn(console, "info").mockImplementation(() => {});
  const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

  return { windowMock, navigatorMock, fetchMock, infoSpy, warnSpy };
}

async function loadModule(): Promise<{
  mod: InstrumentationModule;
  windowMock: WindowLike;
  navigatorMock: NavigatorLike;
  fetchMock: ReturnType<typeof setupGlobals>["fetchMock"];
}> {
  vi.resetModules();
  const { windowMock, navigatorMock, fetchMock } = setupGlobals();
  const mod = await import("../../scripts/api/instrumentation");
  return { mod, windowMock, navigatorMock, fetchMock };
}

afterEach(() => {
  if (ORIGINAL_WINDOW === undefined) {
    delete (globalThis as any).window;
  } else {
    Object.defineProperty(globalThis, "window", {
      value: ORIGINAL_WINDOW,
      configurable: true,
    });
  }

  if (ORIGINAL_NAVIGATOR_DESCRIPTOR) {
    Object.defineProperty(globalThis, "navigator", ORIGINAL_NAVIGATOR_DESCRIPTOR);
  } else {
    delete (globalThis as any).navigator;
  }

  if (ORIGINAL_FETCH) {
    Object.defineProperty(globalThis, "fetch", {
      value: ORIGINAL_FETCH,
      configurable: true,
      writable: true,
    });
  } else {
    delete (globalThis as any).fetch;
  }
  vi.restoreAllMocks();
});

async function waitForMicrotask(): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, 0));
}

describe("instrumentation telemetry", () => {
  it("generates stable filter hashes regardless of key or array order", async () => {
    const { mod } = await loadModule();
    const baseline = mod.hashFilters({
      start_date: "2025-09-01",
      end_date: "2025-09-30",
      species: ["yellowtail", "tuna"],
    });

    const shuffled = mod.hashFilters({
      end_date: "2025-09-30",
      start_date: "2025-09-01",
      species: ["tuna", "yellowtail"],
    });

    expect(shuffled).toBe(baseline);
  });

  it("queues telemetry when offline and flushes once connectivity returns", async () => {
    const { mod, windowMock, navigatorMock, fetchMock } = await loadModule();

    navigatorMock.onLine = false;
    mod.configureTelemetry("https://example.com/hook");

    await mod.emitTelemetry({
      event: "fetch_start",
      endpoint: "catch",
      filters: { start_date: "2025-09-01" },
      timestamp: mod.now(),
    });

    expect(fetchMock).not.toHaveBeenCalled();

    navigatorMock.onLine = true;
    windowMock.dispatchEvent({ type: "online" });
    await waitForMicrotask();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const firstCall = fetchMock.mock.calls[0];
    expect(firstCall?.[0]).toBe("https://example.com/hook");
    const firstBody = JSON.parse((firstCall?.[1]?.body as string) ?? "{}");
    expect(firstBody.event).toBe("fetch_start");
    expect(firstBody.filter_hash).toMatch(/^fh_/);

    fetchMock.mockClear();

    await mod.emitTelemetry({
      event: "fetch_success",
      endpoint: "catch",
      duration_ms: 42,
      timestamp: mod.now(),
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const successBody = JSON.parse((fetchMock.mock.calls[0]?.[1]?.body as string) ?? "{}");
    expect(successBody.event).toBe("fetch_success");
    expect(successBody.filter_hash).toBe(firstBody.filter_hash);
  });
});
