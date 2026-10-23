"""PyDependencyCheck: Dependency Intelligence and Governance Platform"""

__version__ = "1.5.1"
__author__ = "Georgi Mammen Mullassery"
__email__ = "mullassery@gmail.com"
__license__ = "Apache-2.0"

try:
    from ._pydependencycheck import ast, graph, parser, security
except ImportError:
    # Rust extension not built yet
    ast = None
    parser = None
    graph = None
    security = None

__all__ = ["ast", "parser", "graph", "security"]
