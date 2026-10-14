# AI_RULES.md — sast-rules governance
# CLAUDE.md is a symlink to this file. Read it before every session. No rule is optional.

This repository holds MicroHealth's SAST rules (GitLab's, the archived Opengrep
community rules, and MicroHealth's own), the pinned Opengrep engine, and the
one reusable workflow (`security-scan.yml`: SAST, Trivy, SBOM, ZAP) that every
MicroHealth repository (~/TueriDev, ~/TueriCXO, ~/TueriCore, ~/simplr-ehr,
~/fluenta, ~/e-aar, ~/gnosis, ~/fips-container, ...) calls `@main`. A change
merged to `main` is a release that every one of them runs on its next scan.
It is public, so an assessor can reproduce any scan. If a rule here and a
request conflict, stop and say so.

## §0 Session protocol

### 0.1 Read first
Read this file and `README.md` before changing anything. The design decisions
(what a scan guarantees, licenses, FIPS, rule ids) are recorded there; do not
re-litigate them.

### 0.2 Plan before execute
State the plan (files to change, tests that prove it) before editing. Flag any
change that touches a workflow, `engine.json`, `fips-images.json`,
`licenses.yaml` or a guarantee in README's "What a scan guarantees".

### 0.3 Self-audit after every task
Report: files changed, the §4 commands run and their actual result, anything
skipped and why, and every push or PR made (branch and commit).

## §1 Branching — integration first, then a PR to main. ALWAYS.

- `integration` is the default branch and the working branch. Every change is
  committed to `integration` and pushed to `origin integration` first.
- `main` is the release branch. It changes ONLY by a pull request
  `integration` → `main`. Never push to `main`, never open a PR from any other
  branch to `main`.
- A side branch (`rule-fp/<repo>-<date>`, a bot's update branch) is merged
  into `integration` (PR base `integration`), never into `main`. If one was
  opened against `main`, retarget it to `integration`.
- Keep the two in sync. Before starting work, fast-forward `integration` to
  `origin/integration`; after a PR to `main` merges, fast-forward
  `integration` to `main` (the merge commit) and push it, so `main` never has
  commits `integration` lacks. Check with
  `git log --oneline origin/integration..origin/main` (must be empty).
- Resolve conflicts on the side branch by merging `origin/integration` into
  it, never by editing on GitHub and never by force-pushing `integration` or
  `main` (both refuse it).

## §2 Nothing leaves except to GitHub and AWS

- The only outbound destinations are GitHub (git, the API, releases, code
  scanning) and MicroHealth's AWS account (ECR for the FIPS images, the
  scan-evidence bucket), plus the checksum-pinned downloads the workflows
  already make (Opengrep and ZAP releases from GitHub, Go modules checked
  against sum.golang.org, Trivy's vulnerability database).
- NEVER add a notification, webhook or messaging call of any kind (Telegram,
  Slack, Discord, Teams, email, ntfy, pastebins, analytics), in a workflow, a
  script or a rule. Never add a new host to a workflow without the owner's
  decision.
- Rules never execute anything and never touch the network: the engine runs
  in a container with `--network none`. Do not add `fix:` rewrites that
  generate code calling out, and do not remove `--network none`.
- No secrets in any file. AWS access is OIDC only (`secrets.AWS_ROLE`).
  GitHub automation uses the org secret `GH_PAT`, shared with this repository
  from the organization (as for every other MicroHealth repository); never
  copy a token into a repository secret, a file or a log.

## §3 Changing rules — false positives

- **Never edit `upstream/`.** It is the verbatim source of every bundle.
- A false positive is fixed by narrowing, in this order of preference:
  1. `refine:` in `overrides.yaml` (`add` narrowing clauses, `exclude_paths`)
     with a fixture in `tests/refine/` naming the full `mh.*` id;
  2. `allow:` for a known text shape (e.g. `gitleaks:allow`);
  3. a changed copy in `rules/microhealth/<language>/` with `mh_replaces`,
     its own `# ruleid:` / `# ok:` test file, and the old id disabled in
     `overrides.yaml` with a reason naming the copy;
  4. `disable` with a reason, only when the rule cannot be made precise.
- Every narrowing states in its `reason` (or the rule's header comment) which
  repository tripped it, how many hits, the shape it now skips, and what it
  STILL reports. The fixture keeps a `ruleid:` line for the true positive next
  to each new `ok:` line. Never narrow a rule so far that its real finding
  stops being reported, to make a consumer's scan green.
- When two branches narrowed the same rule, keep both narrowings and both
  fixture sets; combine their regexes rather than picking one side.
- Only security rules ship; licenses decide bundles (`licenses.yaml`). The
  product bundle takes MIT and Apache-2.0 only.

## §4 Test before every push — MANDATORY

Generated files (`dist/`, `rules.lock.json`) are never merged or edited by
hand: take either side, then rebuild.

```bash
python3 scripts/build.py && python3 scripts/build.py --check  # dist/ and lock match the sources
python3 -m unittest discover -s tests                         # unit tests
# Pinned engine (engine.json, sha256-checked), offline. It is musl-linked, so run it in alpine:
OG="docker run --rm --network none -u $(id -u) -e HOME=/tmp -v <engine dir>:/c:ro -v $PWD:$PWD -w $PWD --entrypoint /c/opengrep-<version>-x86_64 alpine:3.22"
$OG scan --test rules/microhealth                              # every MicroHealth rule test passes
OPENGREP="$OG" python3 tests/refine/run.py                     # every refine fixture passes
# Both bundles load with 0 errors: scan a one-file dir with --config dist/internal.yaml and dist/product.yaml
```

If a step cannot run locally, say so in the self-audit and watch CI on the
PR until it is green. Never report "done" on an unverified push.

## §5 Commits and PRs

- Subjects say what changed in plain words ("Narrow nine rules that reported
  false positives on Fluenta"); the body lists each rule and why.
- `upstream.yml` (daily) opens update PRs; they target `integration` like
  everything else. It pushes with an Actions token, which GitHub never lets
  change `.github/workflows/`: anything a bot moves (FIPS image pins:
  `fips-images.json`) lives outside the workflow files, never inside them. `release.yml` tags `vYYYY.M.N` on `main`.

## §6 Documentation

Keep `README.md` and this file in step with the code, in the SAME commit as
the change. An assessor reads them; a stale document is a finding.
