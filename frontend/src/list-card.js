/** Compact list of every fixture currently known to the tracker. */
import { LitElement, html, css, nothing } from "lit";

import { stateOf } from "./entities.js";

const PHASE_LABELS = {
  scheduled: "Scheduled",
  first_half: "First half",
  half_time: "Half-time",
  second_half: "Second half",
  extra_time: "Extra time",
  extra_time_half_time: "Extra-time interval",
  penalties: "Penalties",
  full_time_provisional: "Awaiting confirmation",
  full_time_confirmed: "Full-time",
  postponed: "Postponed",
  cancelled: "Cancelled",
  abandoned: "Abandoned",
};

function phaseRank(phase) {
  if (["first_half", "second_half", "extra_time", "penalties"].includes(phase)) {
    return 0;
  }
  if (["full_time_provisional", "full_time_confirmed"].includes(phase)) {
    return 1;
  }
  return 2;
}

export class BallinoraMatchList extends LitElement {
  static properties = {
    hass: { type: Object },
    _config: { state: true },
  };

  static getConfigElement() {
    return document.createElement("ballinora-match-card-editor");
  }

  static getStubConfig(hass, entities, entitiesFill) {
    return {};
  }

  setConfig(config) {
    this._config = { ...(config || {}) };
  }

  _fixtures() {
    if (!this.hass) return [];
    const fixtures = new Map();
    for (const eid of Object.keys(this.hass.states)) {
      const match = /^sensor\.(.+)_phase$/.exec(eid);
      if (!match || match[1].startsWith("tracker")) continue;
      fixtures.set(match[1], eid);
    }
    const list = [];
    for (const [id] of fixtures) {
      const base = `sensor.${id}`;
      const phase = stateOf(this.hass, `${base}_phase`) ?? "scheduled";
      list.push({
        id,
        phase,
        home: stateOf(this.hass, `${base}_home_team`) ?? "Home",
        away: stateOf(this.hass, `${base}_away_team`) ?? "Away",
        homeGP: stateOf(this.hass, `${base}_home_goals_points`) ?? "0-0",
        awayGP: stateOf(this.hass, `${base}_away_goals_points`) ?? "0-0",
        live: stateOf(this.hass, `binary_sensor.${id}_live`) === "on",
        competition: stateOf(this.hass, `${base}_competition`),
        rank: phaseRank(phase),
      });
    }
    list.sort((a, b) => a.rank - b.rank || a.home.localeCompare(b.home));
    return list;
  }

  render() {
    const fixtures = this._fixtures();
    if (!fixtures.length) {
      return html`<ha-card class="bmt-list" part="empty">
        <span>No fixtures from the Ballinora Match Tracker.</span>
      </ha-card>`;
    }
    const rows = fixtures.map(
      (f) => html`
        <div class="bmt-row ${f.live ? "is-live" : ""}">
          <span class="bmt-row-phase">
            ${f.live ? html`<span class="bmt-dot" aria-hidden="true"></span>` : nothing}
            ${PHASE_LABELS[f.phase] ?? f.phase}
          </span>
          <span class="bmt-row-teams">
            <span class="bmt-row-home">${f.home}</span> vs
            <span class="bmt-row-away">${f.away}</span>
          </span>
          <span class="bmt-row-score">${f.homeGP} · ${f.awayGP}</span>
          ${f.competition
            ? html`<span class="bmt-row-comp">${f.competition}</span>`
            : nothing}
        </div>
      `,
    );
    return html`<ha-card class="bmt-list">${rows}</ha-card>`;
  }

  static styles = css`
    .bmt-list {
      padding: 8px 0;
      border-radius: var(--ha-card-border-radius, 12px);
      background: var(--card-background-color, var(--card-bg, #fff));
    }
    .bmt-row {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 16px;
      font-size: 14px;
    }
    .bmt-row + .bmt-row {
      border-top: 1px solid var(--divider-color, rgba(0, 0, 0, 0.08));
    }
    .bmt-row-teams {
      flex: 1;
      min-width: 0;
      color: var(--secondary-text-color, #727272);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .bmt-row-home,
    .bmt-row-away {
      color: var(--primary-text-color, #1c1c1c);
      font-weight: 600;
    }
    .bmt-row-score {
      font-variant-numeric: tabular-nums;
      font-weight: 700;
      color: var(--primary-text-color, #1c1c1c);
      white-space: nowrap;
    }
    .bmt-row-phase {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      color: var(--secondary-text-color, #727272);
      width: 84px;
    }
    .bmt-row-comp {
      font-size: 12px;
      color: var(--secondary-text-color, #727272);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 180px;
    }
    .bmt-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #2e7d32;
      animation: bmt-blink 1.4s ease-in-out infinite;
    }
    @keyframes bmt-blink {
      0%,
      100% {
        opacity: 1;
      }
      50% {
        opacity: 0.3;
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .bmt-dot {
        animation: none;
      }
    }
    @media (max-width: 520px) {
      .bmt-row-comp {
        display: none;
      }
      .bmt-row-phase {
        width: auto;
      }
    }
  `;
}

customElements.define("ballinora-match-list", BallinoraMatchList);