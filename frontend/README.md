# Ballinora Match Tracker cards (frontend)

Two self-contained Lovelace cards plus a shared visual editor:

- `ballinora-match-card` — single fixture scoreboard
- `ballinora-match-list` — compact list of every current fixture
- `ballinora-match-card-editor` — shared visual editor with entity picker

All public styling rolls with Home Assistant's design tokens (light/dark),
is mobile-first, respects `prefers-reduced-motion`, and reads article-order
DOM for screen readers. No card dependencies outside `lit`, which Home
Assistant provides at runtime and is therefore kept external to the bundle.

## Build

```bash
npm install --include=dev
npm run build        # -> dist/ballinora-match-card.js (single file)
npm run watch        # continuous rebuild for development
```

## Test

```bash
npm test             # vitest + happy-dom; entity derivation + render smoke tests
```

## Structure

- `src/entities.js` — entity-id derivation shared by both cards
- `src/match-card.js` — the scoreboard card
- `src/list-card.js` — the fixtures list
- `src/editor.js` — visual editor (config form)
- `src/ballinora-match-card.js` — entry point that registers everything and
  advertises the cards in the picker
- `dist/ballinora-match-card.js` — built resource to add in HA Resources