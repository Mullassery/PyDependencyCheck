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
