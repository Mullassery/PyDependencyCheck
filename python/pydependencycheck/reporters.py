"""Report generators for different output formats"""

import html
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime


def escape(value: Any) -> str:
    """HTML-entity-encode an untrusted value before interpolating it into HTML.

    Dependency metadata (package names, versions, source paths, ...) can
    originate from third-party manifests (requirements.txt, pyproject.toml,
    PyPI responses, etc.) and must never be trusted to be safe to embed
    directly in HTML output. This mirrors str() for non-string values (e.g.
    None) so callers can pass raw dict values straight through.
    """
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


class Reporter(ABC):
    """Base reporter class"""

    @abstractmethod
    def generate(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate report from dependencies"""
        pass


class JsonReporter(Reporter):
    """JSON report generator"""

    def generate(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate JSON report (SBOM-compatible)"""
        return json.dumps(
            {
                "format": "pypi-dependencies",
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "dependencies": dependencies,
                "summary": {
                    "total": len(dependencies),
                    "direct": sum(1 for d in dependencies if d.get("direct", False)),
                    "transitive": sum(1 for d in dependencies if not d.get("direct", False)),
                },
            },
            indent=2,
        )


class HtmlReporter(Reporter):
    """HTML report generator with D3.js visualization"""

    def generate(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate HTML report with interactive graph"""
        direct_count = sum(1 for d in dependencies if d.get("direct", False))
        transitive_count = len(dependencies) - direct_count

        html_doc = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PyDependencyCheck Report</title>
    <style>
        * {{ margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
        .stat {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ background: #667eea; color: white; padding: 12px; text-align: left; font-weight: 600; }}
        td {{ padding: 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 600; }}
        .badge-direct {{ background: #667eea; color: white; }}
        .badge-transitive {{ background: #f97316; color: white; }}
        .footer {{ margin-top: 30px; text-align: center; color: #999; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📦 PyDependencyCheck Report</h1>
            <p>Dependency Intelligence & Governance</p>
        </div>

        <div class="summary">
            <div class="stat">
                <div class="stat-number">{len(dependencies)}</div>
                <div class="stat-label">Total Dependencies</div>
            </div>
            <div class="stat">
                <div class="stat-number">{direct_count}</div>
                <div class="stat-label">Direct</div>
            </div>
            <div class="stat">
                <div class="stat-number">{transitive_count}</div>
                <div class="stat-label">Transitive</div>
            </div>
        </div>

        <h2>Dependencies</h2>
        <table>
            <thead>
                <tr>
                    <th>Package</th>
                    <th>Version</th>
                    <th>Type</th>
                    <th>Source</th>
                </tr>
            </thead>
            <tbody>
"""

        rows = []
        for dep in dependencies:
            dep_type = "Direct" if dep.get("direct", False) else "Transitive"
            badge_class = "badge-direct" if dep.get("direct", False) else "badge-transitive"
            source = dep.get("source", "unknown").split("/")[-1]

            # All values below originate from untrusted third-party manifest
            # data (package names/versions/sources parsed from
            # requirements.txt, pyproject.toml, etc.) and must be
            # HTML-entity-encoded before interpolation to prevent stored XSS.
            rows.append(
                f"""                <tr>
                    <td><strong>{escape(dep.get('name'))}</strong></td>
                    <td>{escape(dep.get('version', '—'))}</td>
                    <td><span class="badge {badge_class}">{escape(dep_type)}</span></td>
                    <td>{escape(source)}</td>
                </tr>
"""
            )

        html_doc += "".join(rows)

        html_doc += """            </tbody>
        </table>

        <div class="footer">
            <p>Generated by PyDependencyCheck</p>
        </div>
    </div>
</body>
</html>
"""
        return html_doc


class MarkdownReporter(Reporter):
    """Markdown report generator"""

    def generate(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate Markdown report"""
        direct_count = sum(1 for d in dependencies if d.get("direct", False))
        transitive_count = len(dependencies) - direct_count

        lines = [
            "# Dependency Report",
            "",
            "## Summary",
            f"- **Total Dependencies:** {len(dependencies)}",
            f"- **Direct:** {direct_count}",
            f"- **Transitive:** {transitive_count}",
            "",
            "## Dependencies",
            "",
            "| Package | Version | Type | Source |",
            "|---------|---------|------|--------|",
        ]

        for dep in dependencies:
            dep_type = "Direct" if dep.get("direct", False) else "Transitive"
            source = dep.get("source", "unknown").split("/")[-1]
            version = dep.get("version") or "—"
            lines.append(f"| `{dep['name']}` | {version} | {dep_type} | {source} |")

        lines.extend(
            [
                "",
                "---",
                "*Generated by PyDependencyCheck*",
            ]
        )

        return "\n".join(lines)


class CycloneDxReporter(Reporter):
    """CycloneDX SBOM reporter (v1.4)"""

    def generate(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate CycloneDX SBOM"""
        components = []
        for dep in dependencies:
            components.append(
                {
                    "type": "library",
                    "name": dep["name"],
                    "version": dep.get("version", "unknown"),
                    "purl": f"pkg:pypi/{dep['name']}@{dep.get('version', 'unknown')}",
                }
            )

        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "components": components,
        }

        return json.dumps(sbom, indent=2)
