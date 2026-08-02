"""PyDependencyCheck CLI: Command-line interface for dependency analysis"""

import click
import json
from pathlib import Path
from typing import Optional
import sys

from .scanner import DependencyScanner, ScanResult
from .reporters import JsonReporter, HtmlReporter, MarkdownReporter
from .storage import SnapshotStorage
from .git_integration import GitIntegration
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
@click.option("--format", "-f", type=click.Choice(["json", "html", "markdown", "table"]), default="table", help="Output format")
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
        console.print(output_data)


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
    """Trace dependency lineage (where it comes from)"""
    console.print(f"\n[bold]Dependency Lineage for {package}:[/bold]")
    console.print(f"  {package} (to be implemented in graph phase)")
    console.print("\n[dim]Coming in Phase 1 finale: full dependency chain visualization[/dim]")


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
        table.add_row(
            dep["name"],
            dep.get("version") or "—",
            dep_type,
            Path(dep.get("source", "")).name
        )

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {result.direct_count} direct, {result.transitive_count} transitive")


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
def health(path: str):
    """Show dependency health score"""
    scanner = DependencyScanner(path)
    result = scanner.scan()

    # TODO: Compute real health score (Phase 3)
    health_score = 72
    console.print(f"\n[bold]Dependency Health Score:[/bold] {health_score}/100")
    console.print(f"  Direct dependencies: {result.direct_count}")
    console.print(f"  Transitive dependencies: {result.transitive_count}")
    console.print(f"  Total: {len(result.dependencies)}")

    if result.cycles:
        console.print(f"\n[yellow]⚠ {len(result.cycles)} cycles detected[/yellow]")
    else:
        console.print(f"\n[green]✓ No circular dependencies[/green]")


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
