"""Storage layer for snapshots, caching, and drift tracking"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


class DriftSnapshot:
    """Represents a dependency snapshot at a point in time"""

    def __init__(
        self,
        snapshot_id: int,
        project_path: str,
        timestamp: datetime,
        dependencies: Dict[str, Any],
        graph_hash: str,
        health_score: Optional[int] = None,
    ):
        self.id = snapshot_id
        self.project_path = project_path
        self.timestamp = timestamp
        self.dependencies = dependencies
        self.graph_hash = graph_hash
        self.health_score = health_score


class SnapshotStorage:
    """Manages SQLite storage for snapshots, caching, and drift tracking"""

    def __init__(self, cache_dir: str = "~/.pydep"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "cache.db"
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Snapshots: Full dependency trees with metadata
        #
        # Deliberately no UNIQUE constraint on graph_hash or
        # (project_path, timestamp): history/timeline tracking needs to
        # store a new snapshot every time a scan runs, even when nothing
        # changed since the last one (that "nothing changed" data point is
        # exactly what `drift`/`history` need to show a stable trend).
        # `timestamp` also only has one-second resolution, so two scans
        # run in quick succession -- entirely normal in CI or in tests --
        # would otherwise collide and the second save would be silently
        # dropped (`save_snapshot` returning -1 without raising).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY,
                project_path TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                graph_json TEXT NOT NULL,
                total_deps INTEGER,
                direct_deps INTEGER,
                transitive_deps INTEGER,
                graph_hash TEXT,
                health_score INTEGER
            )
        """)

        # Vulnerability cache (7-day TTL)
        #
        # Note: SQLite (unlike MySQL) does not support an inline
        # `INDEX(...)` column-style declaration inside CREATE TABLE -- it's
        # a syntax error there, which meant this table (and every command
        # that touches SnapshotStorage: `snapshot`, `history`, `drift`,
        # `scan --save-snapshot`) failed unconditionally with
        # "near INDEX: syntax error" the moment SnapshotStorage() was
        # constructed. Real indexes must be created separately below.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY,
                package_name TEXT NOT NULL,
                package_version TEXT,
                cve_id TEXT,
                osv_id TEXT UNIQUE,
                severity TEXT,
                cvss_score REAL,
                description TEXT,
                affected_versions_json TEXT,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_vulnerabilities_pkg ON vulnerabilities(package_name, package_version)"
        )

        # Usage analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_analysis (
                id INTEGER PRIMARY KEY,
                package_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER,
                usage_type TEXT,
                context TEXT,
                snapshot_id INTEGER REFERENCES snapshots(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_analysis_pkg ON usage_analysis(package_name, file_path)")

        # Blame/history log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blame_log (
                id INTEGER PRIMARY KEY,
                package_name TEXT NOT NULL,
                action TEXT,
                version TEXT,
                commit_hash TEXT,
                author TEXT,
                timestamp DATETIME,
                message TEXT,
                snapshot_id INTEGER REFERENCES snapshots(id)
            )
        """)

        # Drift baselines
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drift_baselines (
                id INTEGER PRIMARY KEY,
                project_path TEXT UNIQUE NOT NULL,
                baseline_name TEXT DEFAULT 'main',
                baseline_graph_hash TEXT,
                baseline_snapshot_id INTEGER REFERENCES snapshots(id),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def save_snapshot(self, project_path: str, scan_result: Dict[str, Any], health_score: Optional[int] = None) -> int:
        """Save a dependency scan snapshot"""
        deps = scan_result.get("dependencies", [])
        direct_count = sum(1 for d in deps if d.get("direct", False))

        # Compute graph hash for drift detection
        graph_hash = self._compute_graph_hash(deps)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO snapshots (
                    project_path, graph_json, total_deps, direct_deps, transitive_deps,
                    graph_hash, health_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    project_path,
                    json.dumps(scan_result),
                    len(deps),
                    direct_count,
                    len(deps) - direct_count,
                    graph_hash,
                    health_score,
                ),
            )

            conn.commit()
            snapshot_id = cursor.lastrowid
            logger.info(f"Snapshot saved: {project_path} (ID: {snapshot_id})")
            return snapshot_id

        except sqlite3.IntegrityError as e:
            logger.warning(f"Duplicate snapshot detected: {e}")
            return -1
        finally:
            conn.close()

    def get_latest_snapshot(self, project_path: str) -> Optional[DriftSnapshot]:
        """Get the latest snapshot for a project"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM snapshots
            WHERE project_path = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """,
            (project_path,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return DriftSnapshot(
                snapshot_id=row["id"],
                project_path=row["project_path"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                dependencies=json.loads(row["graph_json"]),
                graph_hash=row["graph_hash"],
                health_score=row["health_score"],
            )
        return None

    def get_snapshot_history(self, project_path: str, limit: int = 30) -> List[DriftSnapshot]:
        """Get snapshot history for a project"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM snapshots
            WHERE project_path = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (project_path, limit),
        )

        rows = cursor.fetchall()
        conn.close()

        snapshots = []
        for row in rows:
            snapshots.append(
                DriftSnapshot(
                    snapshot_id=row["id"],
                    project_path=row["project_path"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    dependencies=json.loads(row["graph_json"]),
                    graph_hash=row["graph_hash"],
                    health_score=row["health_score"],
                )
            )

        return snapshots

    def detect_drift(self, project_path: str, current_snapshot: DriftSnapshot) -> Dict[str, Any]:
        """Detect changes since last snapshot or baseline"""
        baseline = self.get_baseline(project_path)
        latest = self.get_latest_snapshot(project_path)

        if not latest or latest.id == current_snapshot.id:
            return {"changed": False, "drift": []}

        return self._compute_drift(latest.dependencies, current_snapshot.dependencies)

    def _compute_drift(self, old_deps: Dict, new_deps: Dict) -> Dict[str, Any]:
        """Compute differences between two dependency sets"""
        old_names = {d["name"]: d for d in old_deps.get("dependencies", [])}
        new_names = {d["name"]: d for d in new_deps.get("dependencies", [])}

        added = set(new_names.keys()) - set(old_names.keys())
        removed = set(old_names.keys()) - set(new_names.keys())
        upgraded = []
        downgraded = []

        for name in set(old_names.keys()) & set(new_names.keys()):
            old_version = old_names[name].get("version", "0.0.0")
            new_version = new_names[name].get("version", "0.0.0")
            if old_version != new_version:
                if self._version_greater(new_version, old_version):
                    upgraded.append((name, old_version, new_version))
                else:
                    downgraded.append((name, old_version, new_version))

        return {
            "changed": bool(added or removed or upgraded or downgraded),
            "added": sorted(list(added)),
            "removed": sorted(list(removed)),
            "upgraded": upgraded,
            "downgraded": downgraded,
        }

    def set_baseline(self, project_path: str, baseline_name: str = "main") -> bool:
        """Set current state as baseline for drift detection"""
        latest = self.get_latest_snapshot(project_path)
        if not latest:
            logger.warning(f"No snapshot to baseline for {project_path}")
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO drift_baselines (project_path, baseline_name, baseline_snapshot_id)
            VALUES (?, ?, ?)
        """,
            (project_path, baseline_name, latest.id),
        )

        conn.commit()
        conn.close()

        logger.info(f"Baseline set for {project_path}: {baseline_name}")
        return True

    def get_baseline(self, project_path: str) -> Optional[DriftSnapshot]:
        """Get the stored baseline snapshot"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT s.* FROM snapshots s
            JOIN drift_baselines b ON s.id = b.baseline_snapshot_id
            WHERE b.project_path = ?
            ORDER BY b.created_at DESC
            LIMIT 1
        """,
            (project_path,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return DriftSnapshot(
                snapshot_id=row["id"],
                project_path=row["project_path"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                dependencies=json.loads(row["graph_json"]),
                graph_hash=row["graph_hash"],
                health_score=row["health_score"],
            )
        return None

    def cleanup_old_snapshots(self, project_path: str, keep: int = 30) -> int:
        """Remove old snapshots, keeping only the most recent N"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id FROM snapshots
            WHERE project_path = ?
            ORDER BY timestamp DESC
            LIMIT -1 OFFSET ?
        """,
            (project_path, keep),
        )

        old_ids = [row[0] for row in cursor.fetchall()]

        if old_ids:
            placeholders = ",".join("?" * len(old_ids))
            cursor.execute(f"DELETE FROM snapshots WHERE id IN ({placeholders})", old_ids)
            conn.commit()

        conn.close()
        return len(old_ids)

    @staticmethod
    def _compute_graph_hash(dependencies: List[Dict]) -> str:
        """Compute SHA256 hash of dependency graph for drift detection"""
        graph_str = json.dumps(sorted([d["name"] for d in dependencies]), sort_keys=True)
        return hashlib.sha256(graph_str.encode()).hexdigest()

    @staticmethod
    def _version_greater(v1: str, v2: str) -> bool:
        """Simple version comparison (for testing; use packaging.version in production)"""
        try:
            v1_parts = [int(x) for x in v1.split(".")[:3]]
            v2_parts = [int(x) for x in v2.split(".")[:3]]
            v1_parts += [0] * (3 - len(v1_parts))
            v2_parts += [0] * (3 - len(v2_parts))
            return v1_parts > v2_parts
        except (ValueError, AttributeError):
            return False
