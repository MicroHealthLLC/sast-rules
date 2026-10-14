"""scripts/git-view.sh copies exactly what git sees, and survives what is not a file.

A local scan (scripts/scan-local.sh) reads this copy, so a failure here is a
local scan that never runs. It used to exit 123 with no message in any
repository tracking a symlink to a directory, a submodule or an unstaged
deletion, which every `pnpm verify` of such a repository then reported as a
failed scan.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "git-view.sh"


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                   cwd=cwd, check=True, capture_output=True)


def files(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() or p.is_symlink()}


class GitViewTests(unittest.TestCase):
    def test_copies_what_git_sees_and_skips_what_is_not_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src, dest = Path(tmp, "src"), Path(tmp, "dest")
            src.mkdir(), dest.mkdir()
            git(src, "init", "-q")
            (src / "skills" / "one").mkdir(parents=True)
            (src / "skills" / "one" / "SKILL.md").write_text("x\n")
            (src / "app.ts").write_text("export {};\n")
            (src / "gone.ts").write_text("export {};\n")
            (src / ".gitignore").write_text("build/\n")
            # A tracked symlink to a directory: `[ -f ]` is false for it.
            os.symlink("skills/one", src / "linked-skill")
            git(src, "add", "-A")
            git(src, "commit", "-q", "-m", "fixture")
            # A deletion not yet staged: still in the index, absent on disk.
            (src / "gone.ts").unlink()
            (src / "new.ts").write_text("export {};\n")
            (src / "build").mkdir()
            (src / "build" / "out.js").write_text("ignored\n")
            (src / ".sastignore").write_text("vendor/\n")

            run = subprocess.run([str(SCRIPT), str(src), str(dest)], capture_output=True, text=True)

            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(
                files(dest),
                {".gitignore", ".sastignore", "app.ts", "new.ts", "skills/one/SKILL.md"},
            )


if __name__ == "__main__":
    unittest.main()
