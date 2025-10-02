import { CatchTableResponse } from "../api/types";

const LOAD_MORE_SELECTOR = "[data-load-more]";
const ANNOUNCEMENT_SELECTOR = "[data-progressive-announce]";

export function ensureLoadMoreControl(container: HTMLElement): HTMLButtonElement {
  let control = container.querySelector<HTMLButtonElement>(LOAD_MORE_SELECTOR);
  if (!control) {
    control = document.createElement("button");
    control.type = "button";
    control.dataset.loadMore = "true";
    control.className = "load-more";
    control.textContent = "Load more results";
    control.setAttribute("aria-live", "polite");
    container.appendChild(control);
  }
  return control;
}

function ensureAnnouncementRegion(container: HTMLElement): HTMLElement {
  let region = container.querySelector<HTMLElement>(ANNOUNCEMENT_SELECTOR);
  if (!region) {
    region = document.createElement("div");
    region.dataset.progressiveAnnounce = "true";
    region.className = "visually-hidden";
    region.setAttribute("role", "status");
    region.setAttribute("aria-live", "polite");
    region.setAttribute("aria-atomic", "true");
    container.appendChild(region);
  }
  return region;
}

export function updateProgressiveControl(
  container: HTMLElement,
  response: CatchTableResponse,
  onLoadMore: (cursor: string) => Promise<boolean>,
): void {
  const control = ensureLoadMoreControl(container);
  const announcer = ensureAnnouncementRegion(container);
  const nextCursor = response.pagination.next_cursor ?? null;
  const hasMore = typeof nextCursor === "string" && nextCursor.length > 0;

  // Update control state based on cursor availability
  if (hasMore) {
    control.dataset.nextCursor = nextCursor;
  } else {
    delete control.dataset.nextCursor;
  }

  // Handle exhausted state
  const isExhausted = !hasMore && response.pagination.returned_rows > 0;
  control.disabled = !hasMore;

  if (isExhausted) {
    control.textContent = "All results loaded";
    control.setAttribute("aria-label", `All ${response.pagination.total_rows} results loaded`);
    // Announce completion for screen readers
    announcer.textContent = `All ${response.pagination.total_rows} results have been loaded.`;
  } else if (hasMore) {
    const remaining = response.pagination.total_rows - response.pagination.returned_rows;
    control.textContent = `Load more results (${formatNumber(remaining)} remaining)`;
    control.setAttribute(
      "aria-label",
      `Load more results. ${formatNumber(remaining)} of ${formatNumber(response.pagination.total_rows)} remaining`
    );
  } else {
    control.textContent = "No more results";
    control.setAttribute("aria-label", "No more results available");
  }

  // Attach chunked fetch handler
  control.onclick = async () => {
    const cursor = control.dataset.nextCursor;
    if (!cursor) return;

    // Loading state
    control.disabled = true;
    const originalText = control.textContent ?? "Load more results";
    control.textContent = "Loading more...";
    control.setAttribute("aria-label", "Loading more results, please wait");
    announcer.textContent = "Loading more results...";

    try {
      // Execute chunked fetch via callback
      const moreAvailable = await onLoadMore(cursor);

      if (moreAvailable) {
        // More data available, re-enable control
        control.disabled = false;
        control.textContent = originalText;
        control.setAttribute("aria-label", originalText);
        announcer.textContent = `${response.pagination.limit} more results loaded. Additional results available.`;
      } else {
        // Cursor exhausted, disable permanently
        delete control.dataset.nextCursor;
        control.disabled = true;
        control.textContent = "All results loaded";
        control.setAttribute("aria-label", "All results have been loaded");
        announcer.textContent = `Load complete. All results have been loaded.`;
      }
    } catch (error) {
      // Error state - restore control for retry
      control.disabled = false;
      control.textContent = originalText;
      control.setAttribute("aria-label", `${originalText}. Previous load failed, click to retry`);
      announcer.textContent = "Failed to load more results. Click the button to try again.";
      throw error;
    }
  };
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(value);
}
