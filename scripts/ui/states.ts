type StateKind = "loading" | "error" | "empty";

const ANNOUNCEMENT_RULES: Record<StateKind, { role: string; ariaLive: "polite" | "assertive" }> = {
  loading: { role: "status", ariaLive: "polite" },
  error: { role: "alert", ariaLive: "assertive" },
  empty: { role: "status", ariaLive: "polite" },
};

interface StateOptions {
  onRetry?: () => void;
  onTelemetry?: (event: TelemetryEvent) => void;
}

interface TelemetryEvent {
  type: "state_render";
  state: StateKind;
  message: string;
  timestamp: string;
  container_id?: string;
}

function emitTelemetry(kind: StateKind, message: string, container: HTMLElement, onTelemetry?: (event: TelemetryEvent) => void) {
  if (!onTelemetry) return;

  const event: TelemetryEvent = {
    type: "state_render",
    state: kind,
    message,
    timestamp: new Date().toISOString(),
    container_id: container.id || undefined,
  };

  onTelemetry(event);
}

function renderState(container: HTMLElement, kind: StateKind, message: string, options: StateOptions = {}) {
  const state = document.createElement("div");
  const { role, ariaLive } = ANNOUNCEMENT_RULES[kind];

  state.className = `state state--${kind}`;
  state.setAttribute("role", role);
  state.setAttribute("aria-live", ariaLive);
  state.setAttribute("aria-atomic", "true");

  // Create message container
  const messageEl = document.createElement("p");
  messageEl.className = "state__message";
  messageEl.textContent = message;
  state.appendChild(messageEl);

  // Add retry button for error states
  if (kind === "error" && options.onRetry) {
    const retryButton = document.createElement("button");
    retryButton.type = "button";
    retryButton.className = "state__retry";
    retryButton.textContent = "Retry";
    retryButton.setAttribute("aria-label", "Retry loading data");

    retryButton.onclick = () => {
      options.onRetry!();
    };

    state.appendChild(retryButton);
  }

  // Add clear filter button for empty states
  if (kind === "empty" && options.onRetry) {
    const clearButton = document.createElement("button");
    clearButton.type = "button";
    clearButton.className = "state__retry";
    clearButton.textContent = "Clear Filters";
    clearButton.setAttribute("aria-label", "Clear all filters and show all results");

    clearButton.onclick = () => {
      options.onRetry!();
    };

    state.appendChild(clearButton);
  }

  container.innerHTML = "";
  container.appendChild(state);

  // Emit telemetry after render
  emitTelemetry(kind, message, container, options.onTelemetry);
}

export function setLoading(container: HTMLElement, message = "Loading data...", options: StateOptions = {}) {
  renderState(container, "loading", message, options);
}

export function setError(container: HTMLElement, message: string, options: StateOptions = {}) {
  renderState(container, "error", message, options);
}

export function setEmpty(container: HTMLElement, message = "No results. Try adjusting filters.", options: StateOptions = {}) {
  renderState(container, "empty", message, options);
}

export function clearState(container: HTMLElement) {
  container.innerHTML = "";
}
