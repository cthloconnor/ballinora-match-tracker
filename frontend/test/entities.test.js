import { describe, it, expect } from "vitest";

import { splitEntity, sensorId, binaryId, buttonId } from "../src/entities.js";

describe("entity id derivation", () => {
  it("splits a standard fixture sensor id", () => {
    const parts = splitEntity("sensor.f1_phase");
    expect(parts).toEqual({ domain: "sensor", fixture: "f1", object: "f1_phase" });
  });

  it("handles fixture ids that contain underscores", () => {
    expect(splitEntity("sensor.county_final_phase").fixture).toBe("county_final");
  });

  it("tolerates malformed ids", () => {
    expect(splitEntity("").fixture).toBe("");
    expect(splitEntity("no-dot").fixture).toBe("no-dot");
  });

  it("derives sibling entities for the same fixture", () => {
    const src = "sensor.f7_phase";
    expect(sensorId(src, "home_goals_points")).toBe("sensor.f7_home_goals_points");
    expect(sensorId(src, "confidence")).toBe("sensor.f7_confidence");
    expect(binaryId(src, "live")).toBe("binary_sensor.f7_live");
    expect(buttonId(src, "check_sources_now")).toBe("button.f7_check_sources_now");
  });
});