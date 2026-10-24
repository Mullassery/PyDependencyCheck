"""Regression tests for ``GitIntegration.get_blame``'s line-number reporting.

``GitPython``'s ``Repo.blame()`` yields ``(commit, lines)`` per *contiguous
hunk*, not per file or per line, so a hunk's own length is not a line number.
The original code set ``info.line_no = len(lines)``, which was wrong for any
match outside the first hunk — and happened to be right only when the whole
file came from a single hunk, which is exactly the case a naive test would
exercise. These tests build a file with two hunks and assert the *absolute*
1-based line number of a match in the second hunk.
"""

from git import Actor, Repo
from pydependencycheck.git_integration import GitIntegration


def _commit_file(repo, path, content, message):
    path.write_text(content)
    repo.index.add([str(path.name)])
    actor = Actor("Test", "test@example.com")
    repo.index.commit(message, author=actor, committer=actor)


def _make_two_hunk_repo(tmp_path):
    repo = Repo.init(tmp_path)
    req = tmp_path / "requirements.txt"
    _commit_file(repo, req, "flask==2.0.0\n", "add flask")
    _commit_file(repo, req, "flask==2.0.0\ndjango==4.2\nnumpy==1.24\n", "add django+numpy")
    return repo


def test_blame_line_number_is_absolute_across_hunks(tmp_path):
    _make_two_hunk_repo(tmp_path)

    gi = GitIntegration(str(tmp_path))
    info = gi.get_blame("numpy", filename="requirements.txt")

    assert info.file == "requirements.txt"
    assert info.line_no == 3  # absolute 1-based line of "numpy==1.24"
    assert info.message == "add django+numpy"


def test_blame_line_number_first_hunk_still_correct(tmp_path):
    _make_two_hunk_repo(tmp_path)

    gi = GitIntegration(str(tmp_path))
    info = gi.get_blame("flask", filename="requirements.txt")

    assert info.line_no == 1
    assert info.message == "add flask"


def test_blame_second_line_of_second_hunk(tmp_path):
    _make_two_hunk_repo(tmp_path)

    gi = GitIntegration(str(tmp_path))
    info = gi.get_blame("django", filename="requirements.txt")

    assert info.line_no == 2


def test_non_git_directory_is_reported(tmp_path):
    gi = GitIntegration(str(tmp_path))
    assert gi.is_git_repo() is False
    assert gi.get_blame("flask").package == "flask"
    assert gi.get_history("flask") == []
    assert gi.get_commit_deps("HEAD") == {}


def test_history_records_version_changes(tmp_path):
    repo = _make_two_hunk_repo(tmp_path)
    _commit_file(repo, tmp_path / "requirements.txt", "flask==2.1.0\ndjango==4.2\nnumpy==1.24\n", "bump flask")

    gi = GitIntegration(str(tmp_path))
    history = gi.get_history("flask")

    assert [entry["version"] for entry in history] == ["2.1.0", "2.0.0", "2.0.0"]
    assert history[0]["message"] == "bump flask"
    assert history[0]["file"] == "requirements.txt"


def test_commit_deps_reads_every_dependency_file(tmp_path):
    repo = _make_two_hunk_repo(tmp_path)
    _commit_file(repo, tmp_path / "pyproject.toml", '[project]\ndependencies = ["rich>=13"]\n', "add pyproject")
    head = repo.head.commit.hexsha

    gi = GitIntegration(str(tmp_path))
    deps = gi.get_commit_deps(head)

    assert "requirements.txt" in deps
    assert deps["requirements.txt"] == ["flask", "django", "numpy"]
    assert isinstance(deps["pyproject.toml"], list)


def test_version_extraction_handles_operators(tmp_path):
    gi = GitIntegration(str(tmp_path))
    content = "\n".join(
        [
            "requests==2.32.0",
            "django>=4.2,<5",
            "numpy~=1.26.0",
            "flask[async]>=3.0 ; python_version >= '3.10'",
        ]
    )
    assert gi._extract_version("requests", content) == "2.32.0"
    assert gi._extract_version("django", content) == "4.2"
    assert gi._extract_version("numpy", content) == "1.26.0"
    assert gi._extract_version("flask", content) == "3.0"
    assert gi._extract_version("missing", content) is None


def test_parse_content_skips_comments_and_blank_lines(tmp_path):
    gi = GitIntegration(str(tmp_path))
    content = "# comment\n\nrequests==2.32.0\nflask[async]>=3.0\n"
    assert gi._parse_content(content) == ["requests", "flask"]
