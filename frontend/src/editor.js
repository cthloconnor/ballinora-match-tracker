/** Visual editor for the Ballinora Match Tracker cards. */
import { LitElement, html, css, nothing } from "lit";

import { splitEntity } from "./entities.js";

function fireEvent(node, type, detail, options) {
  const event = new Event(type, { bubbles: true, composed: true, ...options });
  event.detail = detail;
  node.dispatchEvent(event);
  return event;
}

const FIXTURE_ENTITY_RE = /^sensor\.(?!tracker_).+_phase$/;

export class BallinoraMatchCardEditor extends LitElement {
  static properties = {
    hass: { type: Object },
    config: { type: Object },
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
      return html`<span>Loading editor…</span>`;
    }
    const c = this.config;
    const phaseEntities = Object.keys(this.hass.states).filter((eid) =>
      FIXTURE_ENTITY_RE.test(eid),
    );

    return html`
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
            @change=${(e) => this._update({ card_title: e.target.value || undefined })}
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

        ${c.outline
          ? html`
              <div class="bmt-field">
                <label>Outline colour</label>
                <ha-textfield
                  .value=${c.outline_color || ""}
                  placeholder="#ffffff"
                  @change=${(e) =>
                    this._update({ outline_color: e.target.value || undefined })}
                ></ha-textfield>
              </div>
            `
          : nothing}

        ${c.show_crests
          ? html`
              <div class="bmt-field">
                <label>Home crest URL</label>
                <ha-textfield
                  .value=${c.home_crest || ""}
                  @change=${(e) =>
                    this._update({ home_crest: e.target.value || undefined })}
                ></ha-textfield>
              </div>
              <div class="bmt-field">
                <label>Away crest URL</label>
                <ha-textfield
                  .value=${c.away_crest || ""}
                  @change=${(e) =>
                    this._update({ away_crest: e.target.value || undefined })}
                ></ha-textfield>
              </div>
            `
          : nothing}

        <div class="bmt-field">
          <label>Accent colour</label>
          <ha-textfield
            .value=${c.accent || ""}
            placeholder="#5c6bc0"
            @change=${(e) => this._update({ accent: e.target.value || undefined })}
          ></ha-textfield>
        </div>

        <div class="bmt-field">
          <label>Home tap URL</label>
          <ha-textfield
            .value=${c.home_url || ""}
            placeholder="https://… or more-info"
            @change=${(e) => this._update({ home_url: e.target.value || undefined })}
          ></ha-textfield>
        </div>
        <div class="bmt-field">
          <label>Away tap URL</label>
          <ha-textfield
            .value=${c.away_url || ""}
            placeholder="https://… or more-info"
            @change=${(e) => this._update({ away_url: e.target.value || undefined })}
          ></ha-textfield>
        </div>
        <div class="bmt-field">
          <label>Tap URL for scoreboard (optional)</label>
          <ha-textfield
            .value=${c.bottom_url || ""}
            placeholder="https://… or more-info"
            @change=${(e) => this._update({ bottom_url: e.target.value || undefined })}
          ></ha-textfield>
        </div>
      </div>
    `;
  }

  _toggle(label, checked, prop) {
    return html`
      <ha-switch
        .checked=${checked}
        @change=${(e) => this._update({ [prop]: e.target.checked })}
      ></ha-switch>
      <span>${label}</span>
    `;
  }

  static styles = css`
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
}

customElements.define("ballinora-match-card-editor", BallinoraMatchCardEditor);