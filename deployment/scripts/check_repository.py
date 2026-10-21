"""Check maintained-folder documentation, public API docs and local package/link integrity.

Run from any directory with Python 3.11+. This is a structural documentation check,
not proof of factual accuracy, security, live-provider behavior or deployment health.
It never reads environment files, credentials or generated database/build outputs.
"""

from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path
from urllib.parse import unquote

EXCLUDED = {
    ".git",
    ".venv",
    ".ruff_cache",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    ".agentic",
    ".test-state",
}
SOURCE_PARENT = "src"
SOURCE_ROOTS = {"core", "contracts", "adapters", "services", "sdk"}


def in_source(relative: Path) -> bool:
    """True when a path is SDK source under src/, not an example or a document."""
    return (
        len(relative.parts) >= 2
        and relative.parts[0] == SOURCE_PARENT
        and relative.parts[1] in SOURCE_ROOTS
    )


def maintained(root: Path, path: Path) -> bool:
    """Exclude generated metadata, caches and private runtime state from the inventory."""
    return not any(
        part in EXCLUDED or part.endswith(".egg-info") for part in path.relative_to(root).parts
    )


def folders(root: Path) -> list[Path]:
    """Return every maintained directory, including repository and automation roots."""
    return [root] + sorted(
        path for path in root.rglob("*") if path.is_dir() and maintained(root, path)
    )


def public_definitions(tree: ast.Module):
    """Yield public top-level definitions and public methods; constructors use class docs."""
    for node in tree.body:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ) and not node.name.startswith("_"):
            yield node.name, node
            if isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(
                        method, (ast.FunctionDef, ast.AsyncFunctionDef)
                    ) and not method.name.startswith("_"):
                        yield node.name + "." + method.name, method


def check(root: Path) -> tuple[list[str], dict[str, int]]:
    """Collect structural violations without importing or executing repository code."""
    errors = []
    inventory = folders(root)
    for folder in inventory:
        if not (folder / "README.md").is_file():
            errors.append(f"{folder.relative_to(root)}: missing README.md")
    count = 0
    for path in root.rglob("*.py"):
        if not maintained(root, path) or not in_source(path.relative_to(root)):
            continue
        relative = path.relative_to(root)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            errors.append(f"{relative}: {exc}")
            continue
        if not ast.get_docstring(tree):
            errors.append(f"{relative}: missing module docstring")
        for name, node in public_definitions(tree):
            count += 1
            if not ast.get_docstring(node):
                errors.append(f"{relative}:{node.lineno}: undocumented {name}")
    for path in root.rglob("*.md"):
        if not maintained(root, path):
            continue
        text = path.read_text(encoding="utf-8")
        # Code snippets often contain illustrative paths rather than Markdown links.
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        for link in re.findall(r"\]\(([^)]+)\)", text):
            target = link.strip().strip("<>").split("#", 1)[0]
            if not target or ":" in target or target.startswith("//"):
                continue
            if not (path.parent / unquote(target)).exists():
                errors.append(f"{path.relative_to(root)}: missing link {target}")
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    mappings = project["tool"]["setuptools"]["package-dir"]
    for package, relative in mappings.items():
        if not (root / relative / "__init__.py").is_file():
            errors.append(f"{package}: missing mapped package {relative}")
    for folder in inventory:
        relative = folder.relative_to(root)
        if relative.parts and in_source(relative) and (folder / "__init__.py").exists():
            name = "agentic_sdk." + ".".join(relative.parts[1:])
            if mappings.get(name) != relative.as_posix():
                errors.append(f"{relative}: not present in package mapping")
    adr_ids = [path.name.split("-", 1)[0] for path in (root / "doc/adr").glob("[0-9]*.md")]
    if len(set(adr_ids)) != len(adr_ids):
        errors.append("doc/adr: duplicate decision IDs")
    return errors, {"folders": len(inventory), "public_definitions": count}


def main() -> None:
    """Print a compact report and fail CI when structural documentation has regressed."""
    root = Path(__file__).resolve().parents[2]
    errors, counts = check(root)
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print(
        f"PASS: {counts['folders']} maintained folders, {counts['public_definitions']} public definitions, local links, package mappings and ADR IDs."
    )


if __name__ == "__main__":
    main()
