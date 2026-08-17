"""Tests for the SQLite-backed snapshot/drift storage layer.

These are, in large part, regression tests: `SnapshotStorage._init_db()`
used to contain an inline `INDEX(...)` column declaration inside two
`CREATE TABLE` statements, which is valid in MySQL but is a hard SQLite
syntax error. That meant *every* command touching storage --
`scan --save-snapshot`, `snapshot`, `history`, `drift`, and (via
CLIDashboard) `health` -- crashed unconditionally the moment
`SnapshotStorage()` was constructed. This was invisible before because the
prior Python test suite never actually instantiated it (see the removed
`pass`-stub tests).
"""

from pydependencycheck.storage import SnapshotStorage


class TestSnapshotStorageInitialization:
    def test_init_db_does_not_raise(self, tmp_path):
        """Regression test for the invalid inline INDEX(...) syntax bug."""
        SnapshotStorage(cache_dir=str(tmp_path))  # must not raise

    def test_creates_expected_tables(self, tmp_path):
        import sqlite3

        storage = SnapshotStorage(cache_dir=str(tmp_path))
        conn = sqlite3.connect(storage.db_path)
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()

        assert {"snapshots", "vulnerabilities", "usage_analysis", "blame_log", "drift_baselines"} <= tables


class TestSnapshotSaveAndRetrieve:
    def test_save_and_get_latest_snapshot(self, tmp_path):
        storage = SnapshotStorage(cache_dir=str(tmp_path))
        scan_result = {
            "dependencies": [{"name": "requests", "direct": True}],
            "direct_count": 1,
            "transitive_count": 0,
        }

        snapshot_id = storage.save_snapshot("/some/project", scan_result, health_score=85)
        assert snapshot_id > 0

        latest = storage.get_latest_snapshot("/some/project")
        assert latest is not None
        assert latest.health_score == 85
        assert latest.dependencies["dependencies"][0]["name"] == "requests"

    def test_get_latest_snapshot_returns_none_when_empty(self, tmp_path):
        storage = SnapshotStorage(cache_dir=str(tmp_path))
        assert storage.get_latest_snapshot("/nonexistent/project") is None

    def test_identical_back_to_back_snapshots_both_save(self, tmp_path):
        """Regression test: an over-strict UNIQUE(graph_hash) /
        UNIQUE(project_path, timestamp) schema used to silently drop the
        second snapshot whenever a project was scanned twice with no
        dependency changes (or twice within the same second) -- exactly
        the "nothing changed" case that `history`/`drift` need to record.
        """
        storage = SnapshotStorage(cache_dir=str(tmp_path))
        scan_result = {
            "dependencies": [{"name": "requests", "direct": True}],
            "direct_count": 1,
            "transitive_count": 0,
        }

        id1 = storage.save_snapshot("/proj", scan_result)
        id2 = storage.save_snapshot("/proj", scan_result)

        assert id1 > 0
        assert id2 > 0
        assert id1 != id2

    def test_snapshot_history_orders_newest_first(self, tmp_path):
        storage = SnapshotStorage(cache_dir=str(tmp_path))
        for i in range(3):
            storage.save_snapshot(
                "/proj",
                {"dependencies": [{"name": f"pkg{i}", "direct": True}], "direct_count": 1, "transitive_count": 0},
            )

        history = storage.get_snapshot_history("/proj", limit=10)
        assert len(history) == 3


class TestBaselineAndDrift:
    def test_set_and_get_baseline(self, tmp_path):
        storage = SnapshotStorage(cache_dir=str(tmp_path))
        storage.save_snapshot(
            "/proj", {"dependencies": [{"name": "requests", "direct": True}], "direct_count": 1, "transitive_count": 0}
        )
        assert storage.set_baseline("/proj") is True

        baseline = storage.get_baseline("/proj")
        assert baseline is not None

    def test_set_baseline_without_snapshot_fails_gracefully(self, tmp_path):
        storage = SnapshotStorage(cache_dir=str(tmp_path))
        assert storage.set_baseline("/no/snapshots/here") is False

    def test_compute_drift_detects_added_and_removed(self, tmp_path):
        storage = SnapshotStorage(cache_dir=str(tmp_path))
        old = {"dependencies": [{"name": "requests", "version": "1.0"}, {"name": "flask", "version": "1.0"}]}
        new = {"dependencies": [{"name": "requests", "version": "1.0"}, {"name": "django", "version": "1.0"}]}

        drift = storage._compute_drift(old, new)

        assert drift["changed"] is True
        assert drift["added"] == ["django"]
        assert drift["removed"] == ["flask"]

    def test_compute_drift_detects_upgrade(self, tmp_path):
        storage = SnapshotStorage(cache_dir=str(tmp_path))
        old = {"dependencies": [{"name": "requests", "version": "1.0.0"}]}
        new = {"dependencies": [{"name": "requests", "version": "2.0.0"}]}

        drift = storage._compute_drift(old, new)

        assert drift["changed"] is True
        assert drift["upgraded"] == [("requests", "1.0.0", "2.0.0")]

    def test_no_drift_when_unchanged(self, tmp_path):
        storage = SnapshotStorage(cache_dir=str(tmp_path))
        deps = {"dependencies": [{"name": "requests", "version": "1.0.0"}]}

        drift = storage._compute_drift(deps, deps)
        assert drift["changed"] is False


class TestVersionComparison:
    def test_version_greater(self):
        assert SnapshotStorage._version_greater("2.0.0", "1.0.0") is True
        assert SnapshotStorage._version_greater("1.0.0", "2.0.0") is False

    def test_invalid_version_does_not_raise(self):
        assert SnapshotStorage._version_greater("not-a-version", "1.0.0") is False
