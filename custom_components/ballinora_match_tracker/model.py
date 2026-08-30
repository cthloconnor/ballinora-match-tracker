"""Pure data model and scoring logic for the Ballinora Match Tracker.

This module deliberately imports nothing from ``homeassistant`` so the core
scoring and normalisation logic can be unit-tested in isolation (and reused
by other consumers). All GAA scores are goals-points pairs; a goal is always
three points.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

SUPPORTED_SPORTS = frozenset({"Football", "Hurling", "Camogie", "Ladies Football"})

#: Every phase the tracker may report.
VALID_PHASES = frozenset(
    {
        "scheduled",
        "first_half",
        "half_time",
        "second_half",
        "extra_time",
        "extra_time_half_time",
        "penalties",
        "full_time_provisional",
        "full_time_confirmed",
        "postponed",
        "cancelled",
        "abandoned",
    }
)

#: Human readable labels for phases (English). Unknown phases fall back to a
#: title-cased version of the raw key.
PHASE_LABELS: dict[str, str] = {
    "scheduled": "Scheduled",
    "first_half": "First half",
    "half_time": "Half-time",
    "second_half": "Second half",
    "extra_time": "Extra time",
    "extra_time_half_time": "Extra-time interval",
    "penalties": "Penalties",
    "full_time_provisional": "Full-time · awaiting confirmation",
    "full_time_confirmed": "Full-time",
    "postponed": "Postponed",
    "cancelled": "Cancelled",
    "abandoned": "Abandoned",
}

_GOALS_POINTS_RE = re.compile(r"^\s*(\d+)\s*[-–]\s*(\d+)\s*$")


def phase_label(phase: str | None) -> str:
    """Return a human readable label for a phase key."""
    if not phase:
        return "Unknown"
    if phase in PHASE_LABELS:
        return PHASE_LABELS[phase]
    return phase.replace("_", " ").title()


def format_goals_points(goals: Any, points: Any) -> str:
    """Render goals-points as ``2-12`` (or ``0-0`` when absent)."""
    g = int(goals or 0)
    p = int(points or 0)
    return f"{g}-{p}"


def parse_goals_points(value: str | None) -> tuple[int, int] | None:
    """Parse ``2-12`` into (goals, points); returns None when unparseable."""
    if not value:
        return None
    match = _GOALS_POINTS_RE.match(str(value))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def expected_total(goals: Any, points: Any) -> int:
    """A goal is always three points."""
    return int(goals or 0) * 3 + int(points or 0)


def total_mismatch(goals: Any, points: Any, reported_total: Any) -> bool | None:
    """True when the reported total disagrees with goals*3+points.

    Returns None when there is nothing to compare (no reported total).
    A discrepancy is surfaced as a diagnostic condition; the API value is
    never silently overwritten.
    """
    if reported_total is None:
        return None
    try:
        return reported_total != expected_total(goals, points)
    except (TypeError, ValueError):
        return True


def is_goals_points_score(value: Any) -> bool:
    """True when the value looks like a rendered goals-points string."""
    return parse_goals_points(value) is not None


def parse_iso_datetime(value: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp into a timezone-aware datetime.

    naive timestamps are assumed to be in the tracker's reported timezone or
    UTC, and are tagged UTC so Home Assistant renders them consistently.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _int(value: Any) -> int | None:
    """Safely coerce to int, tolerating missing/garbage values."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(slots=True)
class Fixture:
    """Normalised, defensively parsed representation of one fixture.

    Missing or unparseable fields fall back to default values rather than
    raising, so a partially formed payload never takes the integration down.
    Attribute ``score_mismatch`` records whether the API's totals disagree
    with goals*3+points without altering the values.
    """

    fixture_id: str
    home_team: str = "Unknown"
    away_team: str = "Unknown"
    sport: str = "Football"
    competition: str | None = None
    scheduled_at: str | None = None
    timezone: str | None = None
    venue: str | None = None
    phase: str = "scheduled"
    lifecycle: str | None = None
    closed_at: str | None = None
    retained_until: str | None = None
    home_goals: int | None = None
    home_points: int | None = None
    home_total: int | None = None
    away_goals: int | None = None
    away_points: int | None = None
    away_total: int | None = None
    score_display: str | None = None
    confidence: float | None = None
    confidence_label: str | None = None
    conflict: bool = False
    operator_attention: bool = False
    is_live: bool = False
    source_id: str | None = None
    source_url: str | None = None
    source_published_at: str | None = None
    source_coverage: str | None = None
    transport_health: str | None = None
    source_freshness_seconds: int | None = None
    last_source_check_at: str | None = None
    selection_reason: str | None = None
    recommended_refresh_seconds: int | None = None
    can_check_sources_now: bool = True
    external_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    #: True when the API supplied totals do not match goals*3 + points.
    score_mismatch: bool = False

    @property
    def home_score(self) -> str:
        return format_goals_points(self.home_goals, self.home_points)

    @property
    def away_score(self) -> str:
        return format_goals_points(self.away_goals, self.away_points)

    @property
    def combined_score(self) -> str:
        return f"{self.home_score} - {self.away_score}"

    @property
    def effective_home_total(self) -> int:
        if self.home_total is not None:
            return self.home_total
        return expected_total(self.home_goals, self.home_points)

    @property
    def effective_away_total(self) -> int:
        if self.away_total is not None:
            return self.away_total
        return expected_total(self.away_goals, self.away_points)

    @property
    def full_time(self) -> bool:
        return self.phase in {"full_time_provisional", "full_time_confirmed"}

    @property
    def in_play(self) -> bool:
        return self.is_live or self.phase in {
            "first_half",
            "second_half",
            "extra_time",
            "extra_time_half_time",
            "penalties",
        }

    @property
    def device_display_name(self) -> str:
        return f"{self.home_team} vs {self.away_team}"


def _team_name(value: Any) -> str:
    """Accept either a plain name string or a ``{name: ...}`` object."""
    if isinstance(value, dict):
        return str(value.get("name") or value.get("team_name") or "Unknown")
    return str(value) if value else "Unknown"


def _team_attr(value: Any, key: str) -> int | None:
    """Read a numeric team attribute, accepting dict team objects too."""
    if isinstance(value, dict):
        return _int(value.get(key))
    return None


def build_fixture(raw: dict[str, Any]) -> Fixture:
    """Normalise one API fixture payload into a :class:`Fixture`.

    The API is assumed to be well-formed, but every access is defensive so a
    missing field degrades gracefully instead of raising.
    """
    fixture_id = str(raw.get("id") or raw.get("external_id") or "")
    if not fixture_id:
        raise ValueError("fixture payload has no id")

    home_goals = _int(raw.get("home_goals"))
    home_points = _int(raw.get("home_points"))
    away_goals = _int(raw.get("away_goals"))
    away_points = _int(raw.get("away_points"))
    home_total = _int(raw.get("home_total"))
    away_total = _int(raw.get("away_total"))

    phase = raw.get("phase") or raw.get("lifecycle") or "scheduled"
    if phase not in VALID_PHASES:
        # Fall back gracefully on unknown values rather than crashing.
        phase = "scheduled"

    fixture = Fixture(
        fixture_id=fixture_id,
        home_team=_team_name(raw.get("home_team")),
        away_team=_team_name(raw.get("away_team")),
        sport=str(raw.get("sport") or "Football"),
        competition=raw.get("competition"),
        scheduled_at=raw.get("scheduled_at"),
        timezone=raw.get("timezone"),
        venue=raw.get("venue"),
        phase=phase,
        lifecycle=raw.get("lifecycle"),
        closed_at=raw.get("closed_at"),
        retained_until=raw.get("retained_until"),
        home_goals=home_goals,
        home_points=home_points,
        home_total=home_total,
        away_goals=away_goals,
        away_points=away_points,
        away_total=away_total,
        score_display=raw.get("score_display"),
        confidence=_float(raw.get("confidence")),
        confidence_label=raw.get("confidence_label"),
        conflict=bool(raw.get("conflict", False)),
        operator_attention=bool(raw.get("operator_attention", False)),
        is_live=bool(raw.get("is_live", False)),
        source_id=raw.get("source_id"),
        source_url=raw.get("source_url"),
        source_published_at=raw.get("source_published_at"),
        source_coverage=raw.get("source_coverage"),
        transport_health=raw.get("transport_health"),
        source_freshness_seconds=_int(raw.get("source_freshness_seconds")),
        last_source_check_at=raw.get("last_source_check_at"),
        selection_reason=raw.get("selection_reason"),
        recommended_refresh_seconds=_int(raw.get("recommended_refresh_seconds")),
        can_check_sources_now=bool(raw.get("can_check_sources_now", True)),
        external_id=None if raw.get("external_id") is None else str(raw["external_id"]),
        raw=raw,
    )

    mismatch = total_mismatch(home_goals, home_points, home_total)
    away_mismatch = total_mismatch(away_goals, away_points, away_total)
    fixture.score_mismatch = bool(mismatch or away_mismatch)
    return fixture


def build_fixture_map(payload: dict[str, Any]) -> dict[str, Fixture]:
    """Turn a batched ``/fixtures/active`` payload into id -> Fixture."""
    fixtures = payload.get("fixtures") or []
    result: dict[str, Fixture] = {}
    for raw in fixtures:
        if not isinstance(raw, dict):
            continue
        try:
            fixture = build_fixture(raw)
        except ValueError:
            continue
        result[fixture.fixture_id] = fixture
    return result
