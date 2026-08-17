"""PyDependencyCheck CLI: Command-line interface for dependency analysis"""

import click
import json
from pathlib import Path
from typing import Dict, List, Optional
import sys

from .scanner import DependencyScanner, ScanResult
from .reporters import JsonReporter, HtmlReporter, MarkdownReporter
from .storage import SnapshotStorage
from .git_integration import GitIntegration
from .sbom import SBOMGenerator, SBOMSigner
from .licenses import LicenseAnalyzer
from .health import HealthAnalyzer, PackageStalenessChecker
from .github_actions import GitHubActionsReporter
from .telemetry import TelemetryConfig, TelemetryManager
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()


@click.group()
@click.version_option()
def cli():
    """PyDependencyCheck - Dependency Intelligence Platform

    Scan dependencies, analyze usage, detect vulnerabilities, and track supply chain.

    Examples:
        pydependencycheck scan .
        pydependencycheck why requests
        pydependencycheck trace urllib3
        pydependencycheck list --path /myproject
    """
    pass


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path to scan")
@click.option("--output", "-o", type=click.Path(), help="Output file path (optional)")
@click.option(
    "--format", "-f", type=click.Choice(["json", "html", "markdown", "table"]), default="table", help="Output format"
)
@click.option("--save-snapshot", is_flag=True, help="Save scan result to cache")
def scan(path: str, output: Optional[str], format: str, save_snapshot: bool):
    """Scan a project for dependencies"""
    with console.status("[bold]Scanning project...[/bold]"):
        scanner = DependencyScanner(path)
        result = scanner.scan()

    # Save snapshot if requested
    if save_snapshot:
        storage = SnapshotStorage()
        storage.save_snapshot(path, result.to_dict())
        console.print("[green]✓[/green] Snapshot saved")

    # Generate report
    if format == "json":
        reporter = JsonReporter()
        output_data = reporter.generate(result.dependencies)
    elif format == "html":
        reporter = HtmlReporter()
        output_data = reporter.generate(result.dependencies)
    elif format == "markdown":
        reporter = MarkdownReporter()
        output_data = reporter.generate(result.dependencies)
    else:
        # Table format (default)
        output_data = _format_table_report(result)

    if output:
        Path(output).write_text(output_data)
        console.print(f"[green]✓[/green] Report saved to [bold]{output}[/bold]")
    else:
        # soft_wrap=True: this can be JSON/HTML/markdown -- Rich's default
        # word-wrapping would inject real newlines into long unbroken
        # tokens (e.g. a single long line of minified JSON), corrupting
        # the output when piped to a file or another tool.
        console.print(output_data, soft_wrap=True)


@cli.command()
@click.argument("package")
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
def why(package: str, path: str):
    """Explain why a dependency is installed"""
    scanner = DependencyScanner(path)
    result = scanner.scan()

    # Find the package in results
    dep = next((d for d in result.dependencies if d["name"].lower() == package.lower()), None)
    if not dep:
        console.print(f"[red]✗[/red] Package '{package}' not found")
        sys.exit(1)

    git = GitIntegration(path)
    blame_info = git.get_blame(package)

    console.print(f"\n[bold]{package}[/bold]")
    console.print(f"  Version: {dep.get('version', 'unknown')}")
    console.print(f"  Source: {dep.get('source', 'unknown')}")

    if git.is_git_repo() and blame_info.commit_hash:
        console.print(f"\n[bold]Introduced by:[/bold]")
        console.print(f"  Commit: {blame_info.commit_short}")
        console.print(f"  Author: {blame_info.author}")
        console.print(f"  Date: {blame_info.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"  Message: {blame_info.message}")
    else:
        console.print("\n[dim]Git history not available[/dim]")


@cli.command()
@click.argument("package")
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
def trace(package: str, path: str):
    """Trace dependency lineage: current status plus its full git history

    Shows whether the package is direct/transitive today, and (when the
    project is a git repository) every commit across the project's history
    that introduced, upgraded, downgraded, or removed it -- reconstructed
    from real git history, not simulated data.
    """
    scanner = DependencyScanner(path)
    result = scanner.scan()

    dep = next((d for d in result.dependencies if d["name"].lower() == package.lower()), None)

    console.print(f"\n[bold]Dependency Lineage: {package}[/bold]")

    if dep:
        dep_type = "direct" if dep.get("direct") else "transitive"
        console.print(f"  Current version: {dep.get('version') or 'unpinned'}")
        console.print(f"  Type: {dep_type}")
        console.print(f"  Declared in: {dep.get('source', 'unknown')}")
    else:
        console.print(f"  [yellow]Not currently declared in this project[/yellow]")

    git = GitIntegration(path)
    if not git.is_git_repo():
        console.print("\n[dim]Git history not available (not a git repository)[/dim]")
        return

    history = git.get_history(package)
    if not history:
        console.print("\n[dim]No history found for this package in tracked dependency files[/dim]")
        return

    table = Table(title=f"History for {package}")
    table.add_column("Date", style="cyan")
    table.add_column("Commit", style="magenta")
    table.add_column("Version", style="green")
    table.add_column("Author", style="blue")
    table.add_column("File", style="dim")
    table.add_column("Message")

    # get_history() walks commits newest-first; show oldest-first so the
    # lineage reads chronologically (introduced -> upgraded -> ... -> today).
    for entry in reversed(history):
        table.add_row(
            entry["timestamp"][:10],
            entry["commit"],
            entry.get("version") or "—",
            entry["author"],
            entry["file"],
            entry["message"],
        )

    console.print()
    console.print(table)


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
@click.option("--limit", "-l", type=int, default=20, help="Maximum packages to show")
def list(path: str, limit: int):
    """List all dependencies"""
    scanner = DependencyScanner(path)
    result = scanner.scan()

    if not result.dependencies:
        console.print("[yellow]No dependencies found[/yellow]")
        return

    table = Table(title="Dependencies")
    table.add_column("Package", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Source", style="blue")

    for i, dep in enumerate(result.dependencies):
        if i >= limit:
            table.add_row("[dim]...[/dim]", "", "", "")
            break
        dep_type = "direct" if dep.get("direct") else "transitive"
        table.add_row(dep["name"], dep.get("version") or "—", dep_type, Path(dep.get("source", "")).name)

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {result.direct_count} direct, {result.transitive_count} transitive")


def _compute_health(path: str, offline: bool, telemetry_mgr: Optional[TelemetryManager] = None):
    """Shared health computation used by both `health` and `gate`.

    Returns (ScanResult, HealthScore, vulnerabilities, dead_deps) so callers
    can both display and act on (e.g. exit-code gate) the same real data.
    """
    scanner = DependencyScanner(path)

    if telemetry_mgr:
        with telemetry_mgr.trace_scan(path):
            result = scanner.scan()
    else:
        result = scanner.scan()

    if offline:
        vulns: List[Dict] = []
        stale: List[str] = []
    else:
        vulns = scanner.check_vulnerabilities()
        stale = PackageStalenessChecker().find_stale_packages(result.dependencies)

    dead = scanner.find_dead_dependencies()
    dead_names = [d["name"] for d in dead]

    vulns_by_pkg: Dict[str, List[Dict]] = {}
    for v in vulns:
        vulns_by_pkg.setdefault(v["package_name"], []).append(v)

    analyzer = HealthAnalyzer()
    score = analyzer.compute_health_score(
        dependencies=result.dependencies,
        vulnerabilities_by_pkg=vulns_by_pkg,
        dead_deps=dead_names,
        stale_packages=stale,
    )

    if telemetry_mgr:
        telemetry_mgr.record_scan_metric(len(result.dependencies), result.direct_count, score.score)
        critical = sum(1 for v in vulns if v.get("severity") == "CRITICAL")
        high = sum(1 for v in vulns if v.get("severity") == "HIGH")
        medium = sum(1 for v in vulns if v.get("severity") == "MEDIUM")
        low = sum(1 for v in vulns if v.get("severity") == "LOW")
        telemetry_mgr.record_vulnerability_metric(critical, high, medium, low)

    return result, score, vulns, dead_names


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
@click.option(
    "--offline",
    is_flag=True,
    help="Skip network calls (OSV vulnerability lookup, PyPI staleness check) for a fully local score",
)
@click.option("--save-snapshot", is_flag=True, help="Save this scan and health score to history")
@click.option("--otel", is_flag=True, help="Emit real OpenTelemetry traces/metrics for this run")
@click.option(
    "--otel-exporter",
    type=click.Choice(["console", "otlp", "jaeger", "prometheus"]),
    default="console",
    help="OTEL exporter to use with --otel (default: console, no collector required)",
)
def health(path: str, offline: bool, save_snapshot: bool, otel: bool, otel_exporter: str):
    """Show a real, computed dependency health score

    Combines live OSV.dev vulnerability data, PyPI release staleness,
    AST-detected dead dependencies, and dependency graph complexity into a
    single weighted score (see HealthAnalyzer.compute_health_score).
    """
    telemetry_mgr = None
    if otel:
        telemetry_mgr = TelemetryManager(TelemetryConfig(enabled=True, exporter=otel_exporter))

    with console.status("[bold]Computing dependency health (scan, vulnerabilities, staleness)...[/bold]"):
        result, score, vulns, dead_names = _compute_health(path, offline, telemetry_mgr)

    from .dashboard import CLIDashboard

    dashboard = CLIDashboard(path)
    console.print(f"\n[bold]Dependency Health Score:[/bold] {score.score}/100 ({score.rating})")
    dashboard.show_health_details(score)

    console.print(f"\n  Direct dependencies: {result.direct_count}")
    console.print(f"  Transitive dependencies: {result.transitive_count}")
    console.print(f"  Total: {len(result.dependencies)}")

    if result.cycles:
        console.print(f"\n[yellow]⚠ {len(result.cycles)} cycles detected[/yellow]")
    else:
        console.print(f"\n[green]✓ No circular dependencies[/green]")

    if offline:
        console.print("\n[dim]--offline: vulnerability and staleness checks skipped[/dim]")

    if save_snapshot:
        storage = SnapshotStorage()
        storage.save_snapshot(path, result.to_dict(), health_score=score.score)
        console.print("\n[green]✓[/green] Snapshot saved with health score")

    if telemetry_mgr:
        telemetry_mgr.shutdown()


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
@click.option("--save", is_flag=True, help="Save current scan as baseline")
def snapshot(path: str, save: bool):
    """Manage dependency snapshots"""
    from .storage import SnapshotStorage
    from .dashboard import CLIDashboard

    scanner = DependencyScanner(path)
    result = scanner.scan()

    storage = SnapshotStorage()
    dashboard = CLIDashboard(path)

    if save:
        with console.status("[bold]Saving snapshot...[/bold]"):
            snapshot_id = storage.save_snapshot(path, result.to_dict())
            storage.set_baseline(path)
        console.print(f"[green]✓[/green] Snapshot saved (ID: {snapshot_id})")
    else:
        # Show latest snapshot info
        latest = storage.get_latest_snapshot(path)
        if latest:
            console.print(f"[bold]Latest Snapshot:[/bold]")
            console.print(f"  Time: {latest.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            console.print(f"  Dependencies: {latest.dependencies.get('total_count', 'unknown')}")
            console.print(f"  Health: {latest.health_score or 'unknown'}/100")
        else:
            console.print("[yellow]No snapshots found[/yellow]")


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
@click.option("--days", "-d", type=int, default=30, help="Number of days to show")
def history(path: str, days: int):
    """Show dependency history and trends"""
    from .storage import SnapshotStorage
    from .dashboard import CLIDashboard

    storage = SnapshotStorage()
    dashboard = CLIDashboard(path)

    dashboard.show_timeline(path, days=days)


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
@click.option("--baseline", "-b", type=str, default="main", help="Baseline name")
def drift(path: str, baseline: str):
    """Detect dependency drift since baseline"""
    from .storage import SnapshotStorage
    from .dashboard import CLIDashboard

    storage = SnapshotStorage()
    dashboard = CLIDashboard(path)

    latest = storage.get_latest_snapshot(path)
    if not latest:
        console.print("[yellow]No current snapshot. Run 'scan' first.[/yellow]")
        return

    baseline_snap = storage.get_baseline(path)
    if not baseline_snap:
        console.print(f"[yellow]No baseline '{baseline}' set. Run 'snapshot --save' first.[/yellow]")
        return

    drift_info = storage._compute_drift(baseline_snap.dependencies, latest.dependencies)

    if not drift_info["changed"]:
        console.print("[green]✓ No drift detected - dependency set stable[/green]")
    else:
        console.print("[yellow]⚠ Drift detected:[/yellow]")
        if drift_info["added"]:
            console.print(f"  [green]Added:[/green] {', '.join(drift_info['added'])}")
        if drift_info["removed"]:
            console.print(f"  [red]Removed:[/red] {', '.join(drift_info['removed'])}")
        if drift_info["upgraded"]:
            console.print(f"  [cyan]Upgraded:[/cyan] {len(drift_info['upgraded'])} packages")
        if drift_info["downgraded"]:
            console.print(f"  [magenta]Downgraded:[/magenta] {len(drift_info['downgraded'])} packages")

    dashboard.show_drift_report(path)


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
@click.option(
    "--format", "-f", "sbom_format", type=click.Choice(["cyclonedx", "spdx"]), default="cyclonedx", help="SBOM format"
)
@click.option("--output", "-o", type=click.Path(), help="Output file path (defaults to stdout)")
@click.option("--sign", is_flag=True, help="Sign the SBOM with a private key (requires --key)")
@click.option("--key", "key_path", type=click.Path(exists=True), help="Path to a PEM RSA private key for --sign")
def export(path: str, sbom_format: str, output: Optional[str], sign: bool, key_path: Optional[str]):
    """Export a Software Bill of Materials (SBOM) for the project

    Supports CycloneDX 1.4 and SPDX 2.3 JSON, the two SBOM formats required
    by most supply-chain-security policies (e.g. US EO 14028). Every SBOM
    also carries a SHA-256 integrity hash; pass --sign with an RSA private
    key to additionally attach a cryptographic signature.
    """
    scanner = DependencyScanner(path)
    with console.status("[bold]Scanning project...[/bold]"):
        result = scanner.scan()

    project_name = Path(path).resolve().name

    if sbom_format == "cyclonedx":
        sbom = SBOMGenerator.generate_cyclonedx(result.dependencies, project_name=project_name)
    else:
        sbom = SBOMGenerator.generate_spdx(result.dependencies, project_name=project_name)

    sbom["integrityHash"] = SBOMGenerator.compute_integrity_hash(sbom)

    if sign:
        if not key_path:
            console.print("[red]✗[/red] --sign requires --key <path-to-private-key.pem>")
            sys.exit(1)
        signer = SBOMSigner(private_key_path=key_path)
        if not signer.private_key:
            console.print("[red]✗[/red] Failed to load signing key (see logs); SBOM not signed")
            sys.exit(1)
        sbom = signer.sign_sbom(sbom)

    output_data = json.dumps(sbom, indent=2)

    if output:
        Path(output).write_text(output_data)
        console.print(
            f"[green]✓[/green] {sbom_format.upper()} SBOM ({len(result.dependencies)} components) saved to [bold]{output}[/bold]"
        )
    else:
        # soft_wrap=True: SBOM signatures/integrity hashes are long,
        # unbroken tokens -- Rich's default wrapping would inject real
        # newlines into them and produce invalid JSON when piped/redirected.
        console.print(output_data, soft_wrap=True)


@cli.command(name="licenses")
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
@click.option(
    "--project-license", type=str, default=None, help="Your project's license (e.g. MIT) for compatibility check"
)
@click.option("--fail-on-restricted", is_flag=True, help="Exit non-zero if any restricted/copyleft license is found")
def licenses_cmd(path: str, project_license: Optional[str], fail_on_restricted: bool):
    """Analyze dependency licenses for supply-chain compliance risk

    Fetches license metadata from PyPI for every declared dependency,
    classifies each as permissive/copyleft/restricted/unknown, and
    optionally checks compatibility against your project's own license.
    """
    scanner = DependencyScanner(path)
    with console.status("[bold]Scanning project...[/bold]"):
        result = scanner.scan()

    analyzer = LicenseAnalyzer()
    with console.status("[bold]Fetching license metadata from PyPI...[/bold]"):
        report = analyzer.analyze_project_licenses(result.dependencies)

    risk_styles = {"permissive": "green", "copyleft": "yellow", "restricted": "red", "unknown": "dim"}

    table = Table(title="License Compliance Report")
    table.add_column("Package", style="cyan")
    table.add_column("License(s)")
    table.add_column("Risk")

    for pkg in report["packages"]:
        style = risk_styles.get(pkg["risk"], "white")
        table.add_row(pkg["name"], ", ".join(pkg["licenses"]) or "Unknown", f"[{style}]{pkg['risk']}[/{style}]")

    console.print(table)
    console.print(
        f"\n[bold]Summary:[/bold] {report['permissive']} permissive, {report['copyleft']} copyleft, "
        f"{report['restricted']} restricted, {report['unknown']} unknown (of {report['total']} total)"
    )

    conflicts: List[str] = []
    if project_license:
        all_licenses = [lic for pkg in report["packages"] for lic in pkg["licenses"]]
        compatible, conflicts = analyzer.check_compatibility(project_license, all_licenses)
        if compatible:
            console.print(f"\n[green]✓[/green] All dependency licenses compatible with {project_license}")
        else:
            console.print(f"\n[red]✗[/red] License conflicts detected against {project_license}:")
            for conflict in conflicts:
                console.print(f"  - {conflict}")

    if fail_on_restricted and (report["restricted"] > 0 or conflicts):
        sys.exit(1)


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
@click.option("--min-health", type=int, default=50, help="Minimum acceptable health score (0-100)")
@click.option("--max-dead-deps", type=int, default=10, help="Maximum acceptable count of unused dependencies")
@click.option("--offline", is_flag=True, help="Skip network calls (OSV/PyPI) for a fully local gate check")
def gate(path: str, min_health: int, max_dead_deps: int, offline: bool):
    """CI gate: exit non-zero if the project fails dependency health criteria

    Designed for GitHub Actions (and any other CI): computes the same real
    health score as `health`, emits GitHub Actions ::error/::warning/::notice
    annotations when running inside a GitHub Actions job (detected via the
    GITHUB_ACTIONS env var), and always sets the process exit code so the
    step (and therefore the job) fails correctly on either platform.
    """
    with console.status("[bold]Computing dependency health for CI gate...[/bold]"):
        result, score, vulns, dead_names = _compute_health(path, offline)

    critical_vulns = sum(1 for v in vulns if v.get("severity") == "CRITICAL")

    reporter = GitHubActionsReporter()
    vulns_by_pkg: Dict[str, List[Dict]] = {}
    for v in vulns:
        vulns_by_pkg.setdefault(v["package_name"], []).append(v)
    reporter.report_vulnerabilities(vulns_by_pkg)
    reporter.report_dead_dependencies(dead_names)
    reporter.report_health_score(score.score, score.issues)

    should_fail = reporter.fail_if_criteria_met(
        health_score=score.score,
        critical_vulns=critical_vulns,
        dead_deps_threshold=max_dead_deps,
        dead_deps_count=len(dead_names),
    )

    # fail_if_criteria_met() only checks health_score < 50 internally; honor
    # a stricter caller-provided --min-health too.
    if score.score < min_health:
        should_fail = True

    console.print(f"\n[bold]Health Score:[/bold] {score.score}/100 ({score.rating})")
    console.print(f"[bold]Critical vulnerabilities:[/bold] {critical_vulns}")
    console.print(f"[bold]Unused dependencies:[/bold] {len(dead_names)}")

    if should_fail:
        console.print("\n[red]✗ Gate FAILED[/red]")
        sys.exit(1)
    else:
        console.print("\n[green]✓ Gate PASSED[/green]")
        sys.exit(0)


def _format_table_report(result: ScanResult) -> str:
    """Format scan result as a table"""
    lines = [
        f"Dependency Scan Report",
        f"{'='*60}",
        f"Total dependencies: {len(result.dependencies)}",
        f"  Direct: {result.direct_count}",
        f"  Transitive: {result.transitive_count}",
        f"",
    ]

    if result.dependencies:
        lines.append("Top 10 Dependencies:")
        lines.append(f"{'Name':<25} {'Version':<15} {'Type':<12}")
        lines.append("-" * 60)

        for i, dep in enumerate(result.dependencies[:10]):
            dep_type = "direct" if dep.get("direct") else "transitive"
            version = dep.get("version") or "—"
            lines.append(f"{dep['name']:<25} {version:<15} {dep_type:<12}")

        if len(result.dependencies) > 10:
            lines.append(f"... and {len(result.dependencies) - 10} more")

    return "\n".join(lines)


def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
