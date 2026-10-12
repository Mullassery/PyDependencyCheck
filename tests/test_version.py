"""Guard against metadata drift in the package's dunder attributes.

Both bugs these tests cover shipped silently: ``__version__`` was hardcoded
and never bumped past 1.4.0 while ``pyproject.toml`` moved to 1.4.1, and
``__license__`` still said ``"Proprietary"`` long after the project
relicensed to Apache-2.0. Nothing asserted either value against its source
of truth, so both went unnoticed.
"""

from importlib.metadata import version as dist_version

import pydependencycheck


def test_dunder_version_matches_installed_metadata():
    assert pydependencycheck.__version__ == dist_version("pydependencycheck")


def test_dunder_license_is_apache_2_0():
    assert pydependencycheck.__license__ == "Apache-2.0"
