# Dashboard examples

Add the card resource first (`frontend/dist/ballinora-match-card.js`), then use
these snippets or build in the visual editor from **Add card → By device**.

## One fixture, scoreboard

```yaml
type: custom:ballinora-match-card
entity: sensor.f1_phase        # any fixture entity works; siblings are derived
show_competition: true
show_venue: true
show_scheduled: true
show_confidence: true
show_sources: true
show_crests: false
home_crest: https://example.org/ballinora.png
away_crest: https://example.org/rivals.png
accent: "#5c6bc0"
```

## Every fixture, compact list

```yaml
type: custom:ballinora-match-list
```

## Side-by-side on a wide screen

```yaml
type: horizontal-stack
cards:
  - type: custom:ballinora-match-card
    entity: sensor.f1_phase
  - type: custom:ballinora-match-card
    entity: sensor.f2_phase
    show_confidence: false
```

## Entities worth pinning to a dashboard

For a fixture, use the device via **By device** for everything, or pick:

- `sensor.f1_combined_score` / `sensor.f1_home_goals_points` (attributes carry
  the goals, points and totals breakdown)
- `binary_sensor.f1_live`, `sensor.f1_phase`
- `button.f1_check_sources_now` for the manual re-check
- `sensor.tracker_last_update` on the tracker device