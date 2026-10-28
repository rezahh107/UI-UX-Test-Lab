#!/usr/bin/env python3
"""Check the foundation's real, bounded documentation and Git hygiene contract."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")
IGNORE_PROBES = (
    ".env", ".env.local", "nested/.env.local", ".venv/pyvenv.cfg",
    "__pycache__/cache.pyc", "generated.pyc", "nested/generated.pyc",
    "node_modules/package/index.js", "artifacts/screenshot.png",
    "nested/artifacts/screenshot.png", "test-results/result.json",
    "playwright-report/index.html", "tmp/temp.txt",
)


def git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, check=False
    )


def ignored_by_repository(tracked: list[Path]) -> tuple[set[str], list[str]]:
    """Evaluate only tracked .gitignore files, not local or user Git excludes."""
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="foundation-ignore-") as directory:
        policy_root = Path(directory)
        initialized = subprocess.run(
            ["git", "init", "-q", "--template=", str(policy_root)],
            capture_output=True, check=False,
        )
        if initialized.returncode != 0:
            return set(), ["Cannot initialize Git ignore evaluation: " +
                           initialized.stderr.decode(errors="replace").strip()]

        for path in tracked:
            if path.name != ".gitignore":
                continue
            source = ROOT / path
            destination = policy_root / path
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            except OSError as exc:
                errors.append(f"Cannot read repository ignore policy {path}: {exc}")
        if errors:
            return set(), errors

        # The disposable Git directory has no .git/info/exclude. Override any
        # user/system core.excludesFile without modifying the user's settings.
        candidates = sorted({p.as_posix() for p in tracked} |
                            set(IGNORE_PROBES) | {".env.example", "nested/.env.example"})
        evaluated = subprocess.run(
            ["git", "-c", f"core.excludesFile={os.devnull}", "-C", str(policy_root),
             "check-ignore", "--no-index", "--stdin", "-z"],
            input=("\0".join(candidates) + "\0").encode("utf-8"),
            capture_output=True, check=False,
        )
        # Exit 1 means no matching ignored paths; every other nonzero exit is
        # an evaluation failure. Without --verbose, negation matches are absent.
        if evaluated.returncode not in (0, 1):
            return set(), ["Git ignore evaluation failed: " +
                           evaluated.stderr.decode(errors="replace").strip()]
        ignored = {p.decode("utf-8") for p in evaluated.stdout.split(b"\0") if p}
        if (evaluated.returncode == 1 and ignored) or not ignored <= set(candidates):
            return set(), ["Git ignore evaluation returned inconsistent results"]
        return ignored, []


def check() -> list[str]:
    errors: list[str] = []
    tracked = git("ls-files", "-z")
    if tracked.returncode:
        return ["git ls-files failed: " + tracked.stderr.decode(errors="replace").strip()]

    files = [Path(p.decode("utf-8")) for p in tracked.stdout.split(b"\0") if p]
    ignored, policy_errors = ignored_by_repository(files)
    errors.extend(policy_errors)
    if not policy_errors:
        for file in files:
            if file.as_posix() in ignored:
                errors.append(f"Tracked path ignored by repository .gitignore: {file.as_posix()}")
        for probe in IGNORE_PROBES:
            if probe not in ignored:
                errors.append(f"Missing .gitignore protection: {probe}")
        for exception in (".env.example", "nested/.env.example"):
            if exception in ignored:
                errors.append(f"Legitimate exception must remain trackable: {exception}")

    for file in files:
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
