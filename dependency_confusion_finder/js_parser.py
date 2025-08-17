"""
JavaScript parser utilities using esprima (Python port).
Parses a JavaScript file and extracts imported/required package specifiers.
"""
import esprima
from typing import List, Set, Any
from .utils import looks_like_package, get_base_package_name

def extract_packages_from_js(source_code: str) -> List[str]:
    """
    Parse JS source and return a deduplicated list of package names referenced.
    Only returns external package names (excludes relative imports and core modules).
    """
    packages: Set[str] = set()
    try:
        tree = esprima.parseModule(source_code, {"tolerant": True, "jsx": True})
    except Exception:
        tree = esprima.parseScript(source_code, {"tolerant": True, "jsx": True})

    def walk(node: Any):
        if node is None:
            return
        if isinstance(node, list):
            for n in node:
                walk(n)
            return
        nodetype = getattr(node, "type", None)
        if nodetype == "ImportDeclaration":
            spec = getattr(node.source, "value", None)
            if spec and looks_like_package(spec):
                packages.add(get_base_package_name(spec))
        elif nodetype == "CallExpression":
            callee = getattr(node, "callee", None)
            if callee:
                callee_name = getattr(callee, "name", None)
                if callee_name in ("require",):
                    args = getattr(node, "arguments", []) or []
                    if args:
                        first = args[0]
                        val = getattr(first, "value", None)
                        if val and looks_like_package(val):
                            packages.add(get_base_package_name(val))
        # Recursively inspect properties for AST nodes
        for prop in dir(node):
            if prop.startswith("_"):
                continue
            try:
                child = getattr(node, prop)
            except Exception:
                continue
            if isinstance(child, (list, dict)) or hasattr(child, "type"):
                walk(child)

    # start walking from program body if available
    body = getattr(tree, "body", tree)
    walk(body)
    return sorted(packages)
