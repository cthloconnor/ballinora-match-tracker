/** The Ballinora Match Tracker single-fixture scoreboard card.
 *
 * A scoreboard in the style of the popular teamtracker card, but driven by the
 * Ballinora Match Tracker integration (the app is the source, never ESPN).
 * Teams sit on opposite sides, the goals-points score dominates the middle and
 * the game state/clock sits below it. Layout is flipped with ``home_side``.
 */
import { LitElement, html, css, nothing, unsafeCSS } from "lit";

import { binaryId, splitEntity, stateOf } from "./entities.js";

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
      show_crests: false,
      show_competition: true,
      show_scheduled: true,
      show_venue: true,
      show_confidence: true,
      show_sources: true,
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
    const home = {
      part: "home",
      name: homeTeam,
      gp: homeGP,
      total: homeTotal,
      crest: c.home_crest,
      url: c.home_url,
    };
    const away = {
      part: "away",
      name: awayTeam,
      gp: awayGP,
      total: awayTotal,
      crest: c.away_crest,
      url: c.away_url,
    };
    const flip = c.home_side === "right";
    const left = flip ? away : home;
    const right = flip ? home : away;

    return html`
      <ha-card
        class="bmt-card"
        style="--bmt-accent:${accent}; --bmt-outline:${c.outline_color || "#fff"}"
      >
        <div class="bmt-head">
          <span class="bmt-title">
            ${c.card_title ||
            (c.show_competition !== false && competition) ||
            "Ballinora"}</span
          >
        </div>

        <div
          class="bmt-scoreline ${c.show_crests ? "bmt-has-crests" : ""}"
          @click=${c.bottom_url ? () => this._open(c.bottom_url) : nothing}
        >
          ${this._side(c, left)}
          ${this._vs(c, phase, live, conflict, attention)}
          ${this._side(c, right)}
        </div>

        <div class="bmt-footer">
          ${c.show_scheduled !== false && scheduledAt
            ? html`<span class="bmt-meta">${this._formatWhen(scheduledAt)}</span>`
            : nothing}
          ${c.show_venue !== false && venue
            ? html`<span class="bmt-meta">${venue}</span>`
            : nothing}
          <span class="bmt-meta bmt-spacer"></span>
          ${c.show_confidence !== false && Number.isFinite(confidence)
            ? html`<span class="bmt-conf bmt-meta">
                <span class="bmt-conf-bar"><i style="width:${confidence}%"></i></span>
                ${confidence}%
              </span>`
            : nothing}
          ${c.show_sources !== false && source
            ? html`<span class="bmt-meta bmt-src">
                ${source}
                ${Number.isFinite(freshness)
                  ? html`<span class="bmt-fresh">${this._freshness(freshness)}</span>`
                  : nothing}
              </span>`
            : nothing}
        </div>
      </ha-card>
    `;
  }

  _side(c, team) {
    return html`
      <div class="bmt-side" part="${team.part}" @click=${() => this._open(team.url)}>
        ${c.show_crests ? this._crest(team.crest, c.outline) : nothing}
        <span class="bmt-team-name">${team.name}</span>
        <span class="bmt-score">${team.gp}</span>
        ${team.total ? html`<span class="bmt-total">${team.total} pts</span>` : nothing}
      </div>
    `;
  }

  _vs(c, phase, live, conflict, attention) {
    return html`
      <div class="bmt-vs">
        <div class="bmt-status">
          ${this._phaseChip(phase, live)}
          ${conflict ? html`<span class="bmt-mini bmt-warn">⚠</span>` : nothing}
          ${attention ? html`<span class="bmt-mini bmt-bad">⛔</span>` : nothing}
        </div>
      </div>
    `;
  }

  _open(url) {
    if (!url) return;
    if (url === "more-info") {
      const ev = new Event("hass-more-info", {
        bubbles: true,
        composed: true,
        cancelable: true,
      });
      ev.detail = { entityId: this._config?.entity };
      this.dispatchEvent(ev);
      return;
    }
    window.open(url, "_blank", "noopener");
  }

  _crest(url, outline) {
    return url
      ? html`<img
          class="bmt-crest ${outline ? "bmt-crest-outline" : ""}"
          alt=""
          src="${url}"
          loading="lazy"
        />`
      : nothing;
  }

  _phaseChip(phase, live) {
    const label = PHASE_LABELS[phase] ?? phase.replaceAll("_", " ");
    return html`<span class="bmt-chip ${live ? "bmt-chip-live" : ""}">
      ${live ? html`<span class="bmt-pulse" aria-hidden="true"></span>` : nothing}
      ${label}
    </span>`;
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
      justify-content: center;
      margin-bottom: 12px;
      border-bottom: 1px solid var(--divider-color, rgba(0, 0, 0, 0.12));
      padding-bottom: 10px;
    }
    .bmt-title {
      font-size: 14px;
      font-weight: 700;
      color: var(--primary-text-color, #1c1c1c);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      text-align: center;
    }
    .bmt-scoreline {
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 6px;
      cursor: pointer;
    }
    .bmt-side {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      min-width: 0;
      cursor: pointer;
    }
    .bmt-team-name {
      font-size: 13px;
      font-weight: 700;
      color: var(--primary-text-color, #1c1c1c);
      text-align: center;
      line-height: 1.2;
    }
    .bmt-crest {
      width: 48px;
      height: 48px;
      object-fit: contain;
      border-radius: 10px;
    }
    .bmt-crest-outline {
      box-shadow: 0 0 0 2px var(--bmt-outline);
    }
    .bmt-score {
      font-size: clamp(24px, 5vw, 38px);
      font-weight: 800;
      font-variant-numeric: tabular-nums;
      color: var(--bmt-accent, ${unsafeCSS(DEFAULT_ACCENT)});
      line-height: 1;
    }
    .bmt-total {
      font-size: 11.5px;
      font-weight: 600;
      color: var(--secondary-text-color, #727272);
      font-variant-numeric: tabular-nums;
    }
    .bmt-vs {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 0 6px;
    }
    .bmt-status {
      display: flex;
      align-items: center;
      gap: 4px;
      flex-wrap: wrap;
      justify-content: center;
    }
    .bmt-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 700;
      padding: 2px 9px;
      border-radius: 999px;
      color: var(--bmt-accent, ${unsafeCSS(DEFAULT_ACCENT)});
      background: rgba(128, 128, 160, 0.14);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .bmt-chip-live {
      color: #2e7d32;
      background: rgba(46, 125, 50, 0.14);
    }
    .bmt-mini {
      font-size: 12px;
    }
    .bmt-warn {
      color: #f57f17;
    }
    .bmt-bad {
      color: #c62828;
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
    .bmt-footer {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px 12px;
      margin-top: 12px;
      padding-top: 8px;
      border-top: 1px solid var(--divider-color, rgba(0, 0, 0, 0.12));
      font-size: 11.5px;
      color: var(--secondary-text-color, #727272);
    }
    .bmt-meta {
      white-space: nowrap;
    }
    .bmt-spacer {
      flex: 1;
    }
    .bmt-conf {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-variant-numeric: tabular-nums;
    }
    .bmt-conf-bar {
      display: inline-block;
      width: 56px;
      height: 5px;
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
    .bmt-src .bmt-fresh {
      font-style: italic;
      margin-left: 4px;
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
    @media (max-width: 420px) {
      .bmt-score {
        font-size: 26px;
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
