"""No release may carry a stale MicroHealth FIPS image (owner's order, 2026-10-22).

* scripts/fips_bump.py finds every microhealthllc/fips-* pin in the tracked
  files, moves it to its tag's current digest, and with --check exits 1 on a
  stale OR unresolvable pin (tested offline with --from-file);
* fips-base-images.yml runs on fips-container's dispatch and weekly, opens ONE
  pull request into integration and merges it at once with GH_PAT, and fails
  red when it cannot;
* ci.yml checks the pins before anything else on pushes to integration and
  main and on pull requests into main; release.yml before any tag;
* main receives integration only: a pull request into main must come from
  this repository's integration, and every commit pushed to main must already
  be on integration (scripts/require-from-integration.sh).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
REG = "295669632222.dkr.ecr.us-east-1.amazonaws.com/microhealthllc"
OLD, NEW, OTHER = "sha256:" + "1" * 64, "sha256:" + "2" * 64, "sha256:" + "3" * 64


def load(name: str) -> dict:
    return yaml.load((WORKFLOWS / name).read_text(), Loader=yaml.BaseLoader)


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd,
                          check=True, capture_output=True, text=True).stdout


class BumpScriptTests(unittest.TestCase):
    def repo(self, digests: dict[str, str]) -> tuple[Path, Path]:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        work = tmp / "work"
        work.mkdir()
        git("init", "-q", cwd=work)
        (work / "fips-images.json").write_text(json.dumps({
            "python": f"{REG}/fips-python:dev-latest@{OLD}",
            "go": f"{REG}/fips-go:dev-latest@{NEW}",
        }, indent=2) + "\n")
        (work / "build.sh").write_text(f"FROM {REG}/fips-python:dev-latest@{OLD}\n")
        (work / "tests").mkdir()
        (work / "tests" / "fixture.json").write_text(f'"{REG}/fips-python:dev-latest@{OLD}"\n')
        (work / "other.yml").write_text(f"image: {REG}/tueri-api:dev-latest@{OLD}\n")
        (work / "untracked.sh").write_text(f"{REG}/fips-python:dev-latest@{OLD}\n")
        git("add", "fips-images.json", "build.sh", "tests", "other.yml", cwd=work)
        git("commit", "-qm", "base", cwd=work)
        table = tmp / "digests.json"
        table.write_text(json.dumps(digests))
        return work, table

    def bump(self, work: Path, table: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["python3", str(ROOT / "scripts" / "fips_bump.py"), "--root", str(work),
                               "--from-file", str(table), *args], capture_output=True, text=True)

    def test_rewrites_every_stale_pin_in_tracked_files_only(self) -> None:
        work, table = self.repo({"fips-python:dev-latest": NEW, "fips-go:dev-latest": NEW})
        summary = work.parent / "bump.md"
        res = self.bump(work, table, "--summary", str(summary))
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        images = json.loads((work / "fips-images.json").read_text())
        self.assertEqual(images["python"], f"{REG}/fips-python:dev-latest@{NEW}")
        self.assertEqual(images["go"], f"{REG}/fips-go:dev-latest@{NEW}")
        self.assertIn(NEW, (work / "build.sh").read_text())
        # Not pins: test fixtures, non-FIPS images, untracked files.
        self.assertIn(OLD, (work / "tests" / "fixture.json").read_text())
        self.assertIn(OLD, (work / "other.yml").read_text())
        self.assertIn(OLD, (work / "untracked.sh").read_text())
        self.assertIn("| `fips-python:dev-latest` | `111111111111` | `222222222222` |", summary.read_text())
        self.assertEqual(self.bump(work, table, "--check").returncode, 0)

    def test_check_fails_on_a_stale_pin_and_writes_nothing(self) -> None:
        work, table = self.repo({"fips-python:dev-latest": NEW, "fips-go:dev-latest": NEW})
        before = (work / "fips-images.json").read_text()
        res = self.bump(work, table, "--check")
        self.assertEqual(res.returncode, 1)
        self.assertIn("::error title=Stale FIPS image pin::fips-python:dev-latest is stale", res.stdout)
        self.assertIn("the FIPS bump is pending — wait for fips-base-images.yml to merge (or dispatch it), "
                      "then promote integration again.", res.stdout)
        self.assertEqual((work / "fips-images.json").read_text(), before)
        self.assertEqual(git("status", "--porcelain", cwd=work).strip(), "?? untracked.sh")

    def test_check_fails_on_an_unresolvable_pin(self) -> None:
        work, table = self.repo({"fips-python:dev-latest": OLD})  # fips-go cannot be resolved
        res = self.bump(work, table, "--check")
        self.assertEqual(res.returncode, 1)
        self.assertIn("fips-go:dev-latest is unresolvable", res.stdout)
        (table).write_text(json.dumps({"fips-python:dev-latest": OLD, "fips-go:dev-latest": "None"}))
        self.assertEqual(self.bump(work, table, "--check").returncode, 1)

    def test_bump_keeps_an_unresolvable_pin_and_moves_the_rest(self) -> None:
        work, table = self.repo({"fips-python:dev-latest": OTHER})
        res = self.bump(work, table)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        images = json.loads((work / "fips-images.json").read_text())
        self.assertTrue(images["python"].endswith(OTHER))
        self.assertTrue(images["go"].endswith(NEW))
        self.assertIn("Not resolvable in ECR (pin left as is): `fips-go:dev-latest`", res.stdout)

    def test_nothing_resolvable_is_an_error(self) -> None:
        work, table = self.repo({})
        self.assertEqual(self.bump(work, table).returncode, 1)

    def test_this_repository_has_pins_to_check(self) -> None:
        # fips-images.json is found by the tracked-file scan (the check would
        # otherwise pass on nothing).
        images = json.loads((ROOT / "fips-images.json").read_text())
        table = {f"fips-{k}:dev-latest": v.rsplit("@", 1)[1] for k, v in images.items() if k != "comment"}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(table, f)
        self.addCleanup(Path(f.name).unlink)
        res = subprocess.run(["python3", str(ROOT / "scripts" / "fips_bump.py"), "--check", "--from-file", f.name],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn(f"{len(table)} image tag(s), 0 stale pin(s)", res.stdout)


class BumpWorkflowTests(unittest.TestCase):
    def test_dispatched_and_weekly_and_one_grouped_pr_into_integration(self) -> None:
        wf = load("fips-base-images.yml")
        self.assertIn("workflow_dispatch", wf["on"])
        self.assertTrue(wf["on"]["schedule"][0]["cron"])
        (job,) = wf["jobs"].values()
        self.assertEqual(job["permissions"].get("id-token"), "write")
        text = json.dumps(job)
        self.assertIn("secrets.AWS_ROLE", text)
        self.assertIn("scripts/ci-run.sh python3 scripts/fips_bump.py", text)
        checkout = next(s for s in job["steps"] if s.get("uses", "").startswith("actions/checkout@"))
        self.assertEqual(checkout["with"]["ref"], "integration")
        self.assertEqual(checkout["with"]["token"], "${{ secrets.GH_PAT }}")
        self.assertEqual(wf["env"]["BRANCH"], "deps/fips-base-images")
        # upstream.yml no longer opens a second, unmerged FIPS pull request.
        up = load("upstream.yml")
        self.assertNotIn("fips", up["jobs"]["update"]["strategy"]["matrix"]["kind"])
        self.assertNotIn("fips_bump", (WORKFLOWS / "upstream.yml").read_text())

    def run_merge_step(self, merge_ok: bool) -> tuple[subprocess.CompletedProcess, str]:
        (job,) = load("fips-base-images.yml")["jobs"].values()
        step = next(s for s in job["steps"] if s.get("name", "").startswith("Open or refresh"))
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        work = tmp / "work"
        git("init", "-q", "--bare", str(tmp / "origin.git"), cwd=tmp)
        git("init", "-q", "-b", "integration", str(work), cwd=tmp)
        (work / "fips-images.json").write_text("{}\n")
        git("add", ".", cwd=work)
        git("commit", "-qm", "base", cwd=work)
        git("remote", "add", "origin", str(tmp / "origin.git"), cwd=work)
        (work / "fips-images.json").write_text('{"go": "new"}\n')
        (tmp / "bin").mkdir()
        state = "MERGED" if merge_ok else "OPEN"
        (tmp / "bin" / "gh").write_text(f"""#!/bin/sh
echo "$*" >> {tmp}/gh.log
case "$*" in
  "pr view deps/fips-base-images --repo o/r --json state --jq .state") exit 1 ;;
  "pr view deps/fips-base-images --repo o/r --json number,state"*) echo 7 ;;
  "pr view 7"*) echo {state} ;;
  "pr merge"*) {"exit 0" if merge_ok else "exit 1"} ;;
esac
""")
        (tmp / "bin" / "sleep").write_text("#!/bin/sh\n")
        for b in ("gh", "sleep"):
            (tmp / "bin" / b).chmod(0o755)
        (tmp / "bump.md").write_text("| table |\n")
        env = {"PATH": f"{tmp}/bin:/usr/bin:/bin", "HOME": str(tmp), "RUNNER_TEMP": str(tmp),
               "GITHUB_STEP_SUMMARY": str(tmp / "summary.md"), "GITHUB_REPOSITORY": "o/r",
               "BRANCH": "deps/fips-base-images", "GIT_CONFIG_NOSYSTEM": "1"}
        res = subprocess.run(["bash", "-e", "-c", step["run"]], cwd=work, env=env, capture_output=True, text=True)
        return res, (tmp / "gh.log").read_text()

    def test_merges_the_pull_request_at_once(self) -> None:
        res, log = self.run_merge_step(True)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("pr create --repo o/r --base integration --head deps/fips-base-images", log)
        self.assertIn("pr merge 7 --repo o/r --merge --admin --delete-branch", log)

    def test_a_merge_that_fails_turns_the_run_red(self) -> None:
        res, log = self.run_merge_step(False)
        self.assertNotEqual(res.returncode, 0)
        self.assertEqual(log.count("pr merge 7"), 6)  # brief retries, then red
        self.assertIn("could not merge the FIPS bump pull request #7", res.stdout)


class FreshnessGateTests(unittest.TestCase):
    def test_ci_checks_the_pins_before_anything_else(self) -> None:
        ci = load("ci.yml")
        job = ci["jobs"]["fips-fresh"]
        self.assertEqual(job["permissions"].get("id-token"), "write")
        self.assertNotIn("needs", job)
        text = json.dumps(job)
        self.assertIn("scripts/ci-run.sh python3 scripts/fips_bump.py --check", text)
        self.assertIn("secrets.AWS_ROLE", text)
        # Skipped only for pull requests that do not target main.
        scope = job["steps"][0]["run"]
        self.assertIn('[ "$GITHUB_EVENT_NAME" = pull_request ] && [ "$BASE_REF" != main ]', scope)
        self.assertEqual(set(ci["on"]["push"]["branches"]), {"main", "integration"})
        # A stale pin starts the bump itself.
        heal = job["steps"][-1]
        self.assertIn("failure()", heal["if"])
        self.assertIn("gh workflow run fips-base-images.yml", heal["run"])
        self.assertIn("--ref integration", heal["run"])
        self.assertEqual(job["permissions"].get("actions"), "write")
        # Everything else waits for it: changes gates build, self-scan and promote-main.
        self.assertIn("fips-fresh", ci["jobs"]["changes"]["needs"])
        for name in ("build", "self-scan", "promote-main"):
            self.assertIn("changes", ci["jobs"][name]["needs"], name)

    def test_release_checks_the_pins_before_tagging(self) -> None:
        rel = load("release.yml")
        self.assertEqual(rel["jobs"]["release"]["needs"], "fips-fresh")
        self.assertIn("scripts/fips_bump.py --check", json.dumps(rel["jobs"]["fips-fresh"]))
        self.assertIn("fips-images.json", rel["on"]["push"]["paths"])


class MainGuardTests(unittest.TestCase):
    def test_ci_refuses_main_from_anything_but_integration(self) -> None:
        ci = load("ci.yml")
        job = ci["jobs"]["main-from-integration"]
        self.assertIn("main-from-integration", ci["jobs"]["changes"]["needs"])
        pr = job["steps"][0]
        self.assertEqual(pr["if"], "github.event_name == 'pull_request' && github.base_ref == 'main'")
        self.assertEqual(pr["env"]["HEAD_REPO"], "${{ github.event.pull_request.head.repo.full_name }}")
        self.assertIn('[ "$HEAD_REPO" != "$GITHUB_REPOSITORY" ] || [ "$HEAD_REF" != integration ]', pr["run"])
        push = job["steps"][-1]
        self.assertEqual(push["if"], "github.event_name == 'push' && github.ref == 'refs/heads/main'")
        self.assertEqual(push["run"], "scripts/require-from-integration.sh")
        self.assertEqual(push["env"]["HEAD_SHA"], "${{ github.sha }}")

    def test_require_from_integration(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        origin, work = tmp / "origin.git", tmp / "work"
        git("init", "-q", "--bare", str(origin), cwd=tmp)
        git("init", "-q", "-b", "integration", str(work), cwd=tmp)
        git("remote", "add", "origin", str(origin), cwd=work)
        git("commit", "-q", "--allow-empty", "-m", "base", cwd=work)
        git("branch", "main", cwd=work)
        git("commit", "-q", "--allow-empty", "-m", "feature", cwd=work)
        git("push", "-q", "origin", "integration", cwd=work)
        git("checkout", "-q", "main", cwd=work)
        git("merge", "-q", "--no-ff", "-m", "Promote integration to main", "integration", cwd=work)
        script = str(ROOT / "scripts" / "require-from-integration.sh")
        ok = subprocess.run([script], cwd=work, capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)  # merge commits only
        git("commit", "-q", "--allow-empty", "-m", "hotfix straight to main", cwd=work)
        bad = subprocess.run([script], cwd=work, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertIn("hotfix straight to main", bad.stdout)
        self.assertIn("::error::main may only receive commits that are already on integration", bad.stdout)


if __name__ == "__main__":
    unittest.main()
