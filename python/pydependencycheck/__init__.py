"""PyDependencyCheck: Dependency Intelligence and Governance Platform"""

__version__ = "0.1.0"
__author__ = "Georgi Mammen Mullassery"
__email__ = "mullassery@gmail.com"
__license__ = "MIT"

try:
    from ._pydependencycheck import parser, graph, security
except ImportError:
    # Rust extension not built yet
    parser = None
    graph = None
    security = None

__all__ = ["parser", "graph", "security"]
