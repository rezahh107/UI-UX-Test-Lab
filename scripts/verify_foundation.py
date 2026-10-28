#!/usr/bin/env python3
"""Check the foundation's real, bounded documentation and Git hygiene contract."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")
GENERATED_OR_PRIVATE = (
    ".env", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", "node_modules", "artifacts", "test-results",
    "playwright-report", "tmp",
)
IGNORE_PROBES = (
    ".env", ".env.local", ".venv/pyvenv.cfg", "__pycache__/cache.pyc",
    "node_modules/package/index.js", "artifacts/screenshot.png",
    "test-results/result.json", "playwright-report/index.html", "tmp/temp.txt",
)


def git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, check=False
    )


def check() -> list[str]:
    errors: list[str] = []
    tracked = git("ls-files", "-z")
    if tracked.returncode:
        return ["git ls-files failed: " + tracked.stderr.decode(errors="replace").strip()]

    files = [Path(p.decode("utf-8")) for p in tracked.stdout.split(b"\0") if p]
    for file in files:
        parts = file.parts
        if parts and (parts[0] in GENERATED_OR_PRIVATE or
                      (parts[0].startswith(".env.") and file.as_posix() != ".env.example")):
            errors.append(f"Tracked generated/private path: {file.as_posix()}")
        if file.suffix.lower() != ".md":
            continue
        try:
            content = (ROOT / file).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Cannot read {file}: {exc}")
            continue
        for match in LINK.finditer(content):
            dest = match.group(1).strip().split(maxsplit=1)[0].strip("<>")
            parsed = urlsplit(dest)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = ((ROOT / file).parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                line = content.count("\n", 0, match.start()) + 1
                errors.append(f"Broken local link: {file}:{line} -> {dest}")

    for probe in IGNORE_PROBES:
        if git("check-ignore", "-q", "--no-index", "--", probe).returncode != 0:
            errors.append(f"Missing .gitignore protection: {probe}")
    if git("check-ignore", "-q", "--no-index", "--", ".env.example").returncode == 0:
        errors.append(".env.example must remain trackable")
    return errors


def main() -> int:
    issues = check()
    if issues:
        for issue in issues:
            print("FAIL: " + issue, file=sys.stderr)
        return 1
    print("PASS: Foundation links and tracked/ignored path hygiene")
    return 0


if __name__ == "__main__":
    sys.exit(main())
