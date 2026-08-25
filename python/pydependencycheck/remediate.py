"""Automated remediation: turn OSV-reported vulnerability fixes into real
dependency-file patches, and optionally a real git branch + commit (and a
GitHub PR via the `gh` CLI, if it's installed and authenticated).

This is the "Automated PR remediation patches" gap called out in
docs/ROADMAP.md's Known Limitations -- previously the tool only reported
findings; there was no path from "OSV says package X has a fix in version Y"
to an actual file change, let alone a branch/PR. `compute_fixes` maps
`DependencyScanner.check_vulnerabilities()` output onto pinned dependencies,
`patch_file_content` rewrites the exact `==` pin in-place (regex-scoped to
the specific package name so it can't touch an unrelated line), and
`RemediationRunner` wires that into real `git`/`gh` operations.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .scanner import exact_pin_version

try:
    from git import GitCommandError, Repo
except ImportError:  # pragma: no cover - gitpython is a hard dependency, see pyproject.toml
    Repo = None
    GitCommandError = None

logger = logging.getLogger(__name__)


def _normalize(name: str) -> str:
    """PyPI package names are case-insensitive and treat '-'/'_'/'.' as
    equivalent (PEP 503); this is how OSV package_name and a manifest's
    on-disk package name can legitimately differ in spelling."""
    return re.sub(r"[-_.]+", "-", name).lower()


@dataclass
class PackageFix:
    """A single package's vulnerable-pin -> fixed-version remediation."""

    name: str
    current_version: Optional[str]
    fix_version: str
    vulnerability_ids: List[str]
    source_files: List[str]


@dataclass
class RemediationPlan:
    """The full set of fixes computed for a project, plus the resulting
    file patches (before anything is written to disk)."""

    fixes: List[PackageFix] = field(default_factory=list)
    # file path (relative to project root) -> (old_content, new_content)
    patches: Dict[str, "tuple[str, str]"] = field(default_factory=dict)

    @property
    def has_fixes(self) -> bool:
        return bool(self.fixes)

    def diff(self, file_path: str) -> str:
        import difflib

        old, new = self.patches[file_path]
        return "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
            )
        )


def compute_fixes(dependencies: List[Dict[str, Any]], vulnerabilities: List[Dict[str, Any]]) -> List[PackageFix]:
    """Map vulnerability-scan results onto pinned dependencies that have a
    known fix. Only packages with `fix_available` and a `fix_version` that
    actually differs from the currently pinned version are included --
    everything else has no concrete patch to apply.

    Only exact `==` pins are considered: `dep["version"]` stores the full
    PEP 508 specifier, and a range/compatible-release constraint doesn't
    name one concrete "current version" to compare or patch (see
    `scanner.exact_pin_version`).
    """
    dep_by_name = {}
    for d in dependencies:
        version = exact_pin_version(d.get("version"))
        if version is not None:
            dep_by_name[_normalize(d["name"])] = (d, version)

    fixes_by_name: Dict[str, PackageFix] = {}
    for vuln in vulnerabilities:
        if not vuln.get("fix_available") or not vuln.get("fix_version"):
            continue

        key = _normalize(vuln["package_name"])
        entry = dep_by_name.get(key)
        if entry is None:
            continue
        dep, current_version = entry

        if current_version == vuln["fix_version"]:
            continue

        existing = fixes_by_name.get(key)
        if existing is None:
            fixes_by_name[key] = PackageFix(
                name=dep["name"],
                current_version=current_version,
                fix_version=vuln["fix_version"],
                vulnerability_ids=[vuln["id"]],
                source_files=list(dep.get("sources") or [dep.get("source", "")]),
            )
        else:
            existing.vulnerability_ids.append(vuln["id"])
            # If multiple vulnerabilities on the same package have
            # different fix versions, take the highest one so the single
            # patch resolves all of them at once.
            if _version_key(vuln["fix_version"]) > _version_key(existing.fix_version):
                existing.fix_version = vuln["fix_version"]

    return list(fixes_by_name.values())


def _version_key(version: str) -> tuple:
    """Best-effort sortable key for a version string; falls back to the raw
    string for anything that isn't dotted-numeric (e.g. '2024.1a1')."""
    parts = []
    for p in version.split("."):
        digits = re.match(r"\d+", p)
        parts.append(int(digits.group()) if digits else -1)
    return tuple(parts) if parts else (0,)


# Matches a requirements.txt/constraints.txt line pinning `name` with `==`,
# capturing everything up to (but not including) a trailing comment/marker
# so extras (`name[extra]==1.0`) and environment markers are preserved.
def _requirements_pin_pattern(name: str) -> "re.Pattern[str]":
    escaped = re.escape(name)
    # '-', '_', '.' are interchangeable in PyPI names (PEP 503); match any
    # of the on-disk spellings for the same normalized name.
    flexible = re.sub(r"\\[-_.]", "[-_.]", escaped)
    return re.compile(
        rf"^([ \t]*{flexible}(?:\[[^\]]*\])?[ \t]*==[ \t]*)([^\s;#]+)",
        re.IGNORECASE | re.MULTILINE,
    )


def patch_requirements_content(content: str, fixes: List[PackageFix]) -> str:
    for fix in fixes:
        pattern = _requirements_pin_pattern(fix.name)
        content = pattern.sub(lambda m: m.group(1) + fix.fix_version, content)
    return content


# Matches a `=="<version>"`/`== "<version>"` pin inside a quoted PEP 508
# requirement string anywhere in a TOML file, e.g. `"requests==2.32.0"` in a
# `dependencies = [...]` array, or `flask==2.0.0` in a Poetry-style table
# (`requests = "==2.32.0"`).
def _toml_pin_pattern(name: str) -> "re.Pattern[str]":
    escaped = re.escape(name)
    flexible = re.sub(r"\\[-_.]", "[-_.]", escaped)
    return re.compile(rf"({flexible}(?:\[[^\]\"']*\])?==)([^\s\"';,]+)", re.IGNORECASE)


def patch_pyproject_content(content: str, fixes: List[PackageFix]) -> str:
    for fix in fixes:
        pattern = _toml_pin_pattern(fix.name)
        content = pattern.sub(lambda m: m.group(1) + fix.fix_version, content)
    return content


def _patch_file(file_path: Path, fixes: List[PackageFix]) -> Optional[str]:
    content = file_path.read_text(encoding="utf-8")
    name_lower = file_path.name.lower()

    if "requirements" in name_lower or name_lower == "constraints.txt":
        new_content = patch_requirements_content(content, fixes)
    elif name_lower == "pyproject.toml":
        new_content = patch_pyproject_content(content, fixes)
    else:
        # setup.py/setup.cfg and other formats aren't remediated
        # automatically -- same limitation the scanner has parsing them
        # (see DependencyScanner._parse_setup_file).
        return None

    return new_content if new_content != content else None


def build_remediation_plan(
    project_path: str, dependencies: List[Dict[str, Any]], vulnerabilities: List[Dict[str, Any]]
) -> RemediationPlan:
    """Compute fixes and the resulting file patches, without writing
    anything to disk."""
    plan = RemediationPlan(fixes=compute_fixes(dependencies, vulnerabilities))
    if not plan.fixes:
        return plan

    root = Path(project_path).resolve()
    fixes_by_file: Dict[str, List[PackageFix]] = {}
    for fix in plan.fixes:
        for source in fix.source_files:
            fixes_by_file.setdefault(source, []).append(fix)

    for rel_path, file_fixes in fixes_by_file.items():
        file_path = root / rel_path
        if not file_path.is_file():
            continue
        old_content = file_path.read_text(encoding="utf-8")
        new_content = _patch_file(file_path, file_fixes)
        if new_content is not None:
            plan.patches[rel_path] = (old_content, new_content)

    return plan


def apply_plan(project_path: str, plan: RemediationPlan) -> List[str]:
    """Write every patch in `plan` to disk for real. Returns the list of
    file paths (relative to project_path) that were changed."""
    root = Path(project_path).resolve()
    written = []
    for rel_path, (_old, new_content) in plan.patches.items():
        (root / rel_path).write_text(new_content, encoding="utf-8")
        written.append(rel_path)
    return written


class RemediationError(Exception):
    """Raised when a git/gh operation required for --pr fails."""


class RemediationRunner:
    """Real git branch/commit creation, and a real `gh pr create` when the
    `gh` CLI is installed, authenticated, and the repo has a remote --
    otherwise the branch/commit are still real and left ready to push
    manually. Nothing here is a stub: every method either performs the
    actual git/gh operation or raises/returns a clearly-labeled reason it
    couldn't.
    """

    def __init__(self, project_path: str):
        if Repo is None:
            raise RemediationError("gitpython is not installed")
        self.project_path = Path(project_path).resolve()
        try:
            self.repo = Repo(str(self.project_path))
        except Exception as e:
            raise RemediationError(f"not a git repository: {e}") from e

    def create_branch_and_commit(self, plan: RemediationPlan, branch_name: Optional[str] = None) -> str:
        """Create a new branch off the current HEAD, write and commit the
        patches in `plan`. Returns the branch name. Raises RemediationError
        if the working tree is dirty (to avoid committing unrelated
        changes) or the branch already exists."""
        if self.repo.is_dirty(untracked_files=False):
            raise RemediationError("working tree has uncommitted changes -- commit or stash them before --pr")

        if branch_name is None:
            branch_name = f"pydependencycheck/fix-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if branch_name in [h.name for h in self.repo.heads]:
            raise RemediationError(f"branch '{branch_name}' already exists")

        new_branch = self.repo.create_head(branch_name)
        new_branch.checkout()

        written = apply_plan(str(self.project_path), plan)
        if not written:
            raise RemediationError("no files were changed by the remediation plan")

        self.repo.index.add(written)
        self.repo.index.commit(self._commit_message(plan))

        return branch_name

    def _commit_message(self, plan: RemediationPlan) -> str:
        lines = ["fix: bump vulnerable dependencies to their patched versions", ""]
        for fix in plan.fixes:
            ids = ", ".join(fix.vulnerability_ids)
            lines.append(f"- {fix.name}: {fix.current_version} -> {fix.fix_version} ({ids})")
        return "\n".join(lines)

    def push_branch(self, branch_name: str, remote_name: str = "origin") -> None:
        try:
            remote = self.repo.remote(remote_name)
        except ValueError as e:
            raise RemediationError(f"no remote named '{remote_name}': {e}") from e
        try:
            remote.push(refspec=f"{branch_name}:{branch_name}")
        except GitCommandError as e:
            raise RemediationError(f"git push failed: {e}") from e

    def create_pull_request(self, branch_name: str, base_branch: str, title: str, body: str) -> Optional[str]:
        """Open a real PR via the `gh` CLI. Returns the PR URL, or None if
        `gh` isn't installed/authenticated -- the branch/commit created by
        `create_branch_and_commit` are still real and pushed, just not
        auto-PR'd, so the caller can open one manually."""
        gh_path = shutil.which("gh")
        if gh_path is None:
            logger.info("`gh` CLI not found; branch was created/pushed but no PR was opened")
            return None

        try:
            result = subprocess.run(
                [
                    gh_path,
                    "pr",
                    "create",
                    "--head",
                    branch_name,
                    "--base",
                    base_branch,
                    "--title",
                    title,
                    "--body",
                    body,
                ],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (subprocess.TimeoutExpired, OSError) as e:
            logger.warning(f"`gh pr create` failed to run: {e}")
            return None

        if result.returncode != 0:
            logger.warning(f"`gh pr create` failed: {result.stderr.strip()}")
            return None

        return result.stdout.strip()
