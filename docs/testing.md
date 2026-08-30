# Testing

Two tiers of tests. Nothing here touches a running Home Assistant instance.

## Pure-logic tier (runs anywhere)

`model.py` and `api.py` deliberately import nothing from Home Assistant (the
API client only needs `aiohttp`), so their tests run in a plain venv.

```bash
python -m venv .venv
.venv/bin/pip install pytest pytest-asyncio aioresponses "aiohttp<3.12"
.venv/bin/pip install ruff
.venv/bin/ruff check custom_components/ tests/
.venv/bin/pytest tests/ -q
```

`aiohttp` is pinned below 3.12 only because `aioresponses` does not yet support
the newer client internals.

`tests/ha_required/` is collected only when `homeassistant` is importable; in
a plain venv it is skipped automatically.

## Integration tier (needs the HA dev environment)

The integration suite exercises the config flow, coordinator, platform entity
onboarding and diagnostics redaction. It requires Home Assistant's test stack,
which this container cannot install (it builds `lru-dict` from source and has
no C toolchain), so it is **delivered but must be executed on a dev machine**.

```bash
pip install homeassistant pytest-homeassistant-custom-component \
  pytest pytest-asyncio aioresponses "aiohttp<3.12"
pytest tests/ -q            # runs EVERYTHING, including tests/ha_required/
```

If you use `hassfest`-style tooling (HA core dev environment), this repo's
structure — `custom_components/ballinora_match_tracker/` plus `tests/` — slots
straight in.

## Frontend

```bash
cd frontend
npm install --include=dev   # NODE_ENV is often "production"; be explicit
npm run build               # -> dist/ballinora-match-card.js
npm test                    # vitest + happy-dom (rendering smoke tests)
```