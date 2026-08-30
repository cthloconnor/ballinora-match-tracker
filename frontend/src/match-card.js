/** The Ballinora Match Tracker single-fixture card. */
import { LitElement, html, css, nothing, unsafeCSS } from "lit";

import { binaryId, sensorId, splitEntity, stateOf } from "./entities.js";

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

const DEFAULT_ACCENT = "#5c6bc0";

const fmt = new Intl.DateTimeFormat("en-IE", {
  weekday: "short",
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

export class BallinoraMatchCard extends LitElement {
  static properties = {
    hass: { type: Object },
    _config: { state: true },
  };

  static getConfigElement() {
    return document.createElement("ballinora-match-card-editor");
  }

  static getStubConfig(hass, entities, entitiesFill) {
    const entity = entities.find(
      (eid) =>
        eid.startsWith("sensor.") &&
        eid.endsWith("_phase") &&
        !eid.includes("tracker_"),
    );
    return {
      entity: entity || "",
      show_competition: true,
      show_venue: true,
      show_scheduled: true,
      show_confidence: true,
      show_sources: true,
      show_crests: false,
    };
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("Select a Ballinora Match Tracker fixture entity.");
    }
    this._config = { ...config };
  }

  render() {
    if (!this._config?.entity || !this.hass) {
      return this._emptyState();
    }
    const c = this._config;
    const { fixture } = splitEntity(c.entity);
    if (!fixture) {
      return this._emptyState();
    }

    const phase = stateOf(this.hass, `sensor.${fixture}_phase`) ?? "scheduled";
    const homeGP = stateOf(this.hass, `sensor.${fixture}_home_goals_points`) ?? "0-0";
    const awayGP = stateOf(this.hass, `sensor.${fixture}_away_goals_points`) ?? "0-0";
    const homeTotal = stateOf(this.hass, `sensor.${fixture}_home_total`);
    const awayTotal = stateOf(this.hass, `sensor.${fixture}_away_total`);
    const combined = stateOf(this.hass, `sensor.${fixture}_combined_score`);
    const homeTeam = stateOf(this.hass, `sensor.${fixture}_home_team`) ?? "Home";
    const awayTeam = stateOf(this.hass, `sensor.${fixture}_away_team`) ?? "Away";
    const competition = stateOf(this.hass, `sensor.${fixture}_competition`);
    const venue = stateOf(this.hass, `sensor.${fixture}_venue`);
    const scheduledAt = stateOf(this.hass, `sensor.${fixture}_scheduled_at`);
    const confidence = Number(stateOf(this.hass, `sensor.${fixture}_confidence`));

    const live =
      stateOf(this.hass, binaryId(c.entity, "live")) === "on";
    const conflict =
      stateOf(this.hass, binaryId(c.entity, "conflict")) === "on";
    const attention =
      stateOf(this.hass, binaryId(c.entity, "operator_attention")) === "on";

    const source = stateOf(this.hass, `sensor.${fixture}_selected_source`);
    const freshness = Number(
      stateOf(this.hass, `sensor.${fixture}_source_freshness`),
    );

    const accent = c.accent || DEFAULT_ACCENT;
    const phases = [this._phaseChip(phase, live), this._statusChips(conflict, attention)];

    return html`
      <ha-card class="bmt-card">
        ${competition && c.show_competition !== false
          ? html`<div class="bmt-head" style="--accent:${accent}">
              <span class="bmt-competition">${competition}</span>
              ${phases}
            </div>`
          : html`<div class="bmt-head" style="--accent:${accent}">${phases}</div>`}

        <div class="bmt-match">
          <div class="bmt-team" part="home">
            ${this._crest(c.home_crest, c)}
            <span class="bmt-team-name">${homeTeam}</span>
          </div>
          <div class="bmt-score" style="--accent:${accent}">
            <div class="bmt-scores">
              <span class="bmt-gp">${homeGP}</span>
              <span class="bmt-dash">–</span>
              <span class="bmt-gp">${awayGP}</span>
            </div>
            ${combined
              ? html`<div class="bmt-totals">${combined}</div>`
              : html`<div class="bmt-totals">
                  <span>${homeTotal ?? "0"}</span
                  ><span class="bmt-totals-sep">·</span
                  ><span>${awayTotal ?? "0"}</span>
                </div>`}
          </div>
          <div class="bmt-team" part="away">
            ${this._crest(c.away_crest, c)}
            <span class="bmt-team-name">${awayTeam}</span>
          </div>
        </div>

        ${(c.show_scheduled !== false && scheduledAt) ||
        (c.show_venue !== false && venue) ||
        (c.show_confidence !== false && Number.isFinite(confidence))
          ? html`
              <div class="bmt-meta">
                ${c.show_scheduled !== false && scheduledAt
                  ? html`<span class="bmt-meta-item">
                      ${this._formatWhen(scheduledAt)}
                    </span>`
                  : nothing}
                ${c.show_venue !== false && venue
                  ? html`<span class="bmt-meta-item">${venue}</span>`
                  : nothing}
                ${c.show_confidence !== false && Number.isFinite(confidence)
                  ? html`<span class="bmt-meta-item bmt-conf">
                      <span class="bmt-conf-bar" style="--accent:${accent}">
                        <i style="width:${confidence}%"></i>
                      </span>
                      <span class="bmt-conf-pct">${confidence}%</span>
                    </span>`
                  : nothing}
              </div>
            `
          : nothing}

        ${c.show_sources !== false && source
          ? html`<div class="bmt-src">
              <span>${source}</span
              >${Number.isFinite(freshness)
                ? html`<span class="bmt-fresh">${this._freshness(freshness)}</span>`
                : nothing}
            </div>`
          : nothing}
      </ha-card>
    `;
  }

  _crest(url) {
    return url
      ? html`<img class="bmt-crest" alt="" src="${url}" loading="lazy" />`
      : nothing;
  }

  _phaseChip(phase, live) {
    const label = PHASE_LABELS[phase] ?? phase.replaceAll("_", " ");
    return html`<span class="bmt-chip ${live ? "bmt-chip-live" : ""}">
      ${live ? html`<span class="bmt-pulse" aria-hidden="true"></span>` : nothing}
      ${label}
    </span>`;
  }

  _statusChips(conflict, attention) {
    const chips = [];
    if (conflict) {
      chips.push(html`<span class="bmt-chip bmt-chip-warn">⚠ Score</span>`);
    }
    if (attention) {
      chips.push(html`<span class="bmt-chip bmt-chip-bad">⛔ Check</span>`);
    }
    return chips;
  }

  _formatWhen(iso) {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return fmt.format(d);
  }

  _freshness(seconds) {
    if (seconds < 0) return "not checked";
    if (seconds < 60) return "updated just now";
    if (seconds < 3600) return `updated ${Math.round(seconds / 60)} min ago`;
    const hours = Math.round(seconds / 3600);
    return `updated ${hours} h ago`;
  }

  _emptyState() {
    return html`
      <ha-card class="bmt-card bmt-empty">
        <span>Ballinora Match Tracker</span>
        <span class="bmt-empty-hint">Select a fixture entity in the card editor.</span>
      </ha-card>
    `;
  }

  static styles = css`
    :host {
      --bmt-accent: ${unsafeCSS(DEFAULT_ACCENT)};
    }
    .bmt-card {
      padding: 16px;
      border-radius: var(--ha-card-border-radius, 12px);
      background: var(--card-background-color, var(--card-bg, #fff));
    }
    .bmt-head {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 12px;
      border-bottom: 1px solid
        var(--divider-color, rgba(0, 0, 0, 0.12));
      padding-bottom: 10px;
    }
    .bmt-competition {
      font-size: 14px;
      font-weight: 600;
      color: var(--primary-text-color, #1c1c1c);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-right: auto;
    }
    .bmt-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 999px;
      color: var(--bmt-accent, ${unsafeCSS(DEFAULT_ACCENT)});
      background: rgba(128, 128, 160, 0.14);
    }
    .bmt-chip-live {
      color: #2e7d32;
      background: rgba(46, 125, 50, 0.12);
    }
    .bmt-chip-warn {
      color: #f57f17;
      background: rgba(245, 127, 23, 0.14);
    }
    .bmt-chip-bad {
      color: #c62828;
      background: rgba(198, 40, 40, 0.12);
    }
    .bmt-pulse {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
      animation: bmt-pulse 1.6s ease-in-out infinite;
    }
    @keyframes bmt-pulse {
      0%,
      100% {
        opacity: 1;
        transform: scale(1);
      }
      50% {
        opacity: 0.35;
        transform: scale(0.75);
      }
    }
    .bmt-match {
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 8px;
    }
    .bmt-team {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      min-width: 0;
    }
    .bmt-team-name {
      font-size: 14px;
      font-weight: 600;
      color: var(--primary-text-color, #1c1c1c);
      text-align: center;
      line-height: 1.25;
    }
    .bmt-crest {
      width: 44px;
      height: 44px;
      object-fit: contain;
      border-radius: 8px;
    }
    .bmt-score {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      padding: 0 10px;
    }
    .bmt-scores {
      display: flex;
      align-items: baseline;
      gap: 8px;
    }
    .bmt-gp {
      font-size: clamp(20px, 4vw, 30px);
      font-weight: 700;
      font-variant-numeric: tabular-nums;
      color: var(--primary-text-color, #1c1c1c);
    }
    .bmt-dash {
      color: var(--secondary-text-color, #727272);
      font-size: 18px;
    }
    .bmt-totals {
      display: flex;
      gap: 6px;
      align-items: center;
      font-size: 13px;
      font-weight: 600;
      color: var(--bmt-accent, ${unsafeCSS(DEFAULT_ACCENT)});
      font-variant-numeric: tabular-nums;
    }
    .bmt-totals-sep {
      opacity: 0.5;
    }
    .bmt-meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px 16px;
      margin-top: 14px;
      padding-top: 10px;
      border-top: 1px solid var(--divider-color, rgba(0, 0, 0, 0.12));
      font-size: 12.5px;
      color: var(--secondary-text-color, #727272);
    }
    .bmt-conf {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-left: auto;
    }
    .bmt-conf-bar {
      display: inline-block;
      width: 64px;
      height: 6px;
      border-radius: 999px;
      overflow: hidden;
      background: var(--divider-color, rgba(0, 0, 0, 0.12));
    }
    .bmt-conf-bar i {
      display: block;
      height: 100%;
      background: var(--bmt-accent, ${unsafeCSS(DEFAULT_ACCENT)});
      border-radius: inherit;
    }
    .bmt-conf-pct {
      font-variant-numeric: tabular-nums;
    }
    .bmt-src {
      margin-top: 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      font-size: 11.5px;
      color: var(--secondary-text-color, #727272);
    }
    .bmt-fresh {
      font-style: italic;
    }
    .bmt-empty {
      display: flex;
      flex-direction: column;
      gap: 6px;
      color: var(--secondary-text-color, #727272);
      font-size: 14px;
    }
    .bmt-empty-hint {
      font-size: 12px;
      color: var(--disabled-text-color, #999);
    }
    @media (min-width: 520px) {
      .bmt-gp {
        font-size: 34px;
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .bmt-pulse {
        animation: none;
      }
    }
  `;
}

customElements.define("ballinora-match-card", BallinoraMatchCard);