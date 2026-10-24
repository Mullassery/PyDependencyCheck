"""Terminal dashboard rendering tests (Rich console captured to a buffer)."""

from __future__ import annotations

import io
from types import SimpleNamespace

import pytest
from pydependencycheck import dashboard
from pydependencycheck.dashboard import CLIDashboard
from rich.console import Console


@pytest.fixture()
def rendered(monkeypatch):
    output = io.StringIO()
    monkeypatch.setattr(dashboard, "console", Console(file=output, width=120, force_terminal=False))
    return output


def _dashboard(tmp_path):
    dash = CLIDashboard(str(tmp_path))
    return dash


def test_show_summary_renders_counts(rendered, tmp_path):
    dash = _dashboard(tmp_path)
    scan = {
        "dependencies": [
            {"name": "flask", "version": "3.0", "direct": True},
            {"name": "requests", "version": "2.32", "direct": True},
            {"name": "urllib3", "version": "2.2", "direct": False},
        ]
    }
    dash.show_summary(scan, health_score=85)
    text = rendered.getvalue()
    assert "Total Dependencies" in text
    assert "Direct" in text
    assert "flask" in text
    assert "85/100" in text


def test_show_summary_handles_empty_scan(rendered, tmp_path):
    _dashboard(tmp_path).show_summary({"dependencies": []})
    assert "Total Dependencies" in rendered.getvalue()


def test_drift_requires_two_snapshots(rendered, tmp_path, monkeypatch):
    dash = _dashboard(tmp_path)
    monkeypatch.setattr(dash.storage, "get_snapshot_history", lambda *a, **k: [])
    dash.show_drift_report(str(tmp_path))
    assert "Need at least 2 snapshots" in rendered.getvalue()


def test_timeline_with_no_snapshots(rendered, tmp_path, monkeypatch):
    dash = _dashboard(tmp_path)
    monkeypatch.setattr(dash.storage, "get_snapshot_history", lambda *a, **k: [])
    dash.show_timeline(str(tmp_path))
    assert "No snapshots" in rendered.getvalue()


def test_health_details_renders_factors(rendered, tmp_path):
    dash = _dashboard(tmp_path)
    score = SimpleNamespace(
        score=72,
        rating="Good",
        vulnerabilities_score=90,
        maintenance_score=80,
        quality_score=65,
        complexity_score=40,
        issues=["one issue"],
        recommendations=["one recommendation"],
    )
    dash.show_health_details(score)
    text = rendered.getvalue()
    assert "Health Score Breakdown" in text
    assert "Overall Health" in text
    assert "one issue" in text
    assert "one recommendation" in text


def test_score_helpers():
    assert "✅" in str(CLIDashboard._score_to_rich_text(90))
    assert "👍" in str(CLIDashboard._score_to_rich_text(70))
    assert "⚠️" in str(CLIDashboard._score_to_rich_text(55))
    assert "🚨" in str(CLIDashboard._score_to_rich_text(10))

    assert CLIDashboard._score_to_bar(100) == "█" * 10
    assert CLIDashboard._score_to_bar(50) == "█" * 5 + "░" * 5

    assert CLIDashboard._get_factor_rating(90) == "Excellent"
    assert CLIDashboard._get_factor_rating(70) == "Good"
    assert CLIDashboard._get_factor_rating(55) == "Fair"
    assert CLIDashboard._get_factor_rating(10) == "Poor"


def test_drift_report_renders_changes(rendered, tmp_path, monkeypatch):
    from datetime import datetime

    dash = _dashboard(tmp_path)
    current = SimpleNamespace(
        timestamp=datetime(2026, 10, 24),
        dependencies={"dependencies": [{"name": "flask", "direct": True}]},
    )
    previous = SimpleNamespace(
        timestamp=datetime(2026, 10, 23),
        dependencies={"dependencies": [{"name": "django", "direct": True}]},
    )
    monkeypatch.setattr(dash.storage, "get_snapshot_history", lambda *a, **k: [current, previous])
    monkeypatch.setattr(
        dash.storage,
        "_compute_drift",
        lambda old, new: {
            "added": ["flask"],
            "removed": ["django"],
            "upgraded": [],
            "downgraded": [],
            "changed": True,
        },
    )
    dash.show_drift_report(str(tmp_path))
    text = rendered.getvalue()
    assert "Dependency Drift Analysis" in text
    assert "Added" in text
    assert "Removed" in text


def test_timeline_renders_snapshots(rendered, tmp_path, monkeypatch):
    from datetime import datetime

    dash = _dashboard(tmp_path)
    history = [
        SimpleNamespace(
            timestamp=datetime.now(),
            dependencies={"dependencies": [{"name": "flask", "direct": True}]},
            health_score=80,
        ),
        SimpleNamespace(
            timestamp=datetime.now(),
            dependencies={
                "dependencies": [
                    {"name": "flask", "direct": True},
                    {"name": "requests", "direct": False},
                ]
            },
            health_score=70,
        ),
    ]
    monkeypatch.setattr(dash.storage, "get_snapshot_history", lambda *a, **k: history)
    dash.show_timeline(str(tmp_path))
    text = rendered.getvalue()
    assert "Dependency Timeline" in text
    assert "flask" not in text  # table lists counts, not package names
    assert "2" in text
