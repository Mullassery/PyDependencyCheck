"""Git integration for blame tracking and history analysis"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from git import Commit, GitCommandError, Repo
except ImportError:
    Repo = None
    Commit = None
    GitCommandError = None

logger = logging.getLogger(__name__)


class BlameInfo:
    """Information about when/who added a dependency"""

    def __init__(self):
        self.package: str = ""
        self.commit_hash: str = ""
        self.commit_short: str = ""
        self.author: str = ""
        self.author_email: str = ""
        self.timestamp: datetime = datetime.now()
        self.message: str = ""
        self.file: str = ""
        self.line_no: int = 0


class GitIntegration:
    """Git integration for dependency provenance tracking"""

    DEPENDENCY_FILES = [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "Pipfile",
        "poetry.lock",
        "uv.lock",
    ]

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.repo: Optional[Any] = None

        if Repo is not None:
            try:
                self.repo = Repo(project_path)
                logger.info(f"Git repo initialized: {self.repo.working_dir}")
            except Exception as e:
                logger.debug(f"Failed to initialize git repo: {e}")

    def is_git_repo(self) -> bool:
        """Check if project is in a git repository"""
        return self.repo is not None

    def get_blame(self, package: str, filename: Optional[str] = None) -> BlameInfo:
        """Get git blame information for a dependency

        Args:
            package: Package name to search for
            filename: Optional specific file to check (e.g., requirements.txt)

        Returns:
            BlameInfo with commit details
        """
        info = BlameInfo()
        info.package = package

        if not self.repo:
            logger.warning("Git not initialized")
            return info

        try:
            # Search in dependency files
            search_files = []
            if filename:
                search_files = [filename]
            else:
                # Search in all dependency files
                for dep_file in self.DEPENDENCY_FILES:
                    path = self.project_path / dep_file
                    if path.exists():
                        search_files.append(str(path.relative_to(self.project_path)))

            for file_path in search_files:
                try:
                    # Get blame for this file
                    blame_data = list(self.repo.blame("HEAD", file_path))

                    for commit, lines in blame_data:
                        for line in lines:
                            # Check if package name is in this line
                            if self._is_package_in_line(package, line):
                                info.commit_hash = commit.hexsha
                                info.commit_short = commit.hexsha[:7]
                                info.author = commit.author.name
                                info.author_email = commit.author.email
                                info.timestamp = datetime.fromtimestamp(commit.committed_date)
                                info.message = commit.message.split("\n")[0]
                                info.file = file_path
                                info.line_no = len(lines)
                                return info
                except GitCommandError as e:
                    logger.debug(f"Git blame failed for {file_path}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Blame lookup error: {e}")

        return info

    def get_history(self, package: str) -> List[Dict[str, Any]]:
        """Get full history of a dependency across commits

        Shows when package was added, upgraded, downgraded, or removed.
        """
        history = []

        if not self.repo:
            return history

        try:
            for file_path in self.DEPENDENCY_FILES:
                path = self.project_path / file_path
                if not path.exists():
                    continue

                try:
                    commits = list(self.repo.iter_commits(paths=str(path)))

                    for commit in commits:
                        try:
                            content = commit.tree[file_path].data_stream.read().decode()
                            if self._is_package_in_content(package, content):
                                version = self._extract_version(package, content)
                                history.append(
                                    {
                                        "commit": commit.hexsha[:7],
                                        "author": commit.author.name,
                                        "timestamp": datetime.fromtimestamp(commit.committed_date).isoformat(),
                                        "message": commit.message.split("\n")[0],
                                        "version": version,
                                        "file": file_path,
                                    }
                                )
                        except Exception:
                            continue

                except Exception as e:
                    logger.debug(f"History lookup error for {file_path}: {e}")

        except Exception as e:
            logger.error(f"History lookup error: {e}")

        return history

    def get_commit_deps(self, commit_hash: str) -> Dict[str, List[str]]:
        """Get all dependencies at a specific commit"""
        deps = {}

        if not self.repo:
            return deps

        try:
            commit = self.repo.commit(commit_hash)

            for file_path in self.DEPENDENCY_FILES:
                try:
                    content = commit.tree[file_path].data_stream.read().decode()
                    parsed_deps = self._parse_content(content)
                    deps[file_path] = parsed_deps
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Failed to get commit deps: {e}")

        return deps

    def _is_package_in_line(self, package: str, line: str) -> bool:
        """Check if package name appears in a line"""
        # Normalize: "requests" matches "requests==2.0" or "requests[security]"
        line_lower = line.lower()
        pkg_lower = package.lower().replace("_", "-")
        return pkg_lower in line_lower

    def _is_package_in_content(self, package: str, content: str) -> bool:
        """Check if package appears in file content"""
        pkg_lower = package.lower().replace("_", "-")
        return pkg_lower in content.lower()

    def _extract_version(self, package: str, content: str) -> Optional[str]:
        """Extract version of package from content"""
        for line in content.split("\n"):
            if self._is_package_in_line(package, line):
                # Simple extraction: split on ==, >=, etc.
                for op in ["==", ">=", "<=", "!=", "~=", ">"]:
                    if op in line:
                        parts = line.split(op)
                        if len(parts) > 1:
                            version = parts[1].strip().split(",")[0].split(";")[0].strip()
                            return version
                return None
        return None

    def _parse_content(self, content: str) -> List[str]:
        """Parse dependency file content and extract package names"""
        packages = []
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Simple extraction of package name
            name = line.split("==")[0].split(">=")[0].split("[")[0].strip()
            if name and name.lower() not in ("python",):
                packages.append(name)
        return packages
