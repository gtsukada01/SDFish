import { Filters } from "../api/types";

export const FILTER_CHANGE_EVENT = "filters:change" as const;

export type FilterChangeReason = "user" | "reset" | "sync";

export interface FilterChangeDetail {
  filters: Filters;
  reason: FilterChangeReason;
}

export type FilterChangeEvent = CustomEvent<FilterChangeDetail>;

export interface FilterCollections {
  landings: readonly string[];
  boats: readonly string[];
  species: readonly string[];
}

export interface FiltersPanelConfig {
  initialFilters: Filters;
  options: FilterCollections;
}

export interface FiltersPanelController {
  setFilters(next: Filters, reason?: FilterChangeReason, options?: { updateBaseline?: boolean }): void;
  setOptions(collections: FilterCollections): void;
  destroy(): void;
}

let instanceCounter = 0;

export function createFiltersPanel(
  container: HTMLElement,
  config: FiltersPanelConfig,
): FiltersPanelController {
  instanceCounter += 1;
  const instanceId = `filters-${instanceCounter}`;
  const form = document.createElement("form");
  form.className = "filters-form";

  const startField = buildDateField({
    id: `${instanceId}-start-date`,
    label: "Start Date",
  });
  const endField = buildDateField({
    id: `${instanceId}-end-date`,
    label: "End Date",
  });

  const landingField = buildSelectField({
    id: `${instanceId}-landing`,
    label: "Landing",
    placeholder: "All landings",
  });

  const boatField = buildSelectField({
    id: `${instanceId}-boat`,
    label: "Boat",
    placeholder: "All boats",
  });

  const speciesField = buildMultiSelectField({
    id: `${instanceId}-species`,
    label: "Species",
    placeholder: "All species",
  });

  const resetButton = document.createElement("button");
  resetButton.type = "button";
  resetButton.className = "filters-reset";
  resetButton.textContent = "Reset";

  const actions = document.createElement("div");
  actions.className = "filters-actions";
  actions.appendChild(resetButton);

  form.append(
    startField.field,
    endField.field,
    landingField.field,
    boatField.field,
    speciesField.field,
    actions,
  );

  container.innerHTML = "";
  container.appendChild(form);

  let resetBaseline = cloneFilters(config.initialFilters);

  function emitChange(next: Filters, reason: FilterChangeReason) {
    const detail: FilterChangeDetail = { filters: { ...next }, reason };
    const event: FilterChangeEvent = new CustomEvent(FILTER_CHANGE_EVENT, {
      detail,
      bubbles: false,
    });
    container.dispatchEvent(event);
  }

  function readFiltersFromForm(): Filters {
    const filters: Filters = {
      start_date: startField.input.value,
      end_date: endField.input.value,
    };

    const landing = landingField.select.value;
    if (landing) {
      filters.landing = landing;
    }

    const boat = boatField.select.value;
    if (boat) {
      filters.boat = boat;
    }

    const selectedSpecies = Array.from(speciesField.select.selectedOptions)
      .map((option) => option.value)
      .filter((value) => value.length > 0);
    if (selectedSpecies.length > 0) {
      filters.species = selectedSpecies;
    }

    return filters;
  }

  function handleInput() {
    emitChange(readFiltersFromForm(), "user");
  }

  form.addEventListener("change", handleInput);
  startField.input.addEventListener("input", handleInput);
  endField.input.addEventListener("input", handleInput);
  speciesField.select.addEventListener("input", handleInput);

  resetButton.addEventListener("click", () => {
    controller.setFilters(resetBaseline, "reset");
  });

  const controller: FiltersPanelController = {
    setFilters(next, reason = "sync", options) {
      const snapshot = cloneFilters(next);

      setDateValue(startField.input, snapshot.start_date);
      setDateValue(endField.input, snapshot.end_date);

      setSingleSelectValue(landingField.select, snapshot.landing ?? null);
      setSingleSelectValue(boatField.select, snapshot.boat ?? null);

      setMultiSelectValues(speciesField.select, snapshot.species ?? []);

      if (options?.updateBaseline) {
        resetBaseline = snapshot;
      }

      if (reason !== "sync") {
        emitChange(snapshot, reason);
      }
    },
    setOptions(collections) {
      populateSelect(landingField.select, collections.landings, landingField.placeholder);
      populateSelect(boatField.select, collections.boats, boatField.placeholder);
      populateMultiSelect(speciesField.select, collections.species);
    },
    destroy() {
      form.removeEventListener("change", handleInput);
      startField.input.removeEventListener("input", handleInput);
      endField.input.removeEventListener("input", handleInput);
      speciesField.select.removeEventListener("input", handleInput);
      resetButton.remove();
      container.innerHTML = "";
    },
  };

  controller.setOptions(config.options);
  controller.setFilters(resetBaseline, "sync", { updateBaseline: true });

  return controller;
}

function buildDateField({ id, label }: { id: string; label: string }) {
  const field = document.createElement("div");
  field.className = "filters-field";

  const labelEl = document.createElement("label");
  labelEl.className = "filters-label";
  labelEl.htmlFor = id;
  labelEl.textContent = label;

  const input = document.createElement("input");
  input.type = "date";
  input.id = id;
  input.className = "filters-input";

  field.append(labelEl, input);

  return { field, input };
}

function buildSelectField({
  id,
  label,
  placeholder,
}: {
  id: string;
  label: string;
  placeholder: string;
}) {
  const field = document.createElement("div");
  field.className = "filters-field";

  const labelEl = document.createElement("label");
  labelEl.className = "filters-label";
  labelEl.htmlFor = id;
  labelEl.textContent = label;

  const select = document.createElement("select");
  select.id = id;
  select.className = "filters-select";

  field.append(labelEl, select);

  return { field, select, placeholder };
}

function buildMultiSelectField({
  id,
  label,
  placeholder,
}: {
  id: string;
  label: string;
  placeholder: string;
}) {
  const field = document.createElement("div");
  field.className = "filters-field filters-field--multiselect";

  const labelEl = document.createElement("label");
  labelEl.className = "filters-label";
  labelEl.htmlFor = id;
  labelEl.textContent = label;

  const select = document.createElement("select");
  select.id = id;
  select.multiple = true;
  select.className = "filters-select filters-select--multi";

  const hint = document.createElement("div");
  hint.className = "filters-hint";
  hint.textContent = placeholder;

  field.append(labelEl, select, hint);

  return { field, select, placeholder };
}

function populateSelect(select: HTMLSelectElement, options: readonly string[], placeholder: string) {
  const previousValue = select.value;
  select.innerHTML = "";

  const emptyOption = document.createElement("option");
  emptyOption.value = "";
  emptyOption.textContent = placeholder;
  select.appendChild(emptyOption);

  options.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });

  const hasPrevious = options.includes(previousValue);
  if (previousValue && hasPrevious) {
    select.value = previousValue;
  } else {
    select.value = "";
  }
}

function populateMultiSelect(select: HTMLSelectElement, options: readonly string[]) {
  const previousValues = new Set(
    Array.from(select.selectedOptions).map((option) => option.value),
  );
  select.innerHTML = "";

  options.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    if (previousValues.has(value)) {
      option.selected = true;
    }
    select.appendChild(option);
  });
}

function setDateValue(input: HTMLInputElement, value: string) {
  input.value = value;
}

function setSingleSelectValue(select: HTMLSelectElement, value: string | null) {
  select.value = value ?? "";
}

function setMultiSelectValues(select: HTMLSelectElement, values: readonly string[]) {
  const lookup = new Set(values);
  Array.from(select.options).forEach((option) => {
    option.selected = lookup.has(option.value);
  });
}

function cloneFilters(filters: Filters): Filters {
  const snapshot: Filters = {
    start_date: filters.start_date,
    end_date: filters.end_date,
  };

  if (filters.landing) {
    snapshot.landing = filters.landing;
  }

  if (filters.boat) {
    snapshot.boat = filters.boat;
  }

  if (filters.species) {
    snapshot.species = [...filters.species];
  }

  if (filters.limit !== undefined) {
    snapshot.limit = filters.limit;
  }

  if (filters.cursor !== undefined) {
    snapshot.cursor = filters.cursor;
  }

  return snapshot;
}
