#!/usr/bin/env python3
"""
Project reconnaissance scanner — stdlib only.
Usage: python scan_project.py <project_root> [--json|--markdown]
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Directories to skip during walk
SKIP_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    "vendor",
    ".idea",
    ".vscode",
    "coverage",
    "htmlcov",
    ".eggs",
    "*.egg-info",
}

# Manifest files → ecosystem hints
MANIFESTS: dict[str, str] = {
    "package.json": "nodejs",
    "pnpm-lock.yaml": "nodejs-pnpm",
    "yarn.lock": "nodejs-yarn",
    "package-lock.json": "nodejs-npm",
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "Pipfile": "python-pipenv",
    "poetry.lock": "python-poetry",
    "uv.lock": "python-uv",
    "environment.yml": "conda",
    "setup.py": "python-setuptools",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "pom.xml": "java-maven",
    "build.gradle": "java-gradle",
    "build.gradle.kts": "kotlin-gradle",
    "Gemfile": "ruby",
    "composer.json": "php",
    "mix.exs": "elixir",
    "CMakeLists.txt": "cpp-cmake",
    "Makefile": "make",
    "docker-compose.yml": "docker-compose",
    "docker-compose.yaml": "docker-compose",
    "Dockerfile": "docker",
}

DOC_CANDIDATES = [
    "README.md",
    "README.MD",
    "readme.md",
    "README.rst",
    "README.txt",
    "README",
    "Readme.md",
]

CI_PATTERNS = [
    ".github/workflows",
    ".gitlab-ci.yml",
    "Jenkinsfile",
    "azure-pipelines.yml",
    ".circleci/config.yml",
    "bitbucket-pipelines.yml",
]

TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs", "testing"}
ENTRY_HINTS = [
    "main.py",
    "app.py",
    "manage.py",
    "wsgi.py",
    "asgi.py",
    "cli.py",
    "index.ts",
    "index.js",
    "main.go",
    "main.rs",
    "Application.java",
    "Program.cs",
]


def should_skip_dir(name: str) -> bool:
    if name in SKIP_DIRS:
        return True
    if name.endswith(".egg-info"):
        return True
    return False


def scan_tree(root: Path) -> dict[str, Any]:
    ext_counter: Counter[str] = Counter()
    dir_counter: Counter[str] = Counter()
    file_count = 0
    total_bytes = 0
    max_depth = 0
    largest_files: list[tuple[int, str]] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # prune
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        rel_dir = Path(dirpath).relative_to(root)
        depth = len(rel_dir.parts)
        max_depth = max(max_depth, depth)
        if rel_dir.parts:
            dir_counter[str(rel_dir.parts[0])] += 1

        for fn in filenames:
            file_count += 1
            fp = Path(dirpath) / fn
            try:
                size = fp.stat().st_size
            except OSError:
                size = 0
            total_bytes += size
            ext = fp.suffix.lower() or "(no ext)"
            ext_counter[ext] += 1
            if size > 50_000:
                largest_files.append((size, str(fp.relative_to(root))))

    largest_files.sort(reverse=True)
    top_ext = ext_counter.most_common(15)
    top_dirs = sorted(dir_counter.items(), key=lambda x: -x[1])[:20]

    return {
        "file_count": file_count,
        "total_size_mb": round(total_bytes / (1024 * 1024), 2),
        "max_depth": max_depth,
        "top_extensions": top_ext,
        "top_level_dirs": top_dirs,
        "largest_files": [
            {"path": p, "size_kb": round(s / 1024, 1)} for s, p in largest_files[:15]
        ],
    }


def find_manifests(root: Path) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    skip_glob = {"docker-compose.yml", "docker-compose.yaml", "Dockerfile"}

    for name, ecosystem in MANIFESTS.items():
        p = root / name
        if p.is_file():
            key = str(p.resolve())
            if key not in seen:
                seen.add(key)
                found.append({"file": name, "ecosystem": ecosystem, "path": str(p)})

    for pattern in ("docker-compose*.yml", "docker-compose*.yaml"):
        for p in root.glob(pattern):
            if p.name in skip_glob:
                continue
            key = str(p.resolve())
            if key not in seen:
                seen.add(key)
                found.append({"file": p.name, "ecosystem": "docker-compose", "path": str(p)})

    for p in root.glob("Dockerfile*"):
        if not p.is_file() or p.name == "Dockerfile":
            continue
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            found.append({"file": p.name, "ecosystem": "docker", "path": str(p)})

    return found


def find_readme(root: Path) -> list[str]:
    hits = []
    for name in DOC_CANDIDATES:
        p = root / name
        if p.is_file():
            hits.append(name)
    docs = root / "docs"
    if docs.is_dir():
        hits.append("docs/")
    return hits


def find_ci(root: Path) -> list[str]:
    hits = []
    for pattern in CI_PATTERNS:
        p = root / pattern
        if p.exists():
            hits.append(pattern)
    wf = root / ".github" / "workflows"
    if wf.is_dir():
        for f in wf.iterdir():
            if f.suffix in {".yml", ".yaml"}:
                hits.append(str(f.relative_to(root)))
    return sorted(set(hits))


def find_test_dirs(root: Path) -> list[str]:
    hits = []
    for child in root.iterdir():
        if child.is_dir() and child.name.lower() in TEST_DIR_NAMES:
            hits.append(child.name + "/")
    # nested common
    for name in TEST_DIR_NAMES:
        for p in root.rglob(name):
            if not p.is_dir() or any(should_skip_dir(part) for part in p.parts):
                continue
            rel = str(p.relative_to(root)) + "/"
            if rel not in hits and len(hits) < 10:
                hits.append(rel)
    return hits[:10]


def find_entry_hints(root: Path) -> list[str]:
    hits = []
    for name in ENTRY_HINTS:
        for p in root.rglob(name):
            if any(should_skip_dir(part) for part in p.parts):
                continue
            rel = str(p.relative_to(root))
            if rel not in hits:
                hits.append(rel)
            if len(hits) >= 20:
                return hits
    return hits


def detect_monorepo(root: Path) -> list[str]:
    signals = []
    checks = [
        "pnpm-workspace.yaml",
        "lerna.json",
        "nx.json",
        "go.work",
        "Cargo.toml",
        "turbo.json",
    ]
    for c in checks:
        if (root / c).is_file():
            signals.append(c)
    cargo = root / "Cargo.toml"
    if cargo.is_file():
        text = cargo.read_text(encoding="utf-8", errors="ignore")
        if "[workspace]" in text:
            signals.append("Cargo.toml [workspace]")
    pkg = root / "package.json"
    if pkg.is_file():
        text = pkg.read_text(encoding="utf-8", errors="ignore")
        if "workspaces" in text:
            signals.append("package.json workspaces")
    return signals


def git_summary(root: Path) -> dict[str, Any] | None:
    git_dir = root / ".git"
    if not git_dir.exists():
        return None
    return {
        "is_git_repo": True,
        "hint": "Run git log --oneline -10 for recent activity (Deep mode)",
    }


def scan(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    manifests = find_manifests(root)
    ecosystems = sorted({m["ecosystem"] for m in manifests})

    return {
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root.resolve()),
        "readme": find_readme(root),
        "manifests": manifests,
        "ecosystems": ecosystems,
        "monorepo_signals": detect_monorepo(root),
        "ci": find_ci(root),
        "test_dirs": find_test_dirs(root),
        "entry_hints": find_entry_hints(root),
        "tree": scan_tree(root),
        "git": git_summary(root),
        "env_examples": [
            str(p.relative_to(root))
            for p in root.rglob(".env.example")
            if not any(should_skip_dir(part) for part in p.parts)
        ][:5],
        "license_files": [
            name
            for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")
            if (root / name).is_file()
        ],
    }


def to_markdown(data: dict[str, Any]) -> str:
    lines = [
        f"# Scan: {data['project_root']}",
        f"Time: {data['scan_time']}",
        "",
        "## Ecosystems",
        ", ".join(data["ecosystems"]) or "(none detected)",
        "",
        "## README",
        ", ".join(data["readme"]) or "(not found)",
        "",
        "## Manifests",
    ]
    for m in data["manifests"]:
        lines.append(f"- {m['file']} ({m['ecosystem']})")
    lines.extend(["", "## CI", ", ".join(data["ci"]) or "(none)", "", "## Test dirs"])
    for t in data["test_dirs"]:
        lines.append(f"- {t}")
    lines.extend(["", "## Entry hints"])
    for e in data["entry_hints"][:10]:
        lines.append(f"- `{e}`")
    t = data["tree"]
    lines.extend(
        [
            "",
            "## Tree stats",
            f"- Files: {t['file_count']}",
            f"- Size: {t['total_size_mb']} MB",
            f"- Max depth: {t['max_depth']}",
            "",
            "## Top extensions",
        ]
    )
    for ext, cnt in t["top_extensions"]:
        lines.append(f"- `{ext}`: {cnt}")
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        raise SystemExit(2)

    root = Path(sys.argv[1]).resolve()
    fmt = "--markdown" if "--markdown" in sys.argv else "json"
    data = scan(root)

    if fmt == "markdown":
        print(to_markdown(data))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
