"""PyDependencyCheck CLI: Command-line interface for dependency analysis"""

import click
import json
from pathlib import Path
from typing import Optional

from .scanner import DependencyScanner
from .reporters import JsonReporter, HtmlReporter
from .storage import SnapshotStorage
from .git_integration import GitIntegration


@click.group()
@click.version_option()
def cli():
    """PyDependencyCheck - Dependency Intelligence Platform

    Scan dependencies, analyze usage, detect vulnerabilities, and track supply chain.
    """
    pass


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path to scan")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "-f", type=click.Choice(["json", "html", "markdown"]), default="json", help="Output format")
def scan(path: str, output: Optional[str], format: str):
    """Scan a project for dependencies"""
    click.echo(f"Scanning {path}...")

    scanner = DependencyScanner(path)
    result = scanner.scan()

    click.echo(f"Found {len(result)} dependencies")

    if format == "json":
        reporter = JsonReporter()
    elif format == "html":
        reporter = HtmlReporter()
    else:
        reporter = JsonReporter()

    output_data = reporter.generate(result)

    if output:
        with open(output, "w") as f:
            f.write(output_data)
        click.echo(f"Report saved to {output}")
    else:
        click.echo(output_data)


@cli.command()
@click.argument("package")
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
def why(package: str, path: str):
    """Explain why a dependency is installed"""
    scanner = DependencyScanner(path)
    result = scanner.scan()

    git_integration = GitIntegration(path)
    blame_info = git_integration.get_blame(package)

    click.echo(f"\n{package}")
    click.echo("\nInstalled because:")
    click.echo(f"  {blame_info.get('message', 'Unknown')}")
    click.echo(f"\nIntroduced by:")
    click.echo(f"  Commit: {blame_info.get('commit', 'Unknown')}")
    click.echo(f"  Author: {blame_info.get('author', 'Unknown')}")
    click.echo(f"  Date: {blame_info.get('date', 'Unknown')}")


@cli.command()
@click.argument("package")
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
def trace(package: str, path: str):
    """Trace dependency lineage"""
    scanner = DependencyScanner(path)
    result = scanner.scan()

    click.echo(f"\nDependency chain for {package}:")
    # TODO: Implement dependency chain tracing
    click.echo(f"  app -> {package}")


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
def list_deps(path: str):
    """List all dependencies"""
    scanner = DependencyScanner(path)
    result = scanner.scan()

    click.echo("\nDependencies:")
    for dep in result:
        click.echo(f"  {dep['name']}")


@cli.command()
@click.option("--path", "-p", type=click.Path(exists=True), default=".", help="Project path")
def health(path: str):
    """Show dependency health score"""
    scanner = DependencyScanner(path)
    result = scanner.scan()

    # TODO: Compute health score
    health_score = 72
    click.echo(f"\nDependency Health Score: {health_score}/100")


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
