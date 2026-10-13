import { describe, it, expect } from "vitest";

import { splitEntity, sensorId, binaryId, buttonId } from "../src/entities.js";

describe("entity id derivation", () => {
  it("splits a standard fixture sensor id", () => {
    const parts = splitEntity("sensor.f1_phase");
    expect(parts).toEqual({ domain: "sensor", fixture: "f1", object: "f1_phase" });
  });

  it("handles fixture ids that contain underscores", () => {
    expect(splitEntity("sensor.county_final_phase").fixture).toBe("county_final");
    expect(splitEntity("sensor.county_final_home_goals_points").fixture).toBe("county_final");
    expect(splitEntity("binary_sensor.county_final_operator_attention").fixture).toBe("county_final");
  });

  it("removes the complete known multiword suffix", () => {
    expect(splitEntity("sensor.f1_home_goals_points").fixture).toBe("f1");
    expect(splitEntity("binary_sensor.f1_operator_attention").fixture).toBe("f1");
    expect(splitEntity("button.f1_check_sources_now").fixture).toBe("f1");
  });

  it("tolerates malformed ids", () => {
    expect(splitEntity("").fixture).toBe("");
    expect(splitEntity("no-dot").fixture).toBe("no-dot");
    expect(splitEntity(null).fixture).toBe("");
    expect(splitEntity(".phase")).toEqual({ domain: "", object: ".phase", fixture: ".phase" });
  });

  it("derives sibling entities for the same fixture", () => {
    const src = "sensor.f7_phase";
    expect(sensorId(src, "home_goals_points")).toBe("sensor.f7_home_goals_points");
    expect(sensorId(src, "confidence")).toBe("sensor.f7_confidence");
    expect(binaryId(src, "live")).toBe("binary_sensor.f7_live");
    expect(buttonId(src, "check_sources_now")).toBe("button.f7_check_sources_now");
    expect(sensorId("sensor.county_final_home_goals_points", "phase")).toBe("sensor.county_final_phase");
    expect(binaryId("binary_sensor.county_final_operator_attention", "live")).toBe("binary_sensor.county_final_live");
    expect(buttonId("button.county_final_check_sources_now", "check_sources_now")).toBe("button.county_final_check_sources_now");
  });
});