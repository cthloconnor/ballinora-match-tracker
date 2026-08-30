# Ballinora Match Tracker

A Home Assistant integration plus Lovelace cards for the
**Ballinora Match Tracker** cloud service. It keeps every active and retained
fixture in sync with one batched API request, exposes each fixture as a device
of sensors, binary sensors and a source re-check button, and renders it with
an original, accessible scoreboard card.

> Tracking football, hurling, camogie and ladies football. Scores are rendered
> GAA-style as **goals-points** (`2-12`); a goal is always three points.

## Features

**Integration**
- Single config entry with flow-time connection validation.
- One server-driven coordinator — the poll interval follows the tracker's
  `recommended_refresh_seconds`, clamped to 30–900 s. No per-entity polling.
- Every fixture becomes one device (dynamically added and renamed as matches
  appear); fixtures that leave the retention window go **unavailable** rather
  than being deleted, so history survives.
- Per fixture: phase, teams, goals-points, totals, combined & total points,
  scheduled time, venue, competition, source confidence, selected source,
  source coverage, source freshness, last source check — plus live, score-
  conflict and operator-attention flags and a **Check sources now** button.
- Tracker-level device: active fixture count, last update, an operator-
  attention flag and a **Refresh** button + `refresh` service (canonical cache
  only — never touches upstream score sources).
- 401/403 automatically start Home Assistant's reauthentication flow with a
  load-bearing `ConfigEntryAuthFailed`; nothing is lost on a transient outage.
- Diagnostics redact the token and any credentialed URLs.

**Cards** (`frontend/dist/ballinora-match-card.js`)
- `ballinora-match-card` — the fixture scoreboard: phase chip, live pulse,
  competition, teams, goals-points + totals, venue/time, confidence bar,
  source freshness; light/dark aware, reduced-motion safe, mobile-first.
- `ballinora-match-list` — every current fixture in a compact, live-first list.
- Shared visual editor (`ballinora-match-card-editor`) with an entity picker,
  toggles, optional crest URLs and an accent colour.

## Install

### Integration (HACS)

1. Add this repository as a **custom repository** (type: **Integration**).
2. Search for **Ballinora Match Tracker** in HACS → Download.
3. Restart Home Assistant (**Settings → System → Restart**).
4. **Settings → Devices → Add integration → Ballinora Match Tracker**, enter
   the tracker URL (defaults to the public service) and your access token.
5. The tracker will validate the token during setup.

### Integration (manual)

Copy `custom_components/ballinora_match_tracker/` into your
`config/custom_components/` directory, restart, then add the integration.

### Cards (resource)

Add `frontend/dist/ballinora-match-card.js` as a **JavaScript Module** resource
in **Settings → Dashboards → three-dot menu → Resources**, then pick
**Ballinora Match** or **Ballinora Matches** from **Add card → By device /
By entity**.

## Usage

Each fixture device is named after its two teams (e.g. *Ballinora vs Rivals*)
and carries:

| Domain | Entities |
|---|---|
| `sensor` | `phase` · `sport` · `home_team`/`away_team` · `competition` · `home_goals_points`/`away_goals_points` · `home_total`/`away_total` · `combined_score` · `total_points` · `scheduled_at` · `venue` · `confidence` · `confidence_label` · `source_coverage` · `selected_source` · `source_freshness` · `last_source_check` |
| `binary_sensor` | `live` · `conflict` (scores disagree) · `operator_attention` (tracker operator asks to look) |
| `button` | `check_sources_now` — ask the tracker to re-check every score source (429-rate-limited upstream; surfaced on the button) |

The tracker device (`Ballinora Match Tracker`) carries `active_fixtures`,
`tracker_last_update`, the operator-attention aggregate and the `Refresh`
button. The service `ballinora_match_tracker.refresh` does the same canonical
refresh as the button.

**Score conflicts:** when the tracker's reported totals disagree with
`goals × 3 + points`, the integration records this as the `score_mismatch`
attribute/`Score conflict` binary sensor — it never silently overwrites the
API value.

## Security

- The access token exists **only** in the encrypted config entry and the
  `Authorization` header. It is never logged, never stored in YAML, never
  exposed in diagnostics, and is masked in the config flow.
- The tracker URL is validated as HTTPS (HTTP allowed only for loopback).

## Testing

See [`docs/testing.md`](docs/testing.md). Pure-logic and API tests run without
Home Assistant; the integration suite needs the HA dev environment and is
provided but must be run on a machine with the full HA test stack installed.

## Releasing

`node script/release.mjs bump patch` bumps every version in sync, rebuilds the
card and tags `vX.Y.Z`; pushing that tag drafts the GitHub release with a
changelog automatically. Full flow in [`docs/releasing.md`](docs/releasing.md).

## Uninstall

Remove the config entry (**Settings → Devices → Ballinora Match Tracker →
delete**), delete the custom component / HACS entry, and remove the card
resource. Removing the integration deletes its entities but leaves devices
(besides the tracker device) registered so real-world device history is
preserved.

## Licence

MIT.