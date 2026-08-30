"""Constants for the Ballinora Match Tracker integration."""

DOMAIN = "ballinora_match_tracker"

CONF_URL = "url"
CONF_TOKEN = "token"

DEFAULT_URL = "https://ballinora-match-tracker.cthloconnor.workers.dev"

#: Path of the batched endpoint that returns all active/retained fixtures.
API_ACTIVE_FIXTURES_PATH = "api/v1/fixtures/active"
#: Path that triggers a bounded source check for one fixture.
API_CHECK_SOURCES_PATH = "api/v1/fixtures/{fixture_id}/check-sources-now"

#: Adaptive polling bounds (seconds). We always honour the server's
#: recommended_refresh_seconds unless it falls outside these bounds.
MIN_REFRESH_SECONDS = 30
MAX_REFRESH_SECONDS = 900
DEFAULT_REFRESH_SECONDS = 60
#: Interval used when no fixtures are live (if the server sends no hint).
DEFAULT_LIVE_REFRESH_SECONDS = 30
#: HTTP timeout for a single API request.
HTTP_TIMEOUT_SECONDS = 15

MANUFACTURER = "Ballinora"
MODEL_TRACKER = "Match Tracker service"

#: Stable identifier for the single config entry.
ENTRY_UNIQUE_ID = "ballinora_match_tracker"

#: Device identifier for the integration-level tracker device.
TRACKER_DEVICE_IDENTIFIER = "tracker"
#: Device identifier prefix for per-fixture devices.
FIXTURE_DEVICE_PREFIX = "fixture_"

SENSOR = "sensor"
BINARY_SENSOR = "binary_sensor"
BUTTON = "button"

PLATFORMS = [SENSOR, BINARY_SENSOR, BUTTON]

#: Sensor platform translation keys (per-fixture entities).
PHASE = "phase"
SPORT = "sport"
COMPETITION = "competition"
HOME_GOALS_POINTS = "home_goals_points"
AWAY_GOALS_POINTS = "away_goals_points"
HOME_TOTAL = "home_total"
AWAY_TOTAL = "away_total"
COMBINED_SCORE = "combined_score"
SCHEDULED_AT = "scheduled_at"
VENUE = "venue"
CONFIDENCE = "confidence"
CONFIDENCE_LABEL = "confidence_label"
SOURCE_COVERAGE = "source_coverage"
SELECTED_SOURCE = "selected_source"
SOURCE_FRESHNESS = "source_freshness"
LAST_SOURCE_CHECK = "last_source_check"
TOTAL_POINTS = "total_points"

#: Sensor translation keys for the integration-level tracker device.
ACTIVE_FIXTURES = "active_fixtures"
TRACKER_LAST_UPDATE = "tracker_last_update"
TRACKER_OPS_ATTENTION = "tracker_ops_attention"

#: Button platform translation keys.
CHECK_SOURCES_NOW = "check_sources_now"
REFRESH = "refresh"

#: Service name for refreshing the canonical cache.
SERVICE_REFRESH = "refresh"
REFRESH_SECONDS_ATTR = "recommended_refresh_seconds"
RETRY_AFTER_ATTR = "retry_after"
LAST_CHECK_RESULT_ATTR = "last_check_result"

#: Shared icons.
LIVE_ICON = "mdi:radio-tower"
CONFLICT_ICON = "mdi:alert-circle-outline"
BROKEN_ICON = "mdi:alert-octagon-outline"
