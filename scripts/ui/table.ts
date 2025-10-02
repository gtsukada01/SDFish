import { CatchRecord } from "../api/types";
import { Virtualizer, observeElementRect, observeElementOffset, elementScroll } from "@tanstack/virtual-core";

const COLUMNS: Array<{ key: keyof CatchRecord | "top_species_display"; label: string }> = [
  { key: "trip_date", label: "Date" },
  { key: "boat", label: "Boat" },
  { key: "landing", label: "Landing" },
  { key: "trip_duration_hours", label: "Duration (hrs)" },
  { key: "angler_count", label: "Anglers" },
  { key: "total_fish", label: "Total Fish" },
  { key: "top_species_display", label: "Top Species" },
];

const VIRTUAL_CONTAINER_HEIGHT = 600; // px
const VIRTUAL_ROW_HEIGHT = 48; // px
const VIRTUAL_OVERSCAN = 5; // rows

let currentVirtualizer: Virtualizer<HTMLElement, Element> | null = null;

export function renderCatchTable(container: HTMLElement, records: CatchRecord[]): void {
  container.innerHTML = "";

  // Create scrollable container
  const scrollContainer = document.createElement("div");
  scrollContainer.className = "catch-table-scroll-container";
  scrollContainer.style.height = `${VIRTUAL_CONTAINER_HEIGHT}px`;
  scrollContainer.style.overflow = "auto";
  scrollContainer.style.position = "relative";
  scrollContainer.setAttribute("role", "region");
  scrollContainer.setAttribute("aria-label", "Catch records table");
  scrollContainer.setAttribute("tabindex", "0");

  // Create table
  const table = document.createElement("table");
  table.className = "catch-table";
  table.setAttribute("role", "table");

  // Sticky header
  const thead = document.createElement("thead");
  thead.setAttribute("role", "rowgroup");
  const headerRow = document.createElement("tr");
  headerRow.setAttribute("role", "row");
  COLUMNS.forEach((column) => {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = column.label;
    th.setAttribute("role", "columnheader");
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Virtualized tbody
  const tbody = document.createElement("tbody");
  tbody.setAttribute("role", "rowgroup");
  tbody.style.position = "relative";

  // Initialize virtualizer
  currentVirtualizer = new Virtualizer({
    count: records.length,
    getScrollElement: () => scrollContainer,
    estimateSize: () => VIRTUAL_ROW_HEIGHT,
    overscan: VIRTUAL_OVERSCAN,
    observeElementRect: observeElementRect,
    observeElementOffset: observeElementOffset,
    scrollToFn: elementScroll,
  });

  // Render initial virtual rows
  renderVirtualRows(tbody, records, currentVirtualizer);

  // Subscribe to virtualizer changes
  currentVirtualizer.setOptions({
    onChange: () => {
      if (currentVirtualizer) {
        renderVirtualRows(tbody, records, currentVirtualizer);
      }
    },
  });

  table.appendChild(tbody);
  scrollContainer.appendChild(table);

  // Keyboard navigation
  scrollContainer.addEventListener("keydown", (event) => {
    handleKeyboardNavigation(event, scrollContainer, records.length);
  });

  container.appendChild(scrollContainer);
}

function renderVirtualRows(
  tbody: HTMLElement,
  records: CatchRecord[],
  virtualizer: Virtualizer<HTMLElement, Element>
): void {
  const items = virtualizer.getVirtualItems();

  // Set total size for proper scrolling
  tbody.style.height = `${virtualizer.getTotalSize()}px`;

  // Clear existing rows
  tbody.innerHTML = "";

  // Render visible rows
  items.forEach((virtualRow) => {
    const record = records[virtualRow.index];
    if (!record) return;

    const row = document.createElement("tr");
    row.setAttribute("role", "row");
    row.setAttribute("data-index", String(virtualRow.index));
    row.style.position = "absolute";
    row.style.top = "0";
    row.style.left = "0";
    row.style.width = "100%";
    row.style.transform = `translateY(${virtualRow.start}px)`;
    row.setAttribute("tabindex", "-1");

    COLUMNS.forEach((column) => {
      const td = document.createElement("td");
      td.setAttribute("role", "cell");
      let value: string | number | null = null;
      let isBlank = false;

      if (column.key === "top_species_display") {
        value = record.top_species
          ? `${record.top_species}${record.top_species_count ? ` (${record.top_species_count})` : ""}`
          : "";
        isBlank = !record.top_species;
      } else {
        const raw = record[column.key as keyof CatchRecord];
        value = raw as string | number | null;
        isBlank = value === null || value === undefined || value === "";
      }

      if (isBlank) {
        td.innerHTML = "&nbsp;";
        td.setAttribute("data-blank", "true");
        td.style.background = "rgba(251, 191, 36, 0.1)"; // Subtle yellow indicator
        td.setAttribute("aria-label", `${column.label}: blank`);
      } else {
        td.textContent = String(value);
        td.setAttribute("aria-label", `${column.label}: ${value}`);
      }

      row.appendChild(td);
    });

    tbody.appendChild(row);
  });
}

function handleKeyboardNavigation(
  event: KeyboardEvent,
  scrollContainer: HTMLElement,
  totalRows: number
): void {
  if (!currentVirtualizer) return;

  const currentScrollTop = scrollContainer.scrollTop;
  const visibleRows = Math.floor(VIRTUAL_CONTAINER_HEIGHT / VIRTUAL_ROW_HEIGHT);

  switch (event.key) {
    case "ArrowDown":
      event.preventDefault();
      scrollContainer.scrollTop = Math.min(
        currentScrollTop + VIRTUAL_ROW_HEIGHT,
        (totalRows - visibleRows) * VIRTUAL_ROW_HEIGHT
      );
      break;

    case "ArrowUp":
      event.preventDefault();
      scrollContainer.scrollTop = Math.max(currentScrollTop - VIRTUAL_ROW_HEIGHT, 0);
      break;

    case "PageDown":
      event.preventDefault();
      scrollContainer.scrollTop = Math.min(
        currentScrollTop + VIRTUAL_CONTAINER_HEIGHT,
        (totalRows - visibleRows) * VIRTUAL_ROW_HEIGHT
      );
      break;

    case "PageUp":
      event.preventDefault();
      scrollContainer.scrollTop = Math.max(currentScrollTop - VIRTUAL_CONTAINER_HEIGHT, 0);
      break;

    case "Home":
      event.preventDefault();
      scrollContainer.scrollTop = 0;
      break;

    case "End":
      event.preventDefault();
      scrollContainer.scrollTop = (totalRows - visibleRows) * VIRTUAL_ROW_HEIGHT;
      break;
  }
}

export function cleanupVirtualizer(): void {
  if (currentVirtualizer) {
    currentVirtualizer = null;
  }
}
