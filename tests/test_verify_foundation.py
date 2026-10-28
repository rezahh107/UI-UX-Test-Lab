"""Real-Git regression tests for the foundation hygiene verifier."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
GIT_EXECUTABLE = shutil.which("git")


class FoundationVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="foundation-regression-")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        for relative in (".gitignore", "scripts/verify_foundation.py"):
            target = self.repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / relative, target)
        self.write("README.md", "# Example\n[existing](docs/ok.md)\n")
        self.write("docs/ok.md", "# Exists\n")
        self.write("scripts/regular.py", "print('safe')\n")
        self.git("add", ".")

    def git(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [GIT_EXECUTABLE, "-C", str(self.repo), *args],
            check=True, capture_output=True,
        )

    def write(self, relative: str, content: str = "x\n") -> None:
        target = self.repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def run_verifier(self, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.repo / "scripts/verify_foundation.py")],
            cwd=self.repo, capture_output=True, text=True, env=env,
        )

    def assert_rejected(self, relative: str) -> None:
        self.write(relative)
        self.git("add", "-f", relative)
        result = self.run_verifier()
        self.assertNotEqual(result.returncode, 0, relative)
        self.assertIn("Tracked path ignored by repository .gitignore: " + relative,
                      result.stderr)

    def test_ordinary_tracked_files_and_negation_exceptions_pass(self) -> None:
        self.write(".env.example")
        self.write("nested/.env.example")
        self.git("add", ".env.example", "nested/.env.example")
        result = self.run_verifier()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS:", result.stdout)

    def test_root_secret_is_rejected(self) -> None:
        self.assert_rejected(".env.local")

    def test_nested_secret_is_rejected(self) -> None:
        self.assert_rejected("nested/.env.local")

    def test_root_generated_directory_is_rejected(self) -> None:
        self.assert_rejected("artifacts/screenshot.png")

    def test_nested_generated_directory_is_rejected(self) -> None:
        self.assert_rejected("nested/artifacts/screenshot.png")

    def test_root_glob_generated_file_is_rejected(self) -> None:
        self.assert_rejected("generated.pyc")

    def test_nested_glob_generated_file_is_rejected(self) -> None:
        self.assert_rejected("nested/generated.pyc")

    def test_other_nested_generated_directories_are_rejected(self) -> None:
        for relative in ("nested/__pycache__/module.pyc", "nested/test-results/report.json"):
            with self.subTest(relative=relative):
                self.assert_rejected(relative)
                self.git("rm", "-q", "--cached", relative)

    def test_tracked_nested_gitignore_is_applied(self) -> None:
        self.write("nested/.gitignore", "*.scratch\n")
        self.git("add", "nested/.gitignore")
        self.assert_rejected("nested/generated.scratch")

    def test_untracked_gitignore_is_not_authority(self) -> None:
        self.write("nested/.gitignore", "*.md\n")  # deliberately NOT tracked
        self.write("nested/ordinary.md", "# Normal\n")
        self.git("add", "-f", "nested/ordinary.md")
        result = self.run_verifier()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_global_and_info_excludes_are_not_authority(self) -> None:
        global_ignore = Path(self.temporary.name) / "global-ignore"
        global_ignore.write_text("*.md\n*.py\n", encoding="utf-8")
        global_config = Path(self.temporary.name) / "global-config"
        global_config.write_text(
            "[core]\n\texcludesFile = " + global_ignore.as_posix() + "\n",
            encoding="utf-8",
        )
        info_exclude = self.repo / ".git/info/exclude"
        info_exclude.write_text("*.md\n*.py\n", encoding="utf-8")
        env = dict(os.environ, GIT_CONFIG_GLOBAL=str(global_config))
        result = self.run_verifier(env)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_broken_local_link_is_still_rejected(self) -> None:
        self.write("README.md", "# Example\n[broken](does-not-exist.md)\n")
        result = self.run_verifier()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Broken local link:", result.stderr)

    def test_missing_required_ignore_protection_is_rejected(self) -> None:
        ignore = self.repo / ".gitignore"
        ignore.write_text(ignore.read_text().replace("*.py[cod]\n", ""))
        result = self.run_verifier()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing .gitignore protection: generated.pyc", result.stderr)

    @unittest.skipIf(os.name == "nt", "PATH-based executable shim uses POSIX shebang")
    def test_git_ignore_evaluation_failure_is_not_a_pass(self) -> None:
        shim_directory = Path(self.temporary.name) / "shim"
        shim_directory.mkdir()
        shim = shim_directory / "git"
        shim.write_text(
            "#!/bin/sh\ncase \" $* \" in\n"
            "  *\" check-ignore \"*) echo 'simulated Git failure' >&2; exit 128;;\n"
            "esac\nexec \"" + GIT_EXECUTABLE + "\" \"$@\"\n",
            encoding="utf-8",
        )
        shim.chmod(0o755)
        env = dict(os.environ, PATH=str(shim_directory) + os.pathsep + os.environ["PATH"])
        result = self.run_verifier(env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Git ignore evaluation failed: simulated Git failure", result.stderr)


if __name__ == "__main__":
    unittest.main()
