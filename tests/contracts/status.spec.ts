import { describe, it, expect } from "vitest";
import { validateStatusResponse } from "../../scripts/api/validators";
import { mockStatusResponse } from "../../scripts/api/mocks";
import { StatusResponse } from "../../scripts/api/types";

describe("status contract", () => {
  it("accepts the generated mock payload", () => {
    expect(() => validateStatusResponse(mockStatusResponse)).not.toThrow();
  });

  it("rejects unsupported status states", () => {
    const invalid = { ...mockStatusResponse, status: "unknown" } as any;
    expect(() => validateStatusResponse(invalid)).toThrowError(/status/i);
  });

  it("accepts ok status when message and incident are null", () => {
    const status: StatusResponse = {
      ...mockStatusResponse,
      message: null,
      incident_id: null,
    };

    expect(() => validateStatusResponse(status)).not.toThrow();
  });

  it("accepts degraded status with message and incident id", () => {
    const status: StatusResponse = {
      ...mockStatusResponse,
      status: "degraded",
      message: "Upstream refresh delayed",
      incident_id: "INC-20250927",
    };

    expect(() => validateStatusResponse(status)).not.toThrow();
  });

  it("accepts error status without incident id but with message", () => {
    const status: StatusResponse = {
      ...mockStatusResponse,
      status: "error",
      message: "Supabase edge function unavailable",
      incident_id: null,
    };

    expect(() => validateStatusResponse(status)).not.toThrow();
  });

  it("rejects degraded status without a message", () => {
    const status: StatusResponse = {
      ...mockStatusResponse,
      status: "degraded",
      message: null,
    } as StatusResponse;

    expect(() => validateStatusResponse(status)).toThrowError(/message/i);
  });

  it("rejects empty incident id strings", () => {
    const status: StatusResponse = {
      ...mockStatusResponse,
      incident_id: " ",
    };

    expect(() => validateStatusResponse(status)).toThrowError(/incident_id/i);
  });
});
