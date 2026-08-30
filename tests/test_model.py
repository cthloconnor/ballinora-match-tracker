"""Tests for the pure scoring/normalisation model (runs without HA)."""

from __future__ import annotations

import pytest

from custom_components.ballinora_match_tracker.model import (
    build_fixture,
    build_fixture_map,
    expected_total,
    format_goals_points,
    is_goals_points_score,
    parse_goals_points,
    parse_iso_datetime,
    phase_label,
    total_mismatch,
)


@pytest.mark.parametrize(
    ("goals", "points", "expected"),
    [
        (2, 12, "2-12"),
        (0, 0, "0-0"),
        (None, None, "0-0"),
        ("1", "3", "1-3"),
    ],
)
def test_format_goals_points(goals, points, expected):
    assert format_goals_points(goals, points) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2-12", (2, 12)),
        ("2 – 12", (2, 12)),  # en dash
        (" 0-0 ", (0, 0)),
        ("", None),
        (None, None),
        ("two-two", None),
        ("12", None),
    ],
)
def test_parse_goals_points(value, expected):
    assert parse_goals_points(value) == expected


@pytest.mark.parametrize(
    ("goals", "points", "expected"),
    [(2, 12, 18), (1, 0, 3), (0, 0, 0), (3, 10, 19)],
)
def test_expected_total_goal_is_three_points(goals, points, expected):
    assert expected_total(goals, points) == expected


def test_total_mismatch_detected():
    assert total_mismatch(2, 12, 18) is False
    assert total_mismatch(2, 12, 17) is True
    assert total_mismatch(2, 12, None) is None


def test_is_goals_points_score():
    assert is_goals_points_score("3-14")
    assert not is_goals_points_score("abc")


def test_parse_iso_datetime():
    parsed = parse_iso_datetime("2026-08-30T14:00:00Z")
    assert parsed is not None and parsed.tzinfo is not None
    assert parse_iso_datetime("not-a-date") is None
    assert parse_iso_datetime(None) is None


def test_phase_label():
    assert phase_label("full_time_confirmed") == "Full-time"
    assert phase_label("some_novel_phase") == "Some Novel Phase"
    assert phase_label(None) == "Unknown"


def test_build_fixture_basic():
    fix = build_fixture(
        {
            "id": "abc123",
            "home_team": {"name": "Ballinora"},
            "away_team": "Cork County",
            "sport": "Hurling",
            "phase": "second_half",
            "home_goals": 2,
            "home_points": 12,
            "home_total": 18,
            "away_goals": 1,
            "away_points": 9,
            "away_total": None,
            "competition": "County Championship",
            "is_live": True,
        }
    )
    assert fix.fixture_id == "abc123"
    assert fix.home_team == "Ballinora"
    assert str(fix.home_score) == "2-12"
    assert fix.effective_home_total == 18
    assert fix.effective_away_total == expected_total(1, 9)
    assert fix.in_play
    assert fix.score_mismatch is False
    assert fix.device_display_name == "Ballinora vs Cork County"


def test_build_fixture_mismatch_recorded_not_overwritten():
    fix = build_fixture(
        {
            "id": "x1",
            "home_goals": 2,
            "home_points": 12,
            "home_total": 30,  # disagreees with 2*3+12 == 18
        }
    )
    assert fix.score_mismatch is True
    assert fix.home_total == 30  # API value kept, never overwritten


def test_build_fixture_missing_id_raises():
    with pytest.raises(ValueError):
        build_fixture({})


def test_build_fixture_graceful_on_partial_payload():
    fix = build_fixture({"id": "p1"})
    assert fix.home_team == "Unknown"
    assert fix.phase == "scheduled"
    assert str(fix.home_score) == "0-0"
    assert fix.score_mismatch is False


def test_build_fixture_unknown_phase_falls_back():
    fix = build_fixture({"id": "p2", "phase": "weird_key"})
    assert fix.phase == "scheduled"


def test_build_fixture_map_skips_invalid():
    payload = {
        "fixtures": [
            {"id": "a", "home_team": "X", "away_team": "Y"},
            {"home_team": "no id"},
            "not-a-dict",
        ]
    }
    result = build_fixture_map(payload)
    assert list(result) == ["a"]
    assert result["a"].away_team == "Y"
