# PyDependencyCheck Architecture

## Overview

PyDependencyCheck is a **hybrid Rust + Python application** designed for enterprise-grade dependency analysis.

### Why Rust + Python?

- **Rust (performance):** Graph traversal, AST parsing, vulnerability scoring—CPU-bound operations that benefit from compiled efficiency
- **Python (UX):** CLI, reporting, templating, and ecosystem integrations require flexibility and rapid iteration

### Design Principles

1. **Zero Reimplementation:** Use existing, audited libraries (OSV, petgraph) rather than rewriting security research
2. **Offline-First:** Cache vulnerabilities locally; fall back to online API only when needed
3. **Supply Chain Transparency:** Every dependency must trace back to its source (requirements.txt line, commit, author)
4. **Performance:** Scan 500-node graphs in <1s; generate reports in <5s

---

## Component Architecture

```
┌──────────────────────────────────────────────────────┐
│             Python CLI Layer (Click)                 │
│    Reports, Visualization, Git Integration           │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│        PyO3 Bindings (_pydependencycheck)             │
│   Bridge between Rust core and Python application    │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│                    Rust Core                         │
├──────────────────────────────────────────────────────┤
│ pydep-parser  │ pydep-graph  │ pydep-ast │ pydep-sec │
├──────────────────────────────────────────────────────┤
│ • Parse TOML  │ • petgraph   │ • tree-   │ • OSV API │
│ • Parse YAML  │ • Cycles     │   sitter  │ • CVSS    │
│ • Version     │ • Transitive │ • Import  │ • Risk    │
│   constraints │   closure    │   tracking│   scoring │
└──────────────────────────────────────────────────────┘
```

---

## Rust Crates

### 1. pydep-parser
**Purpose:** Parse Python dependency declarations

**Supported Formats:**
- `requirements.txt`
- `requirements-dev.txt`, `requirements-test.txt`
- `constraints.txt`
- `pyproject.toml` (PEP 508)
- `setup.py` (setuptools)
- `setup.cfg`

**Key APIs:**
```rust
pub fn parse_file(path: &str) -> ParserResult<Vec<Dependency>>
pub fn parse_requirements(content: &str) -> ParserResult<Vec<Dependency>>
pub fn parse_pyproject(path: &Path) -> ParserResult<Vec<Dependency>>
```

**Complexity:** Medium — TOML/YAML parsing is I/O-bound; version constraint solving is CPU-bound

### 2. pydep-graph
**Purpose:** Dependency graph construction and analysis

**Uses:** `petgraph::DiGraph` for O(1) cycle detection, O(V+E) transitive closure

**Key Queries:**
- Topological sort: order for safe upgrades
- Transitive closure: all packages pulled in by A
- Reverse dependencies: who depends on B?
- Path finding: dependency chain A→B→C→D
- Cycle detection: circular dependencies

**Performance:** 10,000-node graph in <500ms

### 3. pydep-ast
**Purpose:** Python code analysis to detect which dependencies are used

**Technology:** `tree-sitter` (fast, language-agnostic parser)

**Detects:**
- `import requests`
- `from requests import Session`
- `importlib.import_module("requests")`
- Conditional imports: `try: import X except: pass`
- Type hints: `def foo(x: SomeType)`

**Dead Code Detection:** Heuristic; flags packages with <5 references as potentially unused

### 4. pydep-security
**Purpose:** Vulnerability scoring and risk propagation

**Data Sources:**
1. **OSV (api.osv.dev):** Official database of open-source vulnerabilities
2. **PyPI Advisories:** Direct from PyPI metadata
3. **Local cache:** `~/.pydep/osv-latest.db` (50MB, weekly updates)

**Risk Scoring:**
- Base: CVSS score (0-10)
- Adjustment: Propagated through dependency chain
- Health: Aggregate 0-100 from multiple factors

### 5. pydep-py
**Purpose:** PyO3 bindings to export Rust types to Python

**Exported:**
- `DependencyGraph` class (petgraph wrapper)
- `Dependency` class (Python-friendly struct)
- `Vulnerability` class with severity enum

---

## Python Modules

### CLI (Click)
**Entry point:** `pydependencycheck` command

**Commands (v0.1):**
- `scan` — Full analysis
- `list` — Show dependencies
- `why` — Explain a dependency
- `trace` — Show dependency chain
- `blame` — Git history

### Scanner
**Class:** `DependencyScanner(project_path)`

**Flow:**
1. Auto-detect dependency files (requirements.txt, pyproject.toml, etc.)
2. Parse each file → unified dependency list
3. Resolve versions, markers, extras
4. Build graph → Rust via PyO3
5. Run analysis (cycles, transitive closure)
6. Correlate with usage analysis + security data

### Reporters
**Base:** Abstract `Reporter` class

**Implementations:**
- `JsonReporter` — Machine-readable
- `HtmlReporter` — Interactive D3 visualization
- `MarkdownReporter` — Human-readable tables
- `SbomReporter` — CycloneDX (v1.0+)

### Storage (SQLite)
**Location:** `~/.pydep/cache.db`

**Tables:**
```sql
snapshots        -- Full dependency trees + metadata
vulnerabilities  -- OSV cache (7-day TTL)
usage_analysis   -- Which files import what
blame_log        -- Git history of dependencies
drift_baselines  -- Stored baselines for comparison
```

### Git Integration
**Library:** `GitPython`

**Operations:**
- Blame per dependency: Who added it? When?
- History: Track versions over time
- Commit deps: Dependencies at a specific commit

---

## Data Flow: A Scan

```
1. User: pydependencycheck scan .
                      ↓
2. CLI detects files (requirements.txt, pyproject.toml)
                      ↓
3. Python calls Rust parser (via PyO3)
   → pydep-parser.parse_file() for each file
                      ↓
4. Unified dependency list
                      ↓
5. Python calls Rust graph builder (via PyO3)
   → pydep-graph.DependencyGraph::new()
   → Add nodes, edges
   → Detect cycles
                      ↓
6. Python analyzes usage (pydep-ast via PyO3)
   → Extract imports from source files
                      ↓
7. Python queries OSV (pydep-security via PyO3)
   → Check cache first
   → Fall back to api.osv.dev
                      ↓
8. Python correlates data
   → Which packages are used? (usage_analysis)
   → Risk scores per package
   → Health score aggregate
                      ↓
9. Python reporters generate output (JSON, HTML, etc.)
                      ↓
10. Store snapshot in SQLite for drift tracking
                      ↓
11. Display to user
```

---

## Storage Schema

### snapshots
```sql
CREATE TABLE snapshots (
    id INTEGER PRIMARY KEY,
    project_path TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Serialized graph (JSON)
    graph_json TEXT NOT NULL,
    
    -- Aggregated stats
    total_deps INTEGER,
    direct_deps INTEGER,
    transitive_deps INTEGER,
    
    -- Drift detection
    graph_hash TEXT UNIQUE,
    
    -- Source file integrity
    requirements_hash TEXT,
    pyproject_hash TEXT
);
```

### vulnerabilities
```sql
CREATE TABLE vulnerabilities (
    id INTEGER PRIMARY KEY,
    package_name TEXT NOT NULL,
    package_version TEXT,
    cve_id TEXT,
    osv_id TEXT UNIQUE,
    severity TEXT,  -- CRITICAL, HIGH, MEDIUM, LOW
    cvss_score REAL,
    description TEXT,
    affected_versions_json TEXT,  -- JSON array of semver ranges
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### usage_analysis
```sql
CREATE TABLE usage_analysis (
    id INTEGER PRIMARY KEY,
    package_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    usage_type TEXT,  -- 'import', 'direct_call', 'indirect_call', 'type_hint'
    context TEXT,  -- function name or class context
    snapshot_id INTEGER REFERENCES snapshots(id)
);
```

### blame_log
```sql
CREATE TABLE blame_log (
    id INTEGER PRIMARY KEY,
    package_name TEXT NOT NULL,
    action TEXT,  -- 'added', 'removed', 'upgraded', 'downgraded'
    version TEXT,
    commit_hash TEXT,
    author TEXT,
    timestamp DATETIME,
    message TEXT,
    snapshot_id INTEGER REFERENCES snapshots(id)
);
```

---

## Performance Targets

| Operation | Target | Notes |
|---|---|---|
| Parse 500-node requirements | <500ms | TOML parsing, constraint resolution |
| Build graph (petgraph) | <100ms | Node insertion, cycle detection |
| Scan 100 Python files (AST) | <1s | tree-sitter parsing |
| Query OSV (100 packages) | <2s | Cached locally when available |
| HTML report generation | <3s | D3 JSON export, template rendering |
| **Total scan** | **<5s** | End-to-end for typical project |

---

## Security Considerations

### Threat Model
- **Trust:** Git history is trusted (local repo only)
- **Untrust:** Dependency metadata from PyPI/OSV (signed, verified)
- **Privacy:** No telemetry, no external API calls without explicit user action

### Vulnerabilities Defense
- **No reimplementation:** Trust OSV and PyPI for CVE data
- **Offline cache:** Local snapshot reduces API dependency
- **Rate limiting:** Batch queries, 7-day cache TTL
- **Verification:** Snapshot integrity checked before use

---

## Testing Strategy

### Unit Tests (Rust)
- Parser: 50+ edge cases (markers, extras, VCS URLs)
- Graph: Cycle detection, transitive closure, topological sort
- AST: Import extraction validation

### Integration Tests (Python)
- End-to-end: Real projects (django, flask, numpy, etc.)
- Fixtures: Synthetic projects (flat, circular, complex)
- Regression: Known CVEs must be detected

### Performance Tests
- Parse 1000-node graph
- Scan 1000-file codebase
- Memory usage on large projects

---

## Future Extensibility

### Plugin System (v1.0)
```python
class CustomReporter:
    def generate(self, scan_result) -> str:
        # Custom output format
```

### Multi-Project Dashboard (v1.0)
- Aggregate scans across org
- Trend visualization
- Alert policies

### Supply Chain Attestation (v2.0)
- SLSA provenance
- SBOM signing
- Supply chain transparency reports
