"""CLI Dashboard using Rich for real-time monitoring"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
import time

from .storage import SnapshotStorage
from .health import HealthAnalyzer

console = Console()


class CLIDashboard:
    """Terminal-based dashboard for dependency monitoring"""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.storage = SnapshotStorage()
        self.health_analyzer = HealthAnalyzer()

    def show_summary(self, scan_result: Dict, health_score: Optional[int] = None) -> None:
        """Display scan summary dashboard"""
        deps = scan_result.get("dependencies", [])
        direct_count = sum(1 for d in deps if d.get("direct", False))
        transitive_count = len(deps) - direct_count

        # Create layout
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="content"),
            Layout(name="footer", size=2),
        )

        # Header
        layout["header"].update(Panel("[bold cyan]📦 PyDependencyCheck Dashboard[/bold cyan]", border_style="cyan"))

        # Main content
        layout["content"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1),
        )

        # Left: Stats
        stats_table = Table(title="Dependency Stats", show_header=False, box=None)
        stats_table.add_row("[bold]Total Dependencies[/bold]", str(len(deps)))
        stats_table.add_row("[bold]Direct[/bold]", str(direct_count), style="green")
        stats_table.add_row("[bold]Transitive[/bold]", str(transitive_count), style="blue")

        if health_score:
            health_text = self._score_to_rich_text(health_score)
            stats_table.add_row("[bold]Health Score[/bold]", health_text)

        layout["left"].update(Panel(stats_table, title="Summary"))

        # Right: Recent activity
        activity_table = Table(title="Top Packages", show_header=True)
        activity_table.add_column("Package", style="cyan")
        activity_table.add_column("Version", style="magenta")
        activity_table.add_column("Type", style="green")

        for dep in deps[:5]:
            dep_type = "📌 Direct" if dep.get("direct") else "📄 Transitive"
            activity_table.add_row(dep["name"], dep.get("version", "—"), dep_type)

        layout["right"].update(Panel(activity_table, title="Top Dependencies"))

        # Footer
        layout["footer"].update(Text(f"Scanned: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", justify="center"))

        console.print(layout)

    def show_drift_report(self, project_path: str) -> None:
        """Display drift detection report"""
        history = self.storage.get_snapshot_history(project_path, limit=2)

        if len(history) < 2:
            console.print("[yellow]⚠️  Need at least 2 snapshots to detect drift[/yellow]")
            return

        current = history[0]
        previous = history[1]

        drift = self.storage._compute_drift(previous.dependencies, current.dependencies)

        # Create drift table
        table = Table(title="Dependency Drift Analysis", show_header=True)
        table.add_column("Change Type", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Details", style="green")

        if drift["added"]:
            table.add_row(
                "➕ Added",
                str(len(drift["added"])),
                ", ".join(drift["added"][:3]) + ("..." if len(drift["added"]) > 3 else ""),
            )

        if drift["removed"]:
            table.add_row(
                "➖ Removed",
                str(len(drift["removed"])),
                ", ".join(drift["removed"][:3]) + ("..." if len(drift["removed"]) > 3 else ""),
            )

        if drift["upgraded"]:
            versions = [f"{pkg}: {old}→{new}" for pkg, old, new in drift["upgraded"][:3]]
            table.add_row(
                "📈 Upgraded",
                str(len(drift["upgraded"])),
                ", ".join(versions) + ("..." if len(drift["upgraded"]) > 3 else ""),
            )

        if drift["downgraded"]:
            versions = [f"{pkg}: {old}→{new}" for pkg, old, new in drift["downgraded"][:3]]
            table.add_row(
                "📉 Downgraded",
                str(len(drift["downgraded"])),
                ", ".join(versions) + ("..." if len(drift["downgraded"]) > 3 else ""),
            )

        if not drift["changed"]:
            table.add_row("✅ No Changes", "0", "Dependency set stable")

        console.print(table)

        # Timestamps
        console.print(f"\n[dim]Previous scan: {previous.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
        console.print(f"[dim]Current scan:  {current.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

    def show_timeline(self, project_path: str, days: int = 30) -> None:
        """Display dependency timeline over N days"""
        history = self.storage.get_snapshot_history(project_path, limit=100)

        # Filter to requested days
        cutoff = datetime.now() - timedelta(days=days)
        history = [s for s in history if s.timestamp >= cutoff]

        if not history:
            console.print(f"[yellow]No snapshots found in last {days} days[/yellow]")
            return

        table = Table(title=f"Dependency Timeline ({days} days)", show_header=True)
        table.add_column("Date", style="cyan")
        table.add_column("Total", style="magenta")
        table.add_column("Direct", style="green")
        table.add_column("Health", style="yellow")
        table.add_column("Trend", style="blue")

        prev_total = None
        for snapshot in reversed(history):  # Oldest first
            deps = snapshot.dependencies.get("dependencies", [])
            total = len(deps)
            direct = sum(1 for d in deps if d.get("direct", False))

            # Compute trend
            if prev_total is None:
                trend = "—"
            elif total > prev_total:
                trend = f"📈 +{total - prev_total}"
            elif total < prev_total:
                trend = f"📉 {total - prev_total}"
            else:
                trend = "→"

            health_text = self._score_to_rich_text(snapshot.health_score) if snapshot.health_score else "—"

            table.add_row(snapshot.timestamp.strftime("%Y-%m-%d"), str(total), str(direct), health_text, trend)

            prev_total = total

        console.print(table)

    def show_health_details(self, health_score_obj) -> None:
        """Display detailed health score breakdown"""
        table = Table(title="Health Score Breakdown", show_header=True)
        table.add_column("Factor", style="cyan")
        table.add_column("Score", style="magenta")
        table.add_column("Status", style="green")

        factors = [
            ("Overall Health", health_score_obj.score, health_score_obj.rating),
            (
                "Vulnerabilities",
                health_score_obj.vulnerabilities_score,
                self._get_factor_rating(health_score_obj.vulnerabilities_score),
            ),
            (
                "Maintenance",
                health_score_obj.maintenance_score,
                self._get_factor_rating(health_score_obj.maintenance_score),
            ),
            ("Quality", health_score_obj.quality_score, self._get_factor_rating(health_score_obj.quality_score)),
            (
                "Complexity",
                health_score_obj.complexity_score,
                self._get_factor_rating(health_score_obj.complexity_score),
            ),
        ]

        for name, score, status in factors:
            bar = self._score_to_bar(score)
            table.add_row(name, f"{score}/100", f"{bar} {status}")

        console.print(table)

        # Issues and recommendations
        if health_score_obj.issues:
            console.print("\n[bold red]⚠️  Issues:[/bold red]")
            for issue in health_score_obj.issues:
                console.print(f"  {issue}")

        if health_score_obj.recommendations:
            console.print("\n[bold green]💡 Recommendations:[/bold green]")
            for rec in health_score_obj.recommendations:
                console.print(f"  • {rec}")

    @staticmethod
    def _score_to_rich_text(score: int) -> Text:
        """Convert score to rich colored text"""
        if score >= 80:
            return Text(f"{score}/100 ✅", style="bold green")
        elif score >= 65:
            return Text(f"{score}/100 👍", style="bold yellow")
        elif score >= 50:
            return Text(f"{score}/100 ⚠️", style="bold orange1")
        else:
            return Text(f"{score}/100 🚨", style="bold red")

    @staticmethod
    def _score_to_bar(score: int) -> str:
        """Convert score to visual bar"""
        filled = int(score / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty

    @staticmethod
    def _get_factor_rating(score: int) -> str:
        """Get rating for individual factor"""
        if score >= 80:
            return "Excellent"
        elif score >= 65:
            return "Good"
        elif score >= 50:
            return "Fair"
        else:
            return "Poor"

    def show_live_monitor(self, project_path: str, interval: int = 60) -> None:
        """Live monitoring dashboard (updates every N seconds)"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Monitoring for changes...", total=None)

            while True:
                latest = self.storage.get_latest_snapshot(project_path)

                if latest:
                    deps = latest.dependencies.get("dependencies", [])
                    direct = sum(1 for d in deps if d.get("direct", False))

                    status = f"[cyan]{len(deps)}[/cyan] dependencies "
                    status += f"([green]{direct}[/green] direct)"

                    if latest.health_score:
                        status += f" • Health: {latest.health_score}/100"

                    progress.update(task, description=status)

                time.sleep(interval)
