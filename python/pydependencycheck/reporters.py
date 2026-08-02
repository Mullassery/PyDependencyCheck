"""Report generators for different output formats"""

import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class Reporter(ABC):
    """Base reporter class"""

    @abstractmethod
    def generate(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate report from dependencies"""
        pass


class JsonReporter(Reporter):
    """JSON report generator"""

    def generate(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate JSON report"""
        return json.dumps({
            "dependencies": dependencies,
            "count": len(dependencies),
        }, indent=2)


class HtmlReporter(Reporter):
    """HTML report generator with D3.js visualization"""

    def generate(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate HTML report with interactive graph"""
        # TODO: Render Jinja2 template with D3.js
        return "<html>TODO: HTML Report</html>"


class MarkdownReporter(Reporter):
    """Markdown report generator"""

    def generate(self, dependencies: List[Dict[str, Any]]) -> str:
        """Generate Markdown report"""
        lines = ["# Dependency Report\n"]
        lines.append(f"**Total dependencies:** {len(dependencies)}\n")

        for dep in dependencies:
            lines.append(f"- {dep.get('name', 'Unknown')}")

        return "\n".join(lines)
