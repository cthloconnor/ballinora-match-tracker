/**
 * Entry point for the Ballinora Match Tracker Lovelace cards.
 *
 * Registers the single-fixture match card, the multi-fixture list card and
 * their shared visual editor, and advertises both in the "Add card" picker.
 */
import { LitElement } from "lit";

import "./match-card.js";
import "./list-card.js";
import "./editor.js";

export const ballinoraMatchCardVersion = "1.0.0";

if (typeof window !== "undefined" && window.customCards) {
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "ballinora-match-card",
    name: "Ballinora Match",
    description: "Live score, phase and source confidence for one Ballinora fixture",
    preview: false,
  });
  window.customCards.push({
    type: "ballinora-match-list",
    name: "Ballinora Matches",
    description: "All current Ballinora fixtures in a compact list",
    preview: false,
  });
}

// The custom element classes must stay referenced so bundlers keep them.
export { BallinoraMatchCard } from "./match-card.js";
export { BallinoraMatchList } from "./list-card.js";