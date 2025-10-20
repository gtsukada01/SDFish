import { describe, it, expect } from "vitest";
import { validateCatchTableResponse } from "../../scripts/api/validators";
import { mockCatchTableResponse } from "../../scripts/api/mocks";
import { CatchTableResponse } from "../../scripts/api/types";
import { detectBlankFields } from "../../scripts/api/instrumentation";

describe("catch table contract", () => {
  it("accepts the generated mock payload", () => {
    expect(() => validateCatchTableResponse(mockCatchTableResponse)).not.toThrow();
  });

  it("rejects records where top_species_count exceeds total_fish", () => {
    const invalid = {
      ...mockCatchTableResponse,
      data: [
        {
          ...mockCatchTableResponse.data[0],
          top_species_count: mockCatchTableResponse.data[0].total_fish + 10,
        },
      ],
    };

    expect(() => validateCatchTableResponse(invalid)).toThrowError(/top_species_count/i);
  });

  it("flags missing required fields", () => {
    const invalid = {
      ...mockCatchTableResponse,
      data: [
        {
          ...mockCatchTableResponse.data[0],
          landing: null,
        },
      ],
    } as unknown as CatchTableResponse;

    expect(() => validateCatchTableResponse(invalid)).toThrowError(/landing/is);
  });

  it("exposes progressive pagination details once total rows exceed chunk size", () => {
    const { pagination } = mockCatchTableResponse;
    expect(pagination.total_rows).toBeGreaterThan(pagination.limit);
    expect(pagination.limit).toBe(1000);
    expect(pagination.returned_rows).toBe(pagination.limit);
    expect(pagination.next_cursor).toEqual(expect.any(String));
  });

  it("permits blank-string fields while requiring telemetry to flag them", () => {
    const mutated: CatchTableResponse = {
      ...mockCatchTableResponse,
      data: [
        {
          ...mockCatchTableResponse.data[0],
          boat: "",
          landing: "",
          top_species: "",
        },
      ],
    };

    expect(() => validateCatchTableResponse(mutated)).not.toThrow();

    const blanks = detectBlankFields(mutated.data[0] as Record<string, unknown>, [
      "boat",
      "landing",
      "angler_count",
      "top_species",
    ]);

    expect(blanks).toEqual(["boat", "landing", "top_species"]);
  });
});
