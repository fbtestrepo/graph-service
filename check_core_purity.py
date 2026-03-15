from __future__ import annotations

import ast
import sys
from pathlib import Path


FORBIDDEN_TOP_LEVEL_MODULES = {
    "fastapi",
    "starlette",
    "pymongo",
    "motor",
    "ldap3",
}


def iter_python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def find_forbidden_imports(py_file: Path) -> list[tuple[int, str]]:
    text = py_file.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(py_file))
    findings: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in FORBIDDEN_TOP_LEVEL_MODULES:
                    findings.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            top = node.module.split(".")[0]
            if top in FORBIDDEN_TOP_LEVEL_MODULES:
                findings.append((node.lineno, node.module))

    return findings


def main() -> int:
    core_root = Path("src/core")
    if not core_root.exists():
        print("Core root not found at src/core; nothing to check.")
        return 0

    violations: list[str] = []
    for py_file in iter_python_files(core_root):
        for lineno, module in find_forbidden_imports(py_file):
            violations.append(f"{py_file}:{lineno}: forbidden import '{module}'")

    if violations:
        print("Core purity violations detected:")
        for v in violations:
            print(f"- {v}")
        return 1

    print("Core purity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
