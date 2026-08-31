# Dashboard examples

Add the card resource first (`frontend/dist/ballinora-match-card.js`), then use
these snippets or build in the visual editor from **Add card → By device**.

The single‑fixture card is a scoreboard in the style of the popular
**teamtracker** card, but the source is always the **Ballinora Match Tracker
app** — never ESPN. Teams sit on opposite sides with the goals‑points score
between them, the league/competition (or a `card_title` override) across the
top, and the game state / kick‑off / venue / confidence / source along the
bottom.

## One fixture, scoreboard

```yaml
type: custom:ballinora-match-card
entity: sensor.f1_phase        # any fixture entity works; siblings are derived
card_title: Senior Championship          # overrides the competition heading
show_competition: true
show_venue: true
show_scheduled: true
show_confidence: true
show_sources: true
show_crests: true
home_crest: https://example.org/ballinora.png
away_crest: https://example.org/rivals.png
outline: true                            # teamtracker-style crest outline
outline_color: "#ffffff"
home_side: left                          # or "right" to flip home to the right
accent: "#5c6bc0"
home_url: https://example.org/ballinora  # tap a team to open a URL (or "more-info")
away_url: more-info
bottom_url: https://example.org
```

### Card options

| Option | Default | Meaning |
| --- | --- | --- |
| `entity` | — (required) | Any fixture entity; the rest of that fixture's entities are derived. |
| `card_title` | league/competition | Text at the top of the scoreboard. |
| `show_competition` | `true` | Show the competition as the title. |
| `show_scheduled` | `true` | Show kick‑off date/time in the footer. |
| `show_venue` | `true` | Show venue in the footer. |
| `show_confidence` | `true` | Show the source‑selection confidence bar. |
| `show_sources` | `true` | Show the selected source + freshness. |
| `show_crests` | `false` | Show team crests next to the names. |
| `home_crest` / `away_crest` | — | URL of a team logo image. |
| `outline` | `false` | Outline the crests (teamtracker‑style, helps on dark themes). |
| `outline_color` | `#ffffff` | Outline colour when `outline` is on. |
| `home_side` | `left` | `left` or `right`; home team on the left or right of the scoreboard. |
| `accent` | `#5c6bc0` | Accent colour for scores/status. |
| `home_url` / `away_url` | — | Tap a team to open a URL, or `more-info`. |
| `bottom_url` | — | Tap the scoreboard centre to open a URL, or `more-info`. |

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