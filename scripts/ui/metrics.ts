import { SummaryMetricsResponse } from "../api/types";

export function renderSummaryMetrics(container: HTMLElement, metrics: SummaryMetricsResponse): void {
  container.innerHTML = "";

  // Fleet totals section
  const fleetSection = document.createElement("section");
  fleetSection.className = "metrics-section";
  fleetSection.setAttribute("aria-labelledby", "fleet-heading");

  const fleetHeading = document.createElement("h2");
  fleetHeading.id = "fleet-heading";
  fleetHeading.textContent = "Fleet Summary";
  fleetHeading.className = "metrics-heading";
  fleetSection.appendChild(fleetHeading);

  const fleetGrid = document.createElement("div");
  fleetGrid.className = "summary-grid";
  fleetGrid.setAttribute("role", "list");

  const fleetCards: Array<{ label: string; value: number }> = [
    { label: "Total Trips", value: metrics.fleet.total_trips },
    { label: "Total Fish", value: metrics.fleet.total_fish },
    { label: "Active Boats", value: metrics.fleet.unique_boats },
    { label: "Species", value: metrics.fleet.unique_species },
  ];

  fleetCards.forEach((card) => {
    const cardEl = createMetricCard(card.label, card.value);
    fleetGrid.appendChild(cardEl);
  });

  fleetSection.appendChild(fleetGrid);
  container.appendChild(fleetSection);

  // Per-boat section with toggle
  const perBoatSection = createToggleableSection({
    id: "per-boat",
    heading: "Per-Boat Breakdown",
    defaultExpanded: false,
    data: metrics.per_boat,
    renderContent: (data, contentContainer) => {
      if (data.length === 0) {
        const empty = document.createElement("p");
        empty.className = "metrics-empty";
        empty.textContent = "No boat data available for current filters.";
        contentContainer.appendChild(empty);
        return;
      }

      const table = document.createElement("table");
      table.className = "metrics-table";
      table.setAttribute("role", "table");
      table.setAttribute("aria-label", "Per-boat fishing metrics");

      const thead = document.createElement("thead");
      const headerRow = document.createElement("tr");
      ["Boat", "Trips", "Total Fish", "Top Species", "Top Species Count"].forEach((header) => {
        const th = document.createElement("th");
        th.textContent = header;
        th.setAttribute("role", "columnheader");
        headerRow.appendChild(th);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);

      const tbody = document.createElement("tbody");
      data.forEach((boat) => {
        const row = document.createElement("tr");
        row.setAttribute("role", "row");

        const cells = [
          boat.boat,
          formatNumber(boat.trips),
          formatNumber(boat.total_fish),
          boat.top_species,
          formatNumber(boat.top_species_count),
        ];

        cells.forEach((cellValue) => {
          const td = document.createElement("td");
          td.setAttribute("role", "cell");
          td.textContent = cellValue;
          row.appendChild(td);
        });

        tbody.appendChild(row);
      });
      table.appendChild(tbody);

      contentContainer.appendChild(table);

      // Accessible summary
      const summary = document.createElement("p");
      summary.className = "metrics-summary";
      summary.setAttribute("role", "status");
      summary.setAttribute("aria-live", "polite");
      summary.textContent = `Showing ${data.length} boat${data.length === 1 ? "" : "s"} with a combined total of ${formatNumber(
        data.reduce((sum, b) => sum + b.total_fish, 0)
      )} fish across ${formatNumber(data.reduce((sum, b) => sum + b.trips, 0))} trips.`;
      contentContainer.appendChild(summary);
    },
  });

  container.appendChild(perBoatSection);

  // Per-species section with toggle
  const perSpeciesSection = createToggleableSection({
    id: "per-species",
    heading: "Per-Species Breakdown",
    defaultExpanded: false,
    data: metrics.per_species,
    renderContent: (data, contentContainer) => {
      if (data.length === 0) {
        const empty = document.createElement("p");
        empty.className = "metrics-empty";
        empty.textContent = "No species data available for current filters.";
        contentContainer.appendChild(empty);
        return;
      }

      const table = document.createElement("table");
      table.className = "metrics-table";
      table.setAttribute("role", "table");
      table.setAttribute("aria-label", "Per-species fishing metrics");

      const thead = document.createElement("thead");
      const headerRow = document.createElement("tr");
      ["Species", "Total Fish", "Number of Boats"].forEach((header) => {
        const th = document.createElement("th");
        th.textContent = header;
        th.setAttribute("role", "columnheader");
        headerRow.appendChild(th);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);

      const tbody = document.createElement("tbody");
      data.forEach((species) => {
        const row = document.createElement("tr");
        row.setAttribute("role", "row");

        const cells = [
          species.species,
          formatNumber(species.total_fish),
          formatNumber(species.boats),
        ];

        cells.forEach((cellValue) => {
          const td = document.createElement("td");
          td.setAttribute("role", "cell");
          td.textContent = cellValue;
          row.appendChild(td);
        });

        tbody.appendChild(row);
      });
      table.appendChild(tbody);

      contentContainer.appendChild(table);

      // Accessible summary
      const summary = document.createElement("p");
      summary.className = "metrics-summary";
      summary.setAttribute("role", "status");
      summary.setAttribute("aria-live", "polite");
      summary.textContent = `Showing ${data.length} species with a combined total of ${formatNumber(
        data.reduce((sum, s) => sum + s.total_fish, 0)
      )} fish caught across ${formatNumber(
        data.reduce((sum, s) => sum + s.boats, 0)
      )} unique boat-species combinations.`;
      contentContainer.appendChild(summary);
    },
  });

  container.appendChild(perSpeciesSection);
}

function createMetricCard(label: string, value: number): HTMLElement {
  const cardEl = document.createElement("div");
  cardEl.className = "summary-card";
  cardEl.setAttribute("role", "listitem");

  const labelEl = document.createElement("h3");
  labelEl.textContent = label;
  labelEl.className = "summary-card__label";

  const valueEl = document.createElement("p");
  valueEl.textContent = formatNumber(value);
  valueEl.className = "summary-card__value";
  valueEl.setAttribute("aria-label", `${label}: ${formatNumber(value)}`);

  cardEl.append(labelEl, valueEl);
  return cardEl;
}

interface ToggleableSectionOptions<T> {
  id: string;
  heading: string;
  defaultExpanded: boolean;
  data: T[];
  renderContent: (data: T[], container: HTMLElement) => void;
}

function createToggleableSection<T>(options: ToggleableSectionOptions<T>): HTMLElement {
  const section = document.createElement("section");
  section.className = "metrics-section metrics-section--toggleable";
  section.setAttribute("aria-labelledby", `${options.id}-heading`);

  const header = document.createElement("div");
  header.className = "metrics-section-header";

  const toggleButton = document.createElement("button");
  toggleButton.className = "metrics-toggle";
  toggleButton.setAttribute("type", "button");
  toggleButton.setAttribute("aria-expanded", String(options.defaultExpanded));
  toggleButton.setAttribute("aria-controls", `${options.id}-content`);

  const heading = document.createElement("h2");
  heading.id = `${options.id}-heading`;
  heading.textContent = options.heading;
  heading.className = "metrics-heading";

  const icon = document.createElement("span");
  icon.className = "metrics-toggle-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = options.defaultExpanded ? "▼" : "▶";

  toggleButton.appendChild(icon);
  toggleButton.appendChild(heading);
  header.appendChild(toggleButton);
  section.appendChild(header);

  const content = document.createElement("div");
  content.id = `${options.id}-content`;
  content.className = "metrics-content";
  content.setAttribute("role", "region");
  content.style.display = options.defaultExpanded ? "block" : "none";

  options.renderContent(options.data, content);

  toggleButton.addEventListener("click", () => {
    const isExpanded = toggleButton.getAttribute("aria-expanded") === "true";
    const newExpanded = !isExpanded;

    toggleButton.setAttribute("aria-expanded", String(newExpanded));
    content.style.display = newExpanded ? "block" : "none";
    icon.textContent = newExpanded ? "▼" : "▶";
  });

  section.appendChild(content);
  return section;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(value);
}
