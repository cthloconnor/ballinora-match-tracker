import { describe, it, expect, afterEach } from "vitest";

import "../src/match-card.js";

function makeHass() {
  return {
    states: {
      "sensor.f1_phase": { state: "second_half" },
      "sensor.f1_home_team": { state: "Ballinora" },
      "sensor.f1_away_team": { state: "Rivals" },
      "sensor.f1_home_goals_points": { state: "2-12" },
      "sensor.f1_away_goals_points": { state: "1-9" },
      "sensor.f1_home_total": { state: "18" },
      "sensor.f1_away_total": { state: "12" },
      "sensor.f1_combined_score": { state: "2-12 - 1-9" },
      "sensor.f1_competition": { state: "County Championship" },
      "sensor.f1_venue": { state: "Ballinora Park" },
      "sensor.f1_scheduled_at": { state: "2026-08-30T14:00:00+01:00" },
      "sensor.f1_confidence": { state: "87.5" },
      "sensor.f1_selected_source": { state: "Home page" },
      "sensor.f1_source_freshness": { state: "42" },
      "binary_sensor.f1_live": { state: "on" },
      "binary_sensor.f1_conflict": { state: "off" },
      "binary_sensor.f1_operator_attention": { state: "off" },
    },
  };
}

async function render(config = {}, hass = makeHass()) {
  const el = document.createElement("ballinora-match-card");
  el.setConfig({ entity: "sensor.f1_phase", ...config });
  el.hass = hass;
  document.body.appendChild(el);
  await el.updateComplete;
  return el;
}

describe("ballinora-match-card", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("throws without an entity", () => {
    const el = document.createElement("ballinora-match-card");
    expect(() => el.setConfig({})).toThrow();
  });

  it("is registered as a custom element", () => {
    expect(customElements.get("ballinora-match-card")).toBeDefined();
  });

  it("renders teams, scores and phase", async () => {
    const el = await render();
    const text = el.shadowRoot.textContent;
    expect(text).toContain("Ballinora");
    expect(text).toContain("Rivals");
    expect(text).toContain("2-12");
    expect(text).toContain("1-9");
    expect(text).toContain("Second half");
    expect(text).toContain("County Championship");
    expect(text).toContain("Ballinora Park");
  });

  it("shows a card_title override instead of the competition", async () => {
    const el = await render({ card_title: "Senior Final" });
    const text = el.shadowRoot.textContent;
    expect(text).toContain("Senior Final");
    expect(text).not.toContain("County Championship");
    expect(text).toContain("Ballinora");
  });

  it("renders a live indicator when the live binary sensor is on", async () => {
    const el = await render();
    expect(el.shadowRoot.querySelector(".bmt-chip-live")).not.toBeNull();
  });

  it("renders crests only when enabled", async () => {
    const el = await render({ show_crests: true, home_crest: "https://h", away_crest: "https://a" });
    const imgs = [...el.shadowRoot.querySelectorAll(".bmt-crest")];
    expect(imgs).toHaveLength(2);
    expect(imgs[0].getAttribute("src")).toBe("https://h");
    expect(imgs[1].getAttribute("src")).toBe("https://a");
  });

  it("adds an outline class when enabled", async () => {
    const el = await render({
      show_crests: true,
      outline: true,
      home_crest: "https://h",
      away_crest: "https://a",
    });
    const imgs = [...el.shadowRoot.querySelectorAll(".bmt-crest")];
    expect(imgs.every((i) => i.classList.contains("bmt-crest-outline"))).toBe(true);
  });

  it("flips sides when home_side is right", async () => {
    const el = await render({ home_side: "right" });
    const homeSide = el.shadowRoot.querySelector('.bmt-side[part="home"]');
    const awaySide = el.shadowRoot.querySelector('.bmt-side[part="away"]');
    // The home element must be physically after the away element in the grid.
    const homeIndex = [...el.shadowRoot.querySelectorAll(".bmt-side")].indexOf(homeSide);
    const awayIndex = [...el.shadowRoot.querySelectorAll(".bmt-side")].indexOf(awaySide);
    expect(homeIndex).toBeGreaterThan(awayIndex);
    expect(homeSide.textContent).toContain("Ballinora");
    expect(awaySide.textContent).toContain("Rivals");
  });

  it("hides optional sections per config", async () => {
    const el = await render({
      show_confidence: false,
      show_sources: false,
      show_venue: false,
    });
    const text = el.shadowRoot.textContent;
    expect(text).not.toContain("Ballinora Park");
    expect(text).not.toContain("Home page");
    expect(text).not.toContain("%");
  });

  it("opens a URL when a side tap target is configured", async () => {
    const opened = [];
    const orig = window.open;
    window.open = (u) => opened.push(u);
    const el = await render({ home_url: "https://example.org/home" });
    await el.updateComplete;
    const homeSide = el.shadowRoot.querySelector('.bmt-side[part="home"]');
    homeSide.click();
    expect(opened).toContain("https://example.org/home");
    window.open = orig;
  });

  it("renders the empty state when no entity is configured", async () => {
    const el = document.createElement("ballinora-match-card");
    el.hass = makeHass();
    document.body.appendChild(el);
    await el.updateComplete;
    expect(el.shadowRoot.textContent).toContain("Select a fixture entity");
  });
});