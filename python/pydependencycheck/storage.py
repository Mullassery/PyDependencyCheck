"""Storage layer for snapshots, caching, and drift tracking"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import json


class SnapshotStorage:
    """Manages SQLite storage for snapshots and caching"""

    def __init__(self, cache_dir: str = "~/.pydep"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "cache.db"
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY,
                project_path TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                graph_json TEXT NOT NULL,
                total_deps INTEGER,
                direct_deps INTEGER,
                transitive_deps INTEGER,
                graph_hash TEXT UNIQUE,
                requirements_hash TEXT,
                pyproject_hash TEXT
            )
        """)

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

        conn.commit()
        conn.close()

    def save_snapshot(self, project_path: str, graph_data: Dict[str, Any]) -> int:
        """Save a dependency graph snapshot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO snapshots (project_path, graph_json, total_deps, direct_deps, transitive_deps)
            VALUES (?, ?, ?, ?, ?)
        """, (
            project_path,
            json.dumps(graph_data),
            len(graph_data.get("nodes", [])),
            sum(1 for n in graph_data.get("nodes", []) if n.get("is_direct")),
            len(graph_data.get("nodes", [])) - sum(1 for n in graph_data.get("nodes", []) if n.get("is_direct")),
        ))

        conn.commit()
        snapshot_id = cursor.lastrowid
        conn.close()

        return snapshot_id

    def get_latest_snapshot(self, project_path: str) -> Dict[str, Any] | None:
        """Get the latest snapshot for a project"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM snapshots
            WHERE project_path = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (project_path,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None
