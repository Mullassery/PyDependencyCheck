"""Guard against metadata drift in the package's dunder attributes.

Both bugs these tests cover shipped silently: ``__version__`` was hardcoded
and never bumped past 1.4.0 while ``pyproject.toml`` moved to 1.4.1, and
``__license__`` still said ``"Proprietary"`` long after the project
relicensed to Apache-2.0. Nothing asserted either value against its source
of truth, so both went unnoticed.

The version is checked against ``pyproject.toml`` (the source of truth) rather
than installed distribution metadata: a source checkout may have no wheel
installed, or a stale one, which made the old assertion fail for reasons that
had nothing to do with the code under test.
"""

from __future__ import annotations

from pathlib import Path

import pydependencycheck

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.8-3.10
    import tomli as tomllib

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _declared_version() -> str:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["project"]["version"]


def test_dunder_version_matches_pyproject():
    assert pydependencycheck.__version__ == _declared_version()


def test_dunder_license_is_apache_2_0():
    assert pydependencycheck.__license__ == "Apache-2.0"
