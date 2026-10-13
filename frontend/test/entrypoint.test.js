import { afterEach, describe, expect, it, vi } from "vitest";

async function loadEntrypoint(initialRegistry) {
  vi.resetModules();
  vi.doMock("../src/match-card.js", () => ({ BallinoraMatchCard: class {} }));
  vi.doMock("../src/list-card.js", () => ({ BallinoraMatchList: class {} }));
  vi.doMock("../src/editor.js", () => ({}));
  delete window.customCards;
  if (initialRegistry !== undefined) window.customCards = initialRegistry;
  await import("../src/ballinora-match-card.js");
}

describe("card entrypoint registration", () => {
  afterEach(() => { delete window.customCards; });

  it("initializes the picker registry and registers both card descriptors", async () => {
    await loadEntrypoint();
    expect(window.customCards.map((card) => card.type)).toEqual([
      "ballinora-match-card", "ballinora-match-list",
    ]);
  });

  it("does not duplicate descriptors in an existing registry", async () => {
    const existing = [
      { type: "ballinora-match-card", name: "Existing match" },
      { type: "ballinora-match-list", name: "Existing list" },
    ];
    await loadEntrypoint(existing);
    expect(window.customCards).toEqual(existing);
  });
});
