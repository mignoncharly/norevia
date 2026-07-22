import { describe, expect, it } from "vitest";
import { aggregate, normalize } from "./index";

describe("normalization", () => {
  it("caps outliers and handles direction", () => {
    expect(normalize(120, 20, 100, "HIGHER_IS_BETTER")).toBe(100);
    expect(normalize(20, 20, 100, "LOWER_IS_BETTER")).toBe(100);
  });
});

describe("aggregation", () => {
  it("keeps coverage distinct from score", () => {
    const result = aggregate([
      { score: 80, weight: 60, qualityCoefficient: 1, available: true },
      { score: null, weight: 40, qualityCoefficient: 0, available: false },
    ]);
    expect(result.destinationScore).toBe(80);
    expect(result.dataCoverage).toBe(60);
  });
});
