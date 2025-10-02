import { Filters } from "./types";

interface BaseEvent {
  endpoint: "catch" | "metrics" | "status";
  timestamp: string;
  filter_hash?: string;
}

interface FetchStartEvent extends BaseEvent {
  event: "fetch_start";
  filters: Partial<Filters>;
}

interface FetchSuccessEvent extends BaseEvent {
  event: "fetch_success";
  duration_ms: number;
  rows_returned?: number;
}

interface FetchErrorEvent extends BaseEvent {
  event: "fetch_error";
  duration_ms?: number;
  error_code: string;
  message: string;
}

interface BlankFieldEvent {
  event: "blank_field_detected";
  record_id: string;
  fields: string[];
  timestamp: string;
}

type TelemetryEvent =
  | FetchStartEvent
  | FetchSuccessEvent
  | FetchErrorEvent
  | BlankFieldEvent;

type EnrichedTelemetryEvent = TelemetryEvent & { filter_hash?: string };

let telemetryEndpoint: string | null = null;
const telemetryQueue: EnrichedTelemetryEvent[] = [];
let flushingQueue = false;
const lastFilterHashByEndpoint: Partial<Record<BaseEvent["endpoint"], string>> = {};

if (typeof window !== "undefined" && typeof window.addEventListener === "function") {
  window.addEventListener("online", () => {
    void flushTelemetryQueue();
  });
}

export function configureTelemetry(endpoint: string | null): void {
  telemetryEndpoint = endpoint && endpoint.length > 0 ? endpoint : null;
  if (telemetryEndpoint) {
    void flushTelemetryQueue();
  }
}

export async function emitTelemetry(event: TelemetryEvent): Promise<void> {
  const enriched = enrichTelemetryEvent(event);

  // Always echo to console for developer ergonomics.
  // eslint-disable-next-line no-console
  console.info(`[telemetry]`, enriched);

  if (!shouldPostTelemetry()) {
    return;
  }

  if (!isBrowserOnline()) {
    queueTelemetry(enriched);
    return;
  }

  try {
    await postTelemetry(enriched);
  } catch (error) {
    queueTelemetry(enriched);
    // eslint-disable-next-line no-console
    console.warn(`[telemetry] failed to post event`, error);
    void flushTelemetryQueue();
  }
}

export function detectBlankFields(record: Record<string, unknown>, keys: readonly string[]): string[] {
  return keys
    .filter((key) => {
      const value = record[key];
      return value === null || value === undefined || value === "";
    })
    .map((key) => String(key));
}

export async function logBlankFields(recordId: string, fields: string[]): Promise<void> {
  if (fields.length === 0) return;
  await emitTelemetry({
    event: "blank_field_detected",
    record_id: recordId,
    fields,
    timestamp: new Date().toISOString(),
  });
}

export function now(): string {
  return new Date().toISOString();
}

export function hashFilters(filters: Partial<Filters>): string {
  const normalized = normalizeForHash(filters);
  const serialized = JSON.stringify(normalized);
  return `fh_${fnv1a(serialized)}`;
}

function enrichTelemetryEvent(event: TelemetryEvent): EnrichedTelemetryEvent {
  if (event.event === "fetch_start") {
    const hash = hashFilters(event.filters ?? {});
    lastFilterHashByEndpoint[event.endpoint] = hash;
    return { ...event, filter_hash: hash };
  }

  if ((event.event === "fetch_success" || event.event === "fetch_error") && !event.filter_hash) {
    const hash = lastFilterHashByEndpoint[event.endpoint];
    return hash ? { ...event, filter_hash: hash } : event;
  }

  return event;
}

function shouldPostTelemetry(): boolean {
  return Boolean(telemetryEndpoint && typeof fetch === "function");
}

function isBrowserOnline(): boolean {
  if (typeof navigator === "undefined" || typeof navigator.onLine !== "boolean") {
    return true;
  }
  return navigator.onLine;
}

async function postTelemetry(event: EnrichedTelemetryEvent): Promise<void> {
  if (!telemetryEndpoint) return;
  await fetch(telemetryEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event),
  });
}

function queueTelemetry(event: EnrichedTelemetryEvent): void {
  telemetryQueue.push(event);
}

async function flushTelemetryQueue(): Promise<void> {
  if (flushingQueue || telemetryQueue.length === 0) {
    return;
  }

  if (!shouldPostTelemetry() || !isBrowserOnline()) {
    return;
  }

  flushingQueue = true;
  try {
    while (telemetryQueue.length > 0 && shouldPostTelemetry() && isBrowserOnline()) {
      const next = telemetryQueue[0];
      try {
        await postTelemetry(next);
        telemetryQueue.shift();
      } catch (error) {
        // eslint-disable-next-line no-console
        console.warn(`[telemetry] failed to flush queued event`, error);
        break;
      }
    }
  } finally {
    flushingQueue = false;
  }
}

function normalizeForHash(filters: Partial<Filters>): Record<string, unknown> {
  const entries = Object.entries(filters ?? {}).filter(([, value]) => value !== undefined);
  entries.sort(([a], [b]) => a.localeCompare(b));
  const normalized: Record<string, unknown> = {};

  for (const [key, value] of entries) {
    if (Array.isArray(value)) {
      normalized[key] = [...value].sort();
    } else {
      normalized[key] = value;
    }
  }

  return normalized;
}

function fnv1a(value: string): string {
  let hash = 0x811c9dc5;
  for (let i = 0; i < value.length; i += 1) {
    hash ^= value.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}
