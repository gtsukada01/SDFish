import { describe, it, expect } from "vitest";
import { validateSummaryMetricsResponse } from "../../scripts/api/validators";
import { mockCatchTableResponse, mockSummaryMetricsResponse } from "../../scripts/api/mocks";
import { SummaryMetricsResponse } from "../../scripts/api/types";

describe("summary metrics contract", () => {
  it("accepts the generated mock payload", () => {
    expect(() => validateSummaryMetricsResponse(mockSummaryMetricsResponse)).not.toThrow();
  });

  it("rejects when fleet totals do not align with per-boat totals", () => {
    const invalid = {
      ...mockSummaryMetricsResponse,
      fleet: {
        ...mockSummaryMetricsResponse.fleet,
        total_fish: mockSummaryMetricsResponse.fleet.total_fish + 1,
      },
    };

    expect(() => validateSummaryMetricsResponse(invalid)).toThrowError(/total_fish/i);
  });

  it("rejects when fleet totals do not align with per-species totals", () => {
    const invalid = JSON.parse(JSON.stringify(mockSummaryMetricsResponse)) as SummaryMetricsResponse;
    invalid.per_species[0].total_fish += 1;

    expect(() => validateSummaryMetricsResponse(invalid)).toThrowError(/per_species/i);
  });

  it("rejects when unique boat count mismatches per-boat aggregates", () => {
    const invalid = JSON.parse(JSON.stringify(mockSummaryMetricsResponse)) as SummaryMetricsResponse;
    invalid.fleet.unique_boats += 1;

    expect(() => validateSummaryMetricsResponse(invalid)).toThrowError(/unique_boats/i);
  });

  it("rejects when unique species count mismatches per-species aggregates", () => {
    const invalid = JSON.parse(JSON.stringify(mockSummaryMetricsResponse)) as SummaryMetricsResponse;
    invalid.fleet.unique_species -= 1;

    expect(() => validateSummaryMetricsResponse(invalid)).toThrowError(/unique_species/i);
  });

  it("summarises boats, species, and totals consistently", () => {
    const { fleet, per_boat: perBoat, per_species: perSpecies } = mockSummaryMetricsResponse;

    const totalBoatFish = perBoat.reduce((sum, boat) => sum + boat.total_fish, 0);
    const totalBoatTrips = perBoat.reduce((sum, boat) => sum + boat.trips, 0);
    const totalSpeciesFish = perSpecies.reduce((sum, species) => sum + species.total_fish, 0);
    const uniqueBoatCount = new Set(perBoat.map((boat) => boat.boat)).size;
    const uniqueSpeciesCount = new Set(perSpecies.map((species) => species.species)).size;

    expect(totalBoatFish).toBe(fleet.total_fish);
    expect(totalBoatTrips).toBe(fleet.total_trips);
    expect(totalSpeciesFish).toBe(fleet.total_fish);
    expect(uniqueBoatCount).toBe(fleet.unique_boats);
    expect(uniqueSpeciesCount).toBe(fleet.unique_species);
  });

  it("echoes the applied filters used for the catch table", () => {
    expect(mockSummaryMetricsResponse.filters_applied).toEqual(
      mockCatchTableResponse.filters_applied,
    );
  });
});
