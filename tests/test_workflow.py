"""The shared workflow keeps the controls every caller relies on.

Callers (each MicroHealth repository's sast.yml) only pin this workflow; what
the scan guarantees is decided here, so it is tested here:

* the scan is a blocking step; a SARIF upload failure is not (GitHub code
  scanning may be unavailable), and both outcomes are recorded under always();
* the scan runs with --network none, and its text output is not printed;
* the bundle is checked against dist/SHA256SUMS and the engine against
  engine.json before anything runs;
* rule ids are reported as published (--no-rewrite-rule-ids);
* every action is pinned to a commit with a version comment, every job's
  permissions are explicit, and nothing runs on pull_request_target;
* every image is built FROM a FIPS base pinned by digest in fips-images.json,
  never written into a workflow (upstream.yml's daily bump pushes with an
  Actions token, which GitHub refuses for .github/workflows/);
* without GH_PAT, upstream.yml pushes its update branch and says where to
  open the pull request, instead of failing on one the Actions token may not
  create.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
PIN = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)(?:\s+#\s*(.*))?$")


def load(name: str) -> dict:
    return yaml.load((WORKFLOWS / name).read_text(), Loader=yaml.BaseLoader)


def steps(name: str) -> dict[str, dict]:
    (job,) = load(name)["jobs"].values()
    return {s.get("id") or s.get("name"): s for s in job["steps"]}


class SharedWorkflowTests(unittest.TestCase):
    def test_scan_blocks_and_publication_does_not(self) -> None:
        s = steps("opengrep.yml")
        self.assertNotIn("continue-on-error", s["scan"])
        self.assertEqual(s["sarif_publication"].get("continue-on-error"), "true")
        self.assertIn("always()", s["sarif_publication"]["if"])
        self.assertIn("always()", s["publication_status"]["if"])
        env = str(s["publication_status"]["env"])
        self.assertIn("steps.scan.outcome", env)
        self.assertIn("steps.sarif_publication.outcome", env)

    def test_code_scanning_gets_no_inline_suppressions(self) -> None:
        # GitHub opens an alert for a SARIF result marked suppressed, so a
        # reviewed noopengrep failed the pull request that added it.
        s = steps("opengrep.yml")
        filt = s["sarif_for_github"]
        self.assertIn("sarif_for_code_scanning.py /out/sast.sarif /out/sast.github.sarif", filt["run"])
        self.assertIn("--network none", filt["run"])
        self.assertTrue(s["sarif_publication"]["with"]["sarif_file"].endswith("/out/sast.github.sarif"))
        self.assertIn("steps.sarif_for_github.outcome", s["sarif_publication"]["if"])
        # The artifact is still the full report, suppressed results included.
        self.assertIn("/out/sast.sarif", s["Upload report artifacts"]["with"]["path"])

    def test_scan_has_no_network_and_prints_no_source(self) -> None:
        run = steps("opengrep.yml")["scan"]["run"]
        self.assertIn("--network none", run)
        self.assertIn("--no-rewrite-rule-ids", run)
        self.assertIn(">/dev/null", run)

    def test_rules_and_engine_are_verified_before_use(self) -> None:
        run = steps("opengrep.yml")["engine"]["run"]
        self.assertIn("SHA256SUMS", run)
        self.assertIn("sha256sum -c", run)
        self.assertIn("engine.json", run)

    def test_every_scanner_is_on_by_default(self) -> None:
        inputs = load("security-scan.yml")["on"]["workflow_call"]["inputs"]
        for toggle in ("sast", "trivy", "sbom", "zap"):
            self.assertEqual(inputs[toggle]["default"], "true", toggle)
        jobs = load("security-scan.yml")["jobs"]
        self.assertEqual(jobs["report"]["needs"], ["sast", "trivy", "zap"])
        self.assertEqual(jobs["report"]["if"], "always()")
        for name in ("sast", "trivy", "zap"):
            self.assertTrue(jobs[name]["uses"].startswith("./.github/workflows/"), name)

    def test_no_partial_scan_feeds_ingest(self) -> None:
        dest = (WORKFLOWS.parent.parent / "scripts" / "destination.sh").read_text()
        self.assertIn("pull_request", dest)
        self.assertIn("_branch-scans/branch=", dest)
        for name in ("trivy.yml", "zap.yml", "security-scan.yml"):
            self.assertIn("steps.dest.outputs.upload == 'true'", (WORKFLOWS / name).read_text(), name)

    def test_actions_are_pinned_and_permissions_explicit(self) -> None:
        for path in WORKFLOWS.glob("*.yml"):
            text = path.read_text()
            self.assertNotIn("pull_request_target", text, path.name)
            for line in text.splitlines():
                m = PIN.match(line)
                if not m or m.group(1).startswith("./"):
                    continue
                self.assertRegex(m.group(1), r"@[0-9a-f]{40}$", f"{path.name}: {line.strip()}")
                self.assertTrue(m.group(2) and re.search(r"v\d", m.group(2)), line.strip())
            wf = yaml.load(text, Loader=yaml.BaseLoader)
            self.assertEqual(wf.get("permissions"), {"contents": "read"}, path.name)
            for name, job in wf["jobs"].items():
                self.assertIsInstance(job.get("permissions"), dict, f"{path.name}:{name}")
                for step in job.get("steps") or []:
                    run = step.get("run", "")
                    if "docker build" not in run:
                        continue
                    froms = [ln.strip() for ln in run.splitlines() if ln.strip().startswith("FROM ")]
                    # `FROM scratch` only exports files from a FIPS stage
                    # (engines.yml); nothing runs in it.
                    for line in froms:
                        self.assertIn(line, ("FROM ${BASE}", "FROM ${BASE} AS build", "FROM scratch"), path.name)
                    self.assertRegex(run, r'base="\$\((\.sast-rules/)?scripts/fips-image\.sh (python|go)\)"', path.name)
                    self.assertEqual(run.count("docker build"), run.count('--build-arg BASE="$base"'), path.name)
                    self.assertEqual(run.count("docker build"), run.count("ARG BASE\n"), path.name)

    def test_no_fips_pin_is_written_into_a_workflow(self) -> None:
        for path in WORKFLOWS.glob("*.yml"):
            self.assertNotRegex(path.read_text(), r"microhealthllc/fips-[a-z0-9-]+:", path.name)
        up = (WORKFLOWS / "upstream.yml").read_text()
        self.assertIn("grep -q '^\\.github/workflows/'", up)
        bump = (ROOT / "scripts" / "fips_bump.py").read_text()
        self.assertIn('ROOT / "fips-images.json"', bump)
        self.assertNotIn("rglob", bump)

    def run_upstream_pr_step(self, have_pat: str, pr_state: str) -> tuple[subprocess.CompletedProcess, str, str]:
        """Run upstream.yml's pull-request step in a scratch clone with a fake gh."""
        step = steps("upstream.yml")["Open or refresh the pull request"]
        script = step["run"].replace("${{ matrix.kind }}", "engine")
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        git = lambda *a, cwd=tmp / "work": subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)
        git("init", "-q", "--bare", str(tmp / "origin.git"), cwd=tmp)
        git("init", "-q", "-b", "integration", str(tmp / "work"), cwd=tmp)
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "base")
        git("remote", "add", "origin", str(tmp / "origin.git"))
        (tmp / "work" / "engine.json").write_text("{}\n")
        (tmp / "bin").mkdir()
        gh = tmp / "bin" / "gh"
        gh.write_text(f"""#!/bin/sh
echo "$*" >> {tmp}/gh.log
case "$1 $2" in
  "pr view") [ -n "{pr_state}" ] && echo "{pr_state}" ;;
  "pr create") echo "GraphQL: GitHub Actions is not permitted to create or approve pull requests" >&2; exit 1 ;;
esac
""")
        gh.chmod(0o755)
        (tmp / "body.md").write_text("Opengrep 1.31.0\n")
        (tmp / "summary.md").touch()
        env = {"PATH": f"{tmp}/bin:/usr/bin:/bin", "HOME": str(tmp), "HAVE_PAT": have_pat,
               "RUNNER_TEMP": str(tmp), "GITHUB_STEP_SUMMARY": str(tmp / "summary.md"),
               "GITHUB_SERVER_URL": "https://github.com", "GITHUB_REPOSITORY": "MicroHealthLLC/sast-rules"}
        res = subprocess.run(["bash", "-e", "-c", script], cwd=tmp / "work", env=env, capture_output=True, text=True)
        log = (tmp / "gh.log").read_text() if (tmp / "gh.log").exists() else ""
        return res, log, (tmp / "summary.md").read_text()

    def test_upstream_without_gh_pat_pushes_and_points_at_the_pull_request(self) -> None:
        res, log, summary = self.run_upstream_pr_step("false", "")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("pr create", log)
        url = "https://github.com/MicroHealthLLC/sast-rules/compare/integration...upstream/engine?expand=1"
        self.assertIn(f"::warning title=Pull request not opened::", res.stdout)
        self.assertIn(url, res.stdout)
        self.assertIn(url, summary)
        self.assertIn("Opengrep 1.31.0", summary)

    def test_upstream_with_gh_pat_opens_the_pull_request_against_integration(self) -> None:
        res, log, _ = self.run_upstream_pr_step("true", "")
        self.assertIn("pr create --base integration --head upstream/engine", log)
        self.assertNotEqual(res.returncode, 0)  # the fake gh refuses, as GitHub does: a PAT that fails still fails

    def test_upstream_refreshes_an_open_pull_request_without_gh_pat(self) -> None:
        res, log, _ = self.run_upstream_pr_step("false", "OPEN")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("pr edit upstream/engine --body-file", log)
        self.assertNotIn("pr create", log)
        self.assertNotIn("::warning", res.stdout)


    def test_fips_images_are_pinned_and_checked(self) -> None:
        images = json.loads((ROOT / "fips-images.json").read_text())
        for kind in ("python", "go"):
            out = subprocess.run([str(ROOT / "scripts" / "fips-image.sh"), kind],
                                 capture_output=True, text=True, check=True).stdout.strip()
            self.assertEqual(out, images[kind])
            self.assertRegex(out, rf"^295669632222\.dkr\.ecr\.us-east-1\.amazonaws\.com/microhealthllc/fips-{kind}:[\w.-]+@sha256:[0-9a-f]{{64}}$")
        bad = {
            "python": "295669632222.dkr.ecr.us-east-1.amazonaws.com/microhealthllc/fips-python:dev-latest",
            "go": "docker.io/library/golang:1.26@sha256:" + "0" * 64,
        }
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "scripts").mkdir()
            shutil.copy(ROOT / "scripts" / "fips-image.sh", Path(tmp) / "scripts")
            (Path(tmp) / "fips-images.json").write_text(json.dumps(bad))
            for kind in bad:
                res = subprocess.run([str(Path(tmp) / "scripts" / "fips-image.sh"), kind], capture_output=True, text=True)
                self.assertNotEqual(res.returncode, 0, kind)
                self.assertEqual(res.stdout, "", kind)

    def test_main_is_promoted_only_from_a_green_integration_run(self) -> None:
        # Owner's decision 2026-10-18: a push to integration on which the build
        # check, the rule tests and the end-to-end scan all pass is merged into
        # main; nothing else is.
        ci = load("ci.yml")
        self.assertIn("integration", ci["on"]["push"]["branches"])
        job = ci["jobs"]["promote-main"]
        self.assertEqual(set(job["needs"]), {"changes", "build", "self-scan"})
        for clause in ("github.ref == 'refs/heads/integration'", "github.event_name != 'pull_request'",
                       "needs.build.result == 'success'", "needs.self-scan.result == 'success'"):
            self.assertIn(clause, job["if"])
        self.assertNotIn("always()", job["if"])
        run = job["steps"][-1]["run"]
        self.assertIn("set -euo pipefail", run)
        self.assertIn('scripts/promote_main.sh "$GITHUB_SHA"', run)
        script = (ROOT / "scripts" / "promote_main.sh").read_text()
        self.assertNotIn("--force", script)
        self.assertNotRegex(script, r"push\s[^\n]*\+")

    def test_network_reaches_only_github_gitlab_and_aws(self) -> None:
        # Reports go to GitHub (code scanning, artifacts) and AWS (S3, ECR) and
        # nowhere else; downloads come from GitHub, and upstream rules are
        # cloned read-only from GitHub and GitLab. A new host fails here first.
        allowed = {"github.com", "api.github.com", "raw.githubusercontent.com", "gitlab.com"}
        root = WORKFLOWS.parents[1]
        files = [*WORKFLOWS.glob("*.yml"), *(root / "scripts").glob("*.py"), *(root / "scripts").glob("*.sh"),
                 *(root / "local").glob("*"), root / "sources.yaml", root / "engine.json"]
        for path in files:
            for host in re.findall(r"https?://([A-Za-z0-9.-]+)", path.read_text()):
                self.assertIn(host.lower(), allowed, f"{path.relative_to(root)}: {host}")


if __name__ == "__main__":
    unittest.main()
