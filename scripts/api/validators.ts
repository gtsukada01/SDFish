import {
  CatchRecord,
  CatchTableResponse,
  SummaryMetricsResponse,
  StatusResponse,
} from "./types";

class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValidationError";
  }
}

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new ValidationError(message);
  }
}

function validateCatchRecord(record: CatchRecord): void {
  const requiredString = [
    [record.id, "id"],
    [record.trip_date, "trip_date"],
    [record.boat, "boat"],
    [record.landing, "landing"],
    [record.top_species, "top_species"],
    [record.created_at, "created_at"],
  ] as const;

  const allowBlankString = new Set(["boat", "landing", "top_species"] as const);

  for (const [value, field] of requiredString) {
    const isString = typeof value === "string";
    const hasContent = isString && value.length > 0;
    if (allowBlankString.has(field)) {
      assert(isString, `Missing ${field}`);
    } else {
      assert(hasContent, `Missing ${field}`);
    }
  }

  assert(
    typeof record.trip_duration_hours === "number" &&
      record.trip_duration_hours >= 0,
    "trip_duration_hours must be a non-negative number",
  );

  if (record.angler_count !== null) {
    assert(
      Number.isInteger(record.angler_count) && record.angler_count >= 0,
      "angler_count must be null or a non-negative integer",
    );
  }

  assert(
    Number.isInteger(record.total_fish) && record.total_fish >= 0,
    "total_fish must be a non-negative integer",
  );

  assert(
    Number.isInteger(record.top_species_count) &&
      record.top_species_count >= 0 &&
      record.top_species_count <= record.total_fish,
    "top_species_count must be ≤ total_fish",
  );

  if (Array.isArray(record.species_breakdown)) {
    record.species_breakdown.forEach((entry, index) => {
      assert(entry && typeof entry === "object", `species_breakdown[${index}] invalid`);
      assert(
        typeof entry.species === "string" && entry.species.length > 0,
        `species_breakdown[${index}].species missing`,
      );
      assert(
        Number.isInteger(entry.count) && entry.count >= 0,
        `species_breakdown[${index}].count must be a non-negative integer`,
      );
    });
  }
}

export function validateCatchTableResponse(payload: CatchTableResponse): void {
  assert(payload && typeof payload === "object", "payload must be an object");

  assert(Array.isArray(payload.data), "data must be an array");
  payload.data.forEach(validateCatchRecord);

  const pagination = payload.pagination;
  assert(pagination && typeof pagination === "object", "pagination missing");
  assert(
    Number.isInteger(pagination.total_rows) && pagination.total_rows >= 0,
    "pagination.total_rows invalid",
  );
  assert(
    Number.isInteger(pagination.returned_rows) &&
      pagination.returned_rows >= 0 &&
      pagination.returned_rows <= pagination.total_rows,
    "pagination.returned_rows invalid",
  );
  assert(
    Number.isInteger(pagination.limit) && pagination.limit >= 0,
    "pagination.limit invalid",
  );
  assert(
    pagination.next_cursor === null || typeof pagination.next_cursor === "string",
    "pagination.next_cursor must be string or null",
  );

  const filters = payload.filters_applied;
  assert(filters && typeof filters === "object", "filters_applied missing");
  assert(typeof filters.start_date === "string", "filters.start_date missing");
  assert(typeof filters.end_date === "string", "filters.end_date missing");
  if (filters.species !== undefined) {
    assert(Array.isArray(filters.species), "filters.species must be an array");
    filters.species.forEach((value, index) =>
      assert(typeof value === "string", `filters.species[${index}] must be string`),
    );
  }
  if (filters.landing !== undefined && filters.landing !== null) {
    assert(typeof filters.landing === "string", "filters.landing must be string or null");
  }
  if (filters.boat !== undefined && filters.boat !== null) {
    assert(typeof filters.boat === "string", "filters.boat must be string or null");
  }
  if (filters.limit !== undefined && filters.limit !== null) {
    assert(Number.isInteger(filters.limit) && filters.limit >= 0, "filters.limit must be a non-negative integer");
  }
  if (filters.cursor !== undefined && filters.cursor !== null) {
    assert(typeof filters.cursor === "string", "filters.cursor must be string or null");
  }

  assert(typeof payload.last_synced_at === "string", "last_synced_at missing");
}

export function validateSummaryMetricsResponse(payload: SummaryMetricsResponse): void {
  assert(payload && typeof payload === "object", "payload must be an object");

  const fleet = payload.fleet;
  assert(fleet && typeof fleet === "object", "fleet metrics missing");
  assert(Number.isInteger(fleet.total_trips) && fleet.total_trips >= 0, "fleet.total_trips invalid");
  assert(Number.isInteger(fleet.total_fish) && fleet.total_fish >= 0, "fleet.total_fish invalid");
  assert(Number.isInteger(fleet.unique_boats) && fleet.unique_boats >= 0, "fleet.unique_boats invalid");
  assert(
    Number.isInteger(fleet.unique_species) && fleet.unique_species >= 0,
    "fleet.unique_species invalid",
  );

  assert(Array.isArray(payload.per_boat), "per_boat must be array");
  const boatNames = new Set<string>();
  let totalBoatFish = 0;
  let totalTrips = 0;
  payload.per_boat.forEach((metric, index) => {
    assert(metric && typeof metric === "object", `per_boat[${index}] invalid`);
    assert(typeof metric.boat === "string" && metric.boat.length > 0, `per_boat[${index}].boat missing`);
    assert(Number.isInteger(metric.trips) && metric.trips >= 0, `per_boat[${index}].trips invalid`);
    assert(
      Number.isInteger(metric.total_fish) && metric.total_fish >= 0,
      `per_boat[${index}].total_fish invalid`,
    );
    assert(
      typeof metric.top_species === "string" && metric.top_species.length > 0,
      `per_boat[${index}].top_species missing`,
    );
    assert(
      Number.isInteger(metric.top_species_count) && metric.top_species_count >= 0,
      `per_boat[${index}].top_species_count invalid`,
    );

    boatNames.add(metric.boat);
    totalBoatFish += metric.total_fish;
    totalTrips += metric.trips;
  });

  assert(Array.isArray(payload.per_species), "per_species must be array");
  const speciesNames = new Set<string>();
  let totalSpeciesFish = 0;
  payload.per_species.forEach((metric, index) => {
    assert(metric && typeof metric === "object", `per_species[${index}] invalid`);
    assert(typeof metric.species === "string" && metric.species.length > 0, `per_species[${index}].species missing`);
    assert(
      Number.isInteger(metric.total_fish) && metric.total_fish >= 0,
      `per_species[${index}].total_fish invalid`,
    );
    assert(Number.isInteger(metric.boats) && metric.boats >= 0, `per_species[${index}].boats invalid`);

    assert(
      metric.boats <= fleet.unique_boats,
      `per_species[${index}].boats cannot exceed fleet.unique_boats`,
    );

    speciesNames.add(metric.species);
    totalSpeciesFish += metric.total_fish;
  });

  assert(
    totalBoatFish === fleet.total_fish,
    "Sum of per_boat.total_fish must equal fleet.total_fish",
  );
  assert(
    totalTrips === fleet.total_trips,
    "Sum of per_boat.trips must equal fleet.total_trips",
  );
  assert(
    totalSpeciesFish === fleet.total_fish,
    "Sum of per_species.total_fish must equal fleet.total_fish",
  );
  assert(
    boatNames.size === fleet.unique_boats,
    "fleet.unique_boats must equal unique per_boat count",
  );
  assert(
    speciesNames.size === fleet.unique_species,
    "fleet.unique_species must equal unique per_species count",
  );

  const filters = payload.filters_applied;
  assert(filters && typeof filters === "object", "filters_applied missing");
  assert(typeof filters.start_date === "string", "filters.start_date missing");
  assert(typeof filters.end_date === "string", "filters.end_date missing");

  assert(typeof payload.last_synced_at === "string", "last_synced_at missing");
}

export function validateStatusResponse(payload: StatusResponse): void {
  assert(payload && typeof payload === "object", "payload must be an object");
  const allowed: StatusResponse["status"][] = ["ok", "degraded", "error"];
  assert(allowed.includes(payload.status), "status must be ok, degraded, or error");
  assert(typeof payload.last_synced_at === "string", "last_synced_at missing");
  const message = payload.message ?? null;
  const incidentId = payload.incident_id ?? null;

  if (message !== null) {
    assert(typeof message === "string", "message must be string or null");
    assert(message.trim().length > 0, "message must be a non-empty string");
  }

  if (payload.status !== "ok") {
    assert(message !== null, "degraded/error status requires message");
  }

  if (incidentId !== null) {
    assert(typeof incidentId === "string", "incident_id must be string or null");
    assert(incidentId.trim().length > 0, "incident_id must be a non-empty string when provided");
  }
}
