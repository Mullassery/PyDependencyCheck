"""Tests for automated remediation: computing fixes from vulnerability scan
results, patching real dependency files, and creating a real git
branch/commit/PR for the fix.

`docs/ROADMAP.md`'s Known Limitations called this out as a verified real
gap ("Automated PR remediation patches") -- the tool only ever reported
findings, with no path from "OSV says there's a fix" to an actual file
change or PR. These tests exercise the real logic end-to-end: real file
I/O, a real local git repo (via gitpython), and a real local bare repo as
the push target, not mocks standing in for git.
"""

import pytest
from click.testing import CliRunner
from git import Repo
from pydependencycheck.cli import cli
from pydependencycheck.remediate import (
    PackageFix,
    RemediationError,
    RemediationRunner,
    apply_plan,
    build_remediation_plan,
    compute_fixes,
    patch_pyproject_content,
    patch_requirements_content,
)


def _dep(name, version, sources=None):
    return {"name": name, "version": version, "sources": sources or ["requirements.txt"]}


def _vuln(package_name, fix_version, vuln_id="GHSA-xxxx", fix_available=True):
    return {
        "id": vuln_id,
        "package_name": package_name,
        "fix_available": fix_available,
        "fix_version": fix_version,
    }


class TestComputeFixes:
    def test_matches_vulnerable_pinned_package(self):
        deps = [_dep("requests", "2.25.0")]
        vulns = [_vuln("requests", "2.31.0")]

        fixes = compute_fixes(deps, vulns)

        assert len(fixes) == 1
        assert fixes[0].name == "requests"
        assert fixes[0].current_version == "2.25.0"
        assert fixes[0].fix_version == "2.31.0"
        assert fixes[0].vulnerability_ids == ["GHSA-xxxx"]

    def test_ignores_vuln_without_fix_available(self):
        deps = [_dep("requests", "2.25.0")]
        vulns = [_vuln("requests", None, fix_available=False)]

        assert compute_fixes(deps, vulns) == []

    def test_ignores_vuln_for_unpinned_or_unknown_package(self):
        deps = [_dep("flask", "2.0.0")]
        vulns = [_vuln("requests", "2.31.0")]

        assert compute_fixes(deps, vulns) == []

    def test_skips_when_already_at_fix_version(self):
        deps = [_dep("requests", "2.31.0")]
        vulns = [_vuln("requests", "2.31.0")]

        assert compute_fixes(deps, vulns) == []

    def test_name_matching_is_case_and_separator_insensitive(self):
        # PEP 503: 'Django_Rest-Framework' and 'django-rest-framework' are
        # the same package.
        deps = [_dep("Django_Rest-Framework", "3.0.0")]
        vulns = [_vuln("django-rest-framework", "3.14.0")]

        fixes = compute_fixes(deps, vulns)

        assert len(fixes) == 1
        assert fixes[0].name == "Django_Rest-Framework"
        assert fixes[0].fix_version == "3.14.0"

    def test_multiple_vulns_on_same_package_merge_and_take_highest_fix(self):
        deps = [_dep("requests", "2.20.0")]
        vulns = [
            _vuln("requests", "2.25.0", vuln_id="GHSA-1"),
            _vuln("requests", "2.31.0", vuln_id="GHSA-2"),
        ]

        fixes = compute_fixes(deps, vulns)

        assert len(fixes) == 1
        assert fixes[0].fix_version == "2.31.0"
        assert set(fixes[0].vulnerability_ids) == {"GHSA-1", "GHSA-2"}


class TestPatchRequirementsContent:
    def test_bumps_exact_pin(self):
        content = "requests==2.25.0\nflask==2.0.0\n"
        fixes = [PackageFix("requests", "2.25.0", "2.31.0", ["G"], ["requirements.txt"])]

        result = patch_requirements_content(content, fixes)

        assert "requests==2.31.0" in result
        assert "flask==2.0.0" in result  # untouched

    def test_preserves_extras_and_markers(self):
        content = 'requests[security]==2.25.0; python_version >= "3.8"\n'
        fixes = [PackageFix("requests", "2.25.0", "2.31.0", ["G"], ["requirements.txt"])]

        result = patch_requirements_content(content, fixes)

        assert result == 'requests[security]==2.31.0; python_version >= "3.8"\n'

    def test_does_not_touch_prefix_matching_package(self):
        # 'requests-toolbelt' must not be affected by a fix for 'requests'.
        content = "requests==2.25.0\nrequests-toolbelt==0.9.1\n"
        fixes = [PackageFix("requests", "2.25.0", "2.31.0", ["G"], ["requirements.txt"])]

        result = patch_requirements_content(content, fixes)

        assert "requests==2.31.0" in result
        assert "requests-toolbelt==0.9.1" in result

    def test_matches_dash_underscore_dot_interchangeably(self):
        content = "django_rest_framework==3.0.0\n"
        fixes = [PackageFix("django-rest-framework", "3.0.0", "3.14.0", ["G"], ["requirements.txt"])]

        result = patch_requirements_content(content, fixes)

        assert "django_rest_framework==3.14.0" in result


class TestPatchPyprojectContent:
    def test_bumps_pin_inside_dependency_array(self):
        content = 'dependencies = [\n    "requests==2.25.0",\n    "click>=8.0",\n]\n'
        fixes = [PackageFix("requests", "2.25.0", "2.31.0", ["G"], ["pyproject.toml"])]

        result = patch_pyproject_content(content, fixes)

        assert '"requests==2.31.0"' in result
        assert '"click>=8.0"' in result


class TestBuildRemediationPlanAndApply:
    def test_full_plan_and_apply_writes_real_file(self, tmp_path):
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests==2.25.0\nflask==2.0.0\n")

        deps = [
            _dep("requests", "2.25.0", sources=["requirements.txt"]),
            _dep("flask", "2.0.0", sources=["requirements.txt"]),
        ]
        vulns = [_vuln("requests", "2.31.0")]

        plan = build_remediation_plan(str(tmp_path), deps, vulns)

        assert plan.has_fixes
        assert "requirements.txt" in plan.patches
        diff = plan.diff("requirements.txt")
        assert "-requests==2.25.0" in diff
        assert "+requests==2.31.0" in diff

        # Dry run: file on disk must be untouched until apply_plan runs.
        assert req_file.read_text() == "requests==2.25.0\nflask==2.0.0\n"

        written = apply_plan(str(tmp_path), plan)

        assert written == ["requirements.txt"]
        assert req_file.read_text() == "requests==2.31.0\nflask==2.0.0\n"

    def test_no_fixes_when_no_vulnerabilities(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("requests==2.25.0\n")
        deps = [_dep("requests", "2.25.0")]

        plan = build_remediation_plan(str(tmp_path), deps, [])

        assert not plan.has_fixes
        assert plan.patches == {}

    def test_unsupported_file_type_produces_no_patch(self, tmp_path):
        (tmp_path / "setup.py").write_text("install_requires=['requests==2.25.0']\n")
        deps = [_dep("requests", "2.25.0", sources=["setup.py"])]
        vulns = [_vuln("requests", "2.31.0")]

        plan = build_remediation_plan(str(tmp_path), deps, vulns)

        # A fix is computed (there IS a known fix)...
        assert plan.has_fixes
        # ...but setup.py isn't a format the patcher understands, so no
        # file patch is produced for it.
        assert plan.patches == {}


@pytest.fixture
def git_project(tmp_path):
    """A real git repo with a committed requirements.txt containing a
    vulnerable pin, on branch 'main'."""
    repo = Repo.init(tmp_path, initial_branch="main")
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Test User")
        cw.set_value("user", "email", "test@example.com")

    (tmp_path / "requirements.txt").write_text("requests==2.25.0\n")
    repo.index.add(["requirements.txt"])
    repo.index.commit("initial commit")

    return tmp_path, repo


class TestRemediationRunner:
    def test_create_branch_and_commit_makes_a_real_commit(self, git_project):
        project_path, repo = git_project
        deps = [_dep("requests", "2.25.0", sources=["requirements.txt"])]
        vulns = [_vuln("requests", "2.31.0", vuln_id="GHSA-abcd")]
        plan = build_remediation_plan(str(project_path), deps, vulns)

        runner = RemediationRunner(str(project_path))
        branch_name = runner.create_branch_and_commit(plan, branch_name="fix/requests")

        assert branch_name == "fix/requests"
        assert repo.active_branch.name == "fix/requests"
        assert (project_path / "requirements.txt").read_text() == "requests==2.31.0\n"

        latest_commit = repo.head.commit
        assert "requests" in latest_commit.message
        assert "GHSA-abcd" in latest_commit.message
        # The branch we started on ('main') must be untouched.
        main_content = repo.commit("main").tree["requirements.txt"].data_stream.read().decode()
        assert main_content == "requests==2.25.0\n"

    def test_refuses_dirty_working_tree(self, git_project):
        project_path, repo = git_project
        (project_path / "requirements.txt").write_text("requests==2.25.0  # local edit\n")
        deps = [_dep("requests", "2.25.0", sources=["requirements.txt"])]
        vulns = [_vuln("requests", "2.31.0")]
        plan = build_remediation_plan(str(project_path), deps, vulns)

        runner = RemediationRunner(str(project_path))
        with pytest.raises(RemediationError, match="uncommitted changes"):
            runner.create_branch_and_commit(plan, branch_name="fix/requests")

    def test_refuses_existing_branch_name(self, git_project):
        project_path, repo = git_project
        repo.create_head("fix/requests")
        deps = [_dep("requests", "2.25.0", sources=["requirements.txt"])]
        vulns = [_vuln("requests", "2.31.0")]
        plan = build_remediation_plan(str(project_path), deps, vulns)

        runner = RemediationRunner(str(project_path))
        with pytest.raises(RemediationError, match="already exists"):
            runner.create_branch_and_commit(plan, branch_name="fix/requests")

    def test_non_git_directory_raises(self, tmp_path):
        with pytest.raises(RemediationError, match="not a git repository"):
            RemediationRunner(str(tmp_path))

    def test_push_branch_to_real_local_bare_remote(self, git_project, tmp_path_factory):
        project_path, repo = git_project
        bare_path = tmp_path_factory.mktemp("bare_remote")
        Repo.init(str(bare_path), bare=True)
        repo.create_remote("origin", str(bare_path))

        deps = [_dep("requests", "2.25.0", sources=["requirements.txt"])]
        vulns = [_vuln("requests", "2.31.0")]
        plan = build_remediation_plan(str(project_path), deps, vulns)

        runner = RemediationRunner(str(project_path))
        branch_name = runner.create_branch_and_commit(plan, branch_name="fix/requests")
        runner.push_branch(branch_name, remote_name="origin")

        bare_repo = Repo(str(bare_path))
        assert "fix/requests" in [h.name for h in bare_repo.heads]

    def test_push_branch_missing_remote_raises(self, git_project):
        project_path, repo = git_project
        deps = [_dep("requests", "2.25.0", sources=["requirements.txt"])]
        vulns = [_vuln("requests", "2.31.0")]
        plan = build_remediation_plan(str(project_path), deps, vulns)

        runner = RemediationRunner(str(project_path))
        branch_name = runner.create_branch_and_commit(plan, branch_name="fix/requests")

        with pytest.raises(RemediationError, match="no remote"):
            runner.push_branch(branch_name, remote_name="origin")

    def test_create_pull_request_returns_none_without_gh_cli(self, git_project, monkeypatch):
        project_path, repo = git_project
        monkeypatch.setattr("shutil.which", lambda _name: None)

        runner = RemediationRunner(str(project_path))
        result = runner.create_pull_request("fix/requests", "main", "title", "body")

        assert result is None

    def test_create_pull_request_invokes_real_gh_binary(self, git_project, tmp_path_factory, monkeypatch):
        """Exercises the actual subprocess call path against a fake `gh`
        executable on PATH (not a mock of subprocess.run) -- proves the
        argv construction and stdout parsing are correct for a real
        external-process integration."""
        project_path, repo = git_project

        fake_bin_dir = tmp_path_factory.mktemp("fake_bin")
        fake_gh = fake_bin_dir / "gh"
        fake_gh.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "assert sys.argv[1:4] == ['pr', 'create', '--head']\n"
            "print('https://github.com/example/repo/pull/42')\n"
        )
        fake_gh.chmod(0o755)
        monkeypatch.setenv("PATH", f"{fake_bin_dir}:{__import__('os').environ['PATH']}")

        runner = RemediationRunner(str(project_path))
        result = runner.create_pull_request("fix/requests", "main", "title", "body")

        assert result == "https://github.com/example/repo/pull/42"

    def test_create_pull_request_returns_none_when_gh_fails(self, git_project, tmp_path_factory, monkeypatch):
        project_path, repo = git_project

        fake_bin_dir = tmp_path_factory.mktemp("fake_bin")
        fake_gh = fake_bin_dir / "gh"
        fake_gh.write_text("#!/usr/bin/env python3\nimport sys\nsys.stderr.write('not authenticated')\nsys.exit(1)\n")
        fake_gh.chmod(0o755)
        monkeypatch.setenv("PATH", f"{fake_bin_dir}:{__import__('os').environ['PATH']}")

        runner = RemediationRunner(str(project_path))
        result = runner.create_pull_request("fix/requests", "main", "title", "body")

        assert result is None


class TestRemediateCliCommand:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_dry_run_prints_diff_and_does_not_write(self, runner, tmp_path, monkeypatch):
        (tmp_path / "requirements.txt").write_text("requests==2.25.0\n")

        monkeypatch.setattr(
            "pydependencycheck.cli.DependencyScanner.check_vulnerabilities",
            lambda self: [_vuln("requests", "2.31.0")],
        )

        result = runner.invoke(cli, ["remediate", "--path", str(tmp_path)])

        assert result.exit_code == 0, result.output
        assert "requests: 2.25.0 -> 2.31.0" in result.output
        assert "+requests==2.31.0" in result.output
        assert "Dry run" in result.output
        assert (tmp_path / "requirements.txt").read_text() == "requests==2.25.0\n"

    def test_apply_writes_real_file(self, runner, tmp_path, monkeypatch):
        (tmp_path / "requirements.txt").write_text("requests==2.25.0\n")

        monkeypatch.setattr(
            "pydependencycheck.cli.DependencyScanner.check_vulnerabilities",
            lambda self: [_vuln("requests", "2.31.0")],
        )

        result = runner.invoke(cli, ["remediate", "--path", str(tmp_path), "--apply"])

        assert result.exit_code == 0, result.output
        assert "Applied fixes to 1 file(s)" in result.output
        assert (tmp_path / "requirements.txt").read_text() == "requests==2.31.0\n"

    def test_no_vulnerabilities_reports_clean(self, runner, tmp_path, monkeypatch):
        (tmp_path / "requirements.txt").write_text("requests==2.31.0\n")

        monkeypatch.setattr(
            "pydependencycheck.cli.DependencyScanner.check_vulnerabilities",
            lambda self: [],
        )

        result = runner.invoke(cli, ["remediate", "--path", str(tmp_path)])

        assert result.exit_code == 0, result.output
        assert "No fixable vulnerabilities found" in result.output

    def test_pr_flow_creates_real_branch_and_commit(self, runner, tmp_path, monkeypatch):
        repo = Repo.init(tmp_path, initial_branch="main")
        with repo.config_writer() as cw:
            cw.set_value("user", "name", "Test User")
            cw.set_value("user", "email", "test@example.com")
        (tmp_path / "requirements.txt").write_text("requests==2.25.0\n")
        repo.index.add(["requirements.txt"])
        repo.index.commit("initial commit")

        bare_path = tmp_path.parent / f"{tmp_path.name}_bare.git"
        Repo.init(str(bare_path), bare=True)
        repo.create_remote("origin", str(bare_path))

        monkeypatch.setattr(
            "pydependencycheck.cli.DependencyScanner.check_vulnerabilities",
            lambda self: [_vuln("requests", "2.31.0", vuln_id="GHSA-abcd")],
        )
        monkeypatch.setattr("shutil.which", lambda _name: None)  # no gh CLI -> branch/push only

        result = runner.invoke(cli, ["remediate", "--path", str(tmp_path), "--pr", "--branch", "fix/requests"])

        assert result.exit_code == 0, result.output
        assert "Created branch 'fix/requests'" in result.output
        assert "Pushed 'fix/requests' to 'origin'" in result.output
        assert "gh` CLI not available" in result.output

        bare_repo = Repo(str(bare_path))
        assert "fix/requests" in [h.name for h in bare_repo.heads]
