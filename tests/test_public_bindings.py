import pydependencycheck


def test_native_ast_module_is_exported():
    assert hasattr(pydependencycheck.ast, "scan_imports")
    assert hasattr(pydependencycheck.ast, "find_dead_packages")
