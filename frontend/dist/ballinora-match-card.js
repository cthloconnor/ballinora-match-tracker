// src/ballinora-match-card.js
import { LitElement as LitElement4 } from "lit";

// src/match-card.js
import { LitElement, html, css, nothing, unsafeCSS } from "lit";

// src/entities.js
function splitEntity(entityId) {
  const clean = String(entityId || "").trim();
  const dot = clean.indexOf(".");
  if (dot <= 0) {
    return { domain: "", object: clean, fixture: clean };
  }
  const domain = clean.slice(0, dot);
  const object = clean.slice(dot + 1);
  const underscore = object.lastIndexOf("_");
  return {
    domain,
    object,
    fixture: underscore > 0 ? object.slice(0, underscore) : object
  };
}
function binaryId(entityId, suffix) {
  const { fixture } = splitEntity(entityId);
  return fixture ? `binary_sensor.${fixture}_${suffix}` : null;
}
function stateOf(hass, entityId) {
  const entity = hass?.states?.[entityId];
  return entity ? entity.state : void 0;
}

// src/match-card.js
var PHASE_LABELS = {
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
  abandoned: "Abandoned"
};
var DEFAULT_ACCENT = "#5c6bc0";
var fmt = new Intl.DateTimeFormat("en-IE", {
  weekday: "short",
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit"
});
var BallinoraMatchCard = class extends LitElement {
  static properties = {
    hass: { type: Object },
    _config: { state: true }
  };
  static getConfigElement() {
    return document.createElement("ballinora-match-card-editor");
  }
  static getStubConfig(hass, entities, entitiesFill) {
    const entity = entities.find(
      (eid) => eid.startsWith("sensor.") && eid.endsWith("_phase") && !eid.includes("tracker_")
    );
    return {
      entity: entity || "",
      show_crests: false,
      show_competition: true,
      show_scheduled: true,
      show_venue: true,
      show_confidence: true,
      show_sources: true
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
    const live = stateOf(this.hass, binaryId(c.entity, "live")) === "on";
    const conflict = stateOf(this.hass, binaryId(c.entity, "conflict")) === "on";
    const attention = stateOf(this.hass, binaryId(c.entity, "operator_attention")) === "on";
    const source = stateOf(this.hass, `sensor.${fixture}_selected_source`);
    const freshness = Number(
      stateOf(this.hass, `sensor.${fixture}_source_freshness`)
    );
    const accent = c.accent || DEFAULT_ACCENT;
    const home = {
      part: "home",
      name: homeTeam,
      gp: homeGP,
      total: homeTotal,
      crest: c.home_crest,
      url: c.home_url
    };
    const away = {
      part: "away",
      name: awayTeam,
      gp: awayGP,
      total: awayTotal,
      crest: c.away_crest,
      url: c.away_url
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
            ${c.card_title || c.show_competition !== false && competition || "Ballinora"}</span
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
          ${c.show_scheduled !== false && scheduledAt ? html`<span class="bmt-meta">${this._formatWhen(scheduledAt)}</span>` : nothing}
          ${c.show_venue !== false && venue ? html`<span class="bmt-meta">${venue}</span>` : nothing}
          <span class="bmt-meta bmt-spacer"></span>
          ${c.show_confidence !== false && Number.isFinite(confidence) ? html`<span class="bmt-conf bmt-meta">
                <span class="bmt-conf-bar"><i style="width:${confidence}%"></i></span>
                ${confidence}%
              </span>` : nothing}
          ${c.show_sources !== false && source ? html`<span class="bmt-meta bmt-src">
                ${source}
                ${Number.isFinite(freshness) ? html`<span class="bmt-fresh">${this._freshness(freshness)}</span>` : nothing}
              </span>` : nothing}
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
        cancelable: true
      });
      ev.detail = { entityId: this._config?.entity };
      this.dispatchEvent(ev);
      return;
    }
    window.open(url, "_blank", "noopener");
  }
  _crest(url, outline) {
    return url ? html`<img
          class="bmt-crest ${outline ? "bmt-crest-outline" : ""}"
          alt=""
          src="${url}"
          loading="lazy"
        />` : nothing;
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
};
customElements.define("ballinora-match-card", BallinoraMatchCard);

// src/list-card.js
import { LitElement as LitElement2, html as html2, css as css2, nothing as nothing2 } from "lit";
var PHASE_LABELS2 = {
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
  abandoned: "Abandoned"
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
var BallinoraMatchList = class extends LitElement2 {
  static properties = {
    hass: { type: Object },
    _config: { state: true }
  };
  static getConfigElement() {
    return document.createElement("ballinora-match-card-editor");
  }
  static getStubConfig(hass, entities, entitiesFill) {
    return {};
  }
  setConfig(config) {
    this._config = { ...config || {} };
  }
  _fixtures() {
    if (!this.hass) return [];
    const fixtures = /* @__PURE__ */ new Map();
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
        rank: phaseRank(phase)
      });
    }
    list.sort((a, b) => a.rank - b.rank || a.home.localeCompare(b.home));
    return list;
  }
  render() {
    const fixtures = this._fixtures();
    if (!fixtures.length) {
      return html2`<ha-card class="bmt-list" part="empty">
        <span>No fixtures from the Ballinora Match Tracker.</span>
      </ha-card>`;
    }
    const rows = fixtures.map(
      (f) => html2`
        <div class="bmt-row ${f.live ? "is-live" : ""}">
          <span class="bmt-row-phase">
            ${f.live ? html2`<span class="bmt-dot" aria-hidden="true"></span>` : nothing2}
            ${PHASE_LABELS2[f.phase] ?? f.phase}
          </span>
          <span class="bmt-row-teams">
            <span class="bmt-row-home">${f.home}</span> vs
            <span class="bmt-row-away">${f.away}</span>
          </span>
          <span class="bmt-row-score">${f.homeGP} · ${f.awayGP}</span>
          ${f.competition ? html2`<span class="bmt-row-comp">${f.competition}</span>` : nothing2}
        </div>
      `
    );
    return html2`<ha-card class="bmt-list">${rows}</ha-card>`;
  }
  static styles = css2`
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
};
customElements.define("ballinora-match-list", BallinoraMatchList);

// src/editor.js
import { LitElement as LitElement3, html as html3, css as css3, nothing as nothing3 } from "lit";
function fireEvent(node, type, detail, options) {
  const event = new Event(type, { bubbles: true, composed: true, ...options });
  event.detail = detail;
  node.dispatchEvent(event);
  return event;
}
var FIXTURE_ENTITY_RE = /^sensor\.(?!tracker_).+_phase$/;
var BallinoraMatchCardEditor = class extends LitElement3 {
  static properties = {
    hass: { type: Object },
    config: { type: Object }
  };
  setConfig(config) {
    this.config = config;
  }
  get value() {
    return this.config;
  }
  _update(merge) {
    fireEvent(this, "config-changed", { config: { ...this.config, ...merge } });
  }
  render() {
    if (!this.hass || !this.config) {
      return html3`<span>Loading editor…</span>`;
    }
    const c = this.config;
    const phaseEntities = Object.keys(this.hass.states).filter(
      (eid) => FIXTURE_ENTITY_RE.test(eid)
    );
    return html3`
      <div class="bmt-editor">
        <div class="bmt-field">
          <label>Fixture</label>
          <ha-entity-picker
            .hass=${this.hass}
            .value=${c.entity}
            .includeDomains=${["sensor"]}
            .entities=${phaseEntities}
            @value-changed=${(e) => this._update({ entity: e.detail.value })}
          ></ha-entity-picker>
        </div>

        <div class="bmt-field">
          <label>Title override (optional)</label>
          <ha-textfield
            .value=${c.card_title || ""}
            placeholder="e.g. Senior Championship Final"
            @change=${(e) => this._update({ card_title: e.target.value || void 0 })}
          ></ha-textfield>
        </div>

        <div class="bmt-toggles">
          ${this._toggle("Competition", c.show_competition !== false, "show_competition")}
          ${this._toggle("Venue", c.show_venue !== false, "show_venue")}
          ${this._toggle("Scheduled time", c.show_scheduled !== false, "show_scheduled")}
          ${this._toggle("Confidence", c.show_confidence !== false, "show_confidence")}
          ${this._toggle("Source", c.show_sources !== false, "show_sources")}
          ${this._toggle("Crests", c.show_crests === true, "show_crests")}
          ${this._toggle("Outline crests", c.outline === true, "outline")}
        </div>

        <div class="bmt-field">
          <label>Home side</label>
          <select @change=${(e) => this._update({ home_side: e.target.value })}>
            <option value="left" ?selected=${c.home_side !== "right"}>Left</option>
            <option value="right" ?selected=${c.home_side === "right"}>Right</option>
          </select>
        </div>

        ${c.outline ? html3`
              <div class="bmt-field">
                <label>Outline colour</label>
                <ha-textfield
                  .value=${c.outline_color || ""}
                  placeholder="#ffffff"
                  @change=${(e) => this._update({ outline_color: e.target.value || void 0 })}
                ></ha-textfield>
              </div>
            ` : nothing3}

        ${c.show_crests ? html3`
              <div class="bmt-field">
                <label>Home crest URL</label>
                <ha-textfield
                  .value=${c.home_crest || ""}
                  @change=${(e) => this._update({ home_crest: e.target.value || void 0 })}
                ></ha-textfield>
              </div>
              <div class="bmt-field">
                <label>Away crest URL</label>
                <ha-textfield
                  .value=${c.away_crest || ""}
                  @change=${(e) => this._update({ away_crest: e.target.value || void 0 })}
                ></ha-textfield>
              </div>
            ` : nothing3}

        <div class="bmt-field">
          <label>Accent colour</label>
          <ha-textfield
            .value=${c.accent || ""}
            placeholder="#5c6bc0"
            @change=${(e) => this._update({ accent: e.target.value || void 0 })}
          ></ha-textfield>
        </div>

        <div class="bmt-field">
          <label>Home tap URL</label>
          <ha-textfield
            .value=${c.home_url || ""}
            placeholder="https://… or more-info"
            @change=${(e) => this._update({ home_url: e.target.value || void 0 })}
          ></ha-textfield>
        </div>
        <div class="bmt-field">
          <label>Away tap URL</label>
          <ha-textfield
            .value=${c.away_url || ""}
            placeholder="https://… or more-info"
            @change=${(e) => this._update({ away_url: e.target.value || void 0 })}
          ></ha-textfield>
        </div>
        <div class="bmt-field">
          <label>Tap URL for scoreboard (optional)</label>
          <ha-textfield
            .value=${c.bottom_url || ""}
            placeholder="https://… or more-info"
            @change=${(e) => this._update({ bottom_url: e.target.value || void 0 })}
          ></ha-textfield>
        </div>
      </div>
    `;
  }
  _toggle(label, checked, prop) {
    return html3`
      <ha-switch
        .checked=${checked}
        @change=${(e) => this._update({ [prop]: e.target.checked })}
      ></ha-switch>
      <span>${label}</span>
    `;
  }
  static styles = css3`
    .bmt-editor {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .bmt-field {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .bmt-field label {
      font-size: 12px;
      color: var(--secondary-text-color, #727272);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .bmt-toggles {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
    }
    .bmt-toggles ha-switch {
      margin-right: 6px;
    }
  `;
};
customElements.define("ballinora-match-card-editor", BallinoraMatchCardEditor);

// src/ballinora-match-card.js
var ballinoraMatchCardVersion = "1.0.0";
if (typeof window !== "undefined" && window.customCards) {
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "ballinora-match-card",
    name: "Ballinora Match",
    description: "Live score, phase and source confidence for one Ballinora fixture",
    preview: false
  });
  window.customCards.push({
    type: "ballinora-match-list",
    name: "Ballinora Matches",
    description: "All current Ballinora fixtures in a compact list",
    preview: false
  });
}
export {
  BallinoraMatchCard,
  BallinoraMatchList,
  ballinoraMatchCardVersion
};
//# sourceMappingURL=ballinora-match-card.js.map
