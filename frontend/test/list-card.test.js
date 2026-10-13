import { afterEach, describe, expect, it } from "vitest";
import "../src/list-card.js";

function fixture(id, phase, extra = {}) {
  return {
    [`sensor.${id}_phase`]: { state: phase },
    [`sensor.${id}_home_team`]: { state: id },
    [`sensor.${id}_away_team`]: { state: "Away" },
    ...extra,
  };
}

async function render(states) {
  const el = document.createElement("ballinora-match-list");
  el.hass = { states };
  document.body.appendChild(el);
  await el.updateComplete;
  return el;
}

describe("ballinora-match-list", () => {
  afterEach(() => { document.body.innerHTML = ""; });

  it("sorts canonical live fixtures and all in-play phases before completed fixtures", async () => {
    const states = {
      ...fixture("completed", "full_time_confirmed"),
      ...fixture("z-halftime", "half_time"),
      ...fixture("a-extra-break", "extra_time_half_time"),
      ...fixture("a-live", "scheduled", { "binary_sensor.a-live_live": { state: "on" } }),
    };
    const el = await render(states);
    expect(el._fixtures().map((f) => f.id)).toEqual(["a-extra-break", "a-live", "z-halftime", "completed"]);
    const rows = [...el.shadowRoot.querySelectorAll(".bmt-row")];
    expect(rows[0].textContent).toContain("Extra-time interval");
    expect(rows[1].classList.contains("is-live")).toBe(true);
    expect(rows[2].textContent).toContain("Half-time");
    expect(rows[3].textContent).toContain("Full-time");
  });

  it("filters unavailable, unknown, missing and unrecognized phases and shows missing scores as Unknown", async () => {
    const states = {
      ...fixture("valid", "scheduled"),
      ...fixture("unavailable", "unavailable"),
      ...fixture("unknown", "unknown"),
      ...fixture("missing"),
      ...fixture("unrecognized", "mystery_phase"),
    };
    const el = await render(states);
    expect(el._fixtures().map((f) => f.id)).toEqual(["valid"]);
    expect(el.shadowRoot.textContent).toContain("Unknown · Unknown");
    expect(el.shadowRoot.textContent).not.toContain("unavailable");
    expect(el.shadowRoot.textContent).not.toContain("mystery_phase");
  });
});
