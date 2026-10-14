# sast-rules

MicroHealth's security scanning: the static analysis (SAST) rules, and the one
GitHub Actions workflow every MicroHealth repository runs — SAST, Trivy, the
SBOM and ZAP DAST, in parallel, in one report.

- **Engine:** [Opengrep](https://github.com/opengrep/opengrep) (LGPL-2.1),
  pinned by version and sha256 in [`engine.json`](engine.json).
- **Rules:** GitLab's SAST rules, the archived Opengrep community rules, and
  rules MicroHealth writes, published as two license-checked bundles in
  [`dist/`](dist).
- **Results:** a JSON report for [Tueri Core](https://github.com/MicroHealthLLC)
  (MicroHealth's compliance platform) and SARIF for GitHub code scanning.

This repository is public so that the rules a MicroHealth system is scanned
with can be read, verified and reproduced by anyone, including an assessor.
It is maintained by MicroHealth for MicroHealth's repositories.

> **Contributions.** This repository does not take issues, comments,
> discussions or pull requests from outside MicroHealth; they are switched off.
> You are welcome to fork it and to use the rules and the workflow under their
> licenses (below).

---

## What a scan guarantees

| Guarantee | How |
|---|---|
| The rules are exactly the ones reviewed | The caller names this workflow `@main` (every scan change on `main` is a release, so `main` IS the newest release) or a commit; GitHub resolves that to one commit when the run starts, and the workflow reads that commit from the job's OIDC token and checks out the rules at it. `dist/<bundle>.yaml` must match `dist/SHA256SUMS`. Nothing is fetched from a rule registry. |
| The engine is exactly the one reviewed | The Opengrep binary is downloaded from its GitHub release and must match the sha256 in `engine.json`, or the run stops. |
| The scan cannot reach the network | It runs in a container with `--network none`. |
| No source code in the build log | The engine's text output is discarded; results are only in the report files. |
| Validated cryptography around the scan | The container is built FROM MicroHealth's FIPS 140-3 Python image; git, the AWS CLI and Python use the system OpenSSL with only the FIPS provider. See [FIPS](#fips) for what is outside that claim. |
| A report says which rules ran | Every JSON report carries `ruleset.rules_evaluated`. A finding whose rule did not run is never treated as fixed. |
| A failed upload never hides a failed scan | The scan is a blocking step; the SARIF upload is not. Both outcomes are recorded separately (`publication-status.json`). |
| A reviewed suppression is not a code scanning alert | GitHub opens an alert for a result Opengrep marks as suppressed in source (`noopengrep: <rule id>` with its reason), so code scanning gets a copy without them (`scripts/sarif_for_code_scanning.py`). The `sast-reports` artifact (`sast.sarif`) and `sast.json` keep every result, suppressed ones with their state. |

`tests/test_workflow.py` fails if any of these controls is removed.

## Use it in a repository

One workflow runs every scanner, in parallel, and ends in one report:
**SAST** (Opengrep with these rules), **Trivy** (dependency vulnerabilities,
secrets and misconfiguration, for the repository and any images), the
**SBOM** (CycloneDX) and **ZAP DAST**. Every scanner is **on by default**;
switch one off with its input.

`.github/workflows/security-scan.yml`:

```yaml
name: Security scan
on:
  push:
    branches: [integration]     # the default branch: reports feed Tueri Core
  pull_request:                 # a pull request: a check, reports stay artifacts
  schedule:
    - cron: "30 2 * * *"
  workflow_dispatch:
permissions:
  contents: read
jobs:
  security:
    permissions: {contents: read, actions: read, security-events: write, id-token: write}
    uses: MicroHealthLLC/sast-rules/.github/workflows/security-scan.yml@main # the newest release, always
    with:
      aws_region: ${{ vars.AWS_REGION_EAST_1 }}
      s3_bucket: ${{ vars.SECURITY_REPORTS_S3_BUCKET }}
      zap_target: ${{ vars.ZAP_TARGET_URL }}
      # sast: false        # each scanner is on unless switched off
      # trivy: false
      # sbom: false
      # zap: false
    secrets: inherit
```

| Input | Default | Meaning |
|---|---|---|
| `sast`, `trivy`, `sbom`, `zap` | `true` | Switch a scanner off |
| `aws_region` | — | Region of the evidence bucket |
| `s3_bucket` | empty | Evidence bucket; empty keeps every report as an artifact only |
| `project` | repository name | The Tueri Core project the reports belong to |
| `ref` | triggering ref | Branch, tag or commit to scan |
| `fail_on` | `none` | Fail the run on a finding at or above `critical`, `high`, `medium` or `low` |
| `bundle` | `internal` | SAST rules: `internal` or `product` (permissive licenses only) |
| `exclude` | empty | Paths SAST skips, one glob per line; `.sastignore` is read too |
| `sast_timeout_minutes` | `120` | How long SAST may take |
| `baseline_ref` | empty | SAST reports only what is new since this ref, e.g. `${{ github.base_ref }}` on a pull request |
| `images` | empty | Images Trivy also scans (and SBOMs), one reference per line |
| `image_registries` | empty | ECR account ids those images live in |
| `trivy_runs_on` | `ubuntu-latest` | A larger runner, for images too big for a standard one (Trivy reads images straight from the registry, one copy on disk; on a hosted runner an image scan first frees the preinstalled toolchains and works on the largest disk, `/mnt` on a standard runner) |
| `zap_target` | empty | URL ZAP scans (staging or preview, never production). **Empty: ZAP is recorded as not run, with the reason**, and the build does not fail |
| `zap_scan` | `baseline` | `baseline` (passive) or `full` / `api` (active attack: needs the `dast-active` environment's approval and `zap_confirm` equal to the target) |
| `zap_runs_on` | `ubuntu-latest` | A self-hosted runner, for a target inside a private network |

`AWS_ROLE` (secret): OIDC role that pulls MicroHealth's FIPS images from ECR
and writes the bucket. The calling job needs the four permissions above.

**Where reports go.** Only a full scan of the default branch feeds Tueri
Core: `<project>/sast/`, `trivy-fs/`, `trivy-image/<image>/`, `sbom/`,
`zap-dast/`. Another branch's scans go under `<project>/_branch-scans/`,
which Tueri Core never ingests; a pull request's or a diff scan's are
artifacts only. Absence in a partial scan is not evidence that something was
fixed.

**One report.** The `Security report` job writes `security-report.json` (and
a summary table on the run page): every scanner's status (`ran`, `not_run`,
`failed`, `disabled`), counts by severity, SBOM component counts, the rules
commit. A scanner that was on and left no report **fails the run**; a count
is `null` unless the scanner ran, so "did not run" never reads as "found
nothing". The report is the `security-report` artifact and
`<project>/_security-scan/…` in the bucket.

Each scanner is also its own reusable workflow (`opengrep.yml`, `trivy.yml`,
`zap.yml`) for a repository that needs only one.

### Locally

The same rules and engine, at the commit your workflow runs (`@main` is resolved to its commit when the script starts): copy
[`local/sast.sh`](local/sast.sh) into the repository (e.g. `scripts/sast.sh`)
and run it, or wire it into `make`, a pre-push hook or a test script:

```sh
scripts/sast.sh                     # fails on an ERROR finding
scripts/sast.sh --fail-on warning   # stricter
scripts/sast.sh --fail-on none --json sast.json
```

It needs git, curl, python3, sha256sum and docker or nerdctl logged in to
MicroHealth's ECR. It never needs editing: it reads the reference (`@main` or a commit) from
`.github/workflows/`.

**Suppress a finding inline**, with the full rule id and the reason it does
not apply, on the line or the line above:

```python
# noopengrep: mh.opengrep.python.lang.security.use-defused-xml.use-defused-xml — parsing goes through _safe_parse
import xml.etree.ElementTree as ET
```

A suppression without a reason is a lie a security tool tells itself.

## Where the rules come from

| Source | Path | License | Bundles | Updates |
|---|---|---|---|---|
| [GitLab sast-rules](https://gitlab.com/gitlab-org/security-products/sast-rules) | `upstream/gitlab/` | per file: MIT, Apache-2.0 (gosec), GPL-2.0 (flawfinder), LGPL, LGPL + Commons Clause | by license | daily check for a new release → pull request |
| [opengrep-rules](https://github.com/opengrep/opengrep-rules) (archived 2025-11-28) | `upstream/opengrep/` | LGPL-2.1 + Commons Clause | internal | frozen |
| MicroHealth | `rules/microhealth/` | MIT | internal, product | written here |

Only **security** rules are published: a rule whose `metadata.category` is
anything else (style, correctness, portability, performance, …) stays listed
in the lock as `excluded`, with the reason, and enters no bundle. SAST findings
are security findings; a style rule run across a codebase buries them.

[`licenses.yaml`](licenses.yaml) decides which license may enter which bundle,
and the build fails on a license it does not list:

- **internal**: everything MicroHealth may run on its own code. Running a rule
  is using it, not selling it, so the Commons Clause permits it.
- **product**: MIT and Apache-2.0 only. This bundle ships inside a MicroHealth
  product (Tueri Core's code scanner). Copyleft rules and Commons Clause rules
  are kept out of it.
- Rules under GitLab's Enterprise Edition license are not copied here at all.

Attributions: [`NOTICE.md`](NOTICE.md), shipped beside every bundle.

## Rule ids are stable

Every rule is published as `mh.<source>.<upstream id>`. Opengrep's rules are
qualified by folder and file, as the original registry did
(`mh.opengrep.python.lang.security.use-defused-xml.use-defused-xml`). A
finding's identity in Tueri Core includes its rule id, so an upstream folder
move must never change it.

[`rules.lock.json`](rules.lock.json) lists every rule ever shipped: source,
upstream path, license, content hash, bundles and status. A rule that leaves
upstream stays listed as `retired`; a rule MicroHealth turns off is `disabled`,
with its reason, and a rule it narrows carries `refined`, with its reason.

## Changing rules (MicroHealth)

- **Never edit `upstream/`.** Turn a rule off or re-grade it in
  [`overrides.yaml`](overrides.yaml); a reason is required. Or copy it into
  `rules/microhealth/` and change the copy.
- A rule that is right in general but wrong in one case is **refined** in
  `overrides.yaml`: `add` appends narrowing clauses (`pattern-not`,
  `pattern-not-inside`, `pattern-not-regex`, …) to its `patterns`, and
  `exclude_paths` adds path exclusions. A refinement can only narrow a rule.
  Each one needs a fixture in `tests/refine/` naming the rule's full `mh.*`
  id on `ruleid:` / `ok:` lines (several on one line where rules overlap); `tests/refine/run.py` checks them against the
  built bundle.
- A search rule whose one known false positive is a text shape gets an
  `allow:` entry instead: a `not-regex` the build adds as `pattern-not-regex`
  (a finding overlapping a match is dropped) to every rule it names, by id or
  by an id prefix ending in `*`. The secret rules honour gitleaks' own
  `gitleaks:allow` this way.
- `overrides.yaml` and the other configuration files must not repeat a key:
  YAML would keep only the last, so the build refuses it.
- A new rule goes in `rules/microhealth/<language>/<name>.yaml`, with a test
  file of the same name beside it (`# ruleid:` and `# ok:` comments).
- Every rule file there starts with a `# License:` header, read per file as
  GitLab's are: `MIT` for a rule we wrote, the upstream license for a changed
  copy of an upstream rule (an LGPL rule we narrowed is still LGPL and stays
  out of the product bundle). A copy gets a new id, says in its header what
  changed, carries `metadata.mh_replaces: <old id>`, and the old id is
  disabled in `overrides.yaml` with a reason naming the copy.
- `python3 scripts/build.py` rebuilds `dist/` and the lock. CI fails if they
  were not rebuilt, if any rule does not load in the pinned engine, or if a
  rule test or a refinement fixture fails.
- GitLab's `security-severity` words (`Low`, `High`) become the numbers GitHub
  code scanning requires; the original is kept as
  `metadata.mh_upstream_security_severity`.

## How updates reach every repository

1. `upstream.yml` (daily) opens one pull request per kind of update: a new
   GitLab release, with the rules added, changed, retired and relicensed
   listed; a new Opengrep release; newer FIPS image digests
   (`fips-images.json`). No update edits `.github/workflows/`: GitHub
   refuses a workflow change pushed with an Actions token, and the job checks
   for one before it pushes.
2. A MicroHealth maintainer reviews and merges it into `integration`, then
   merges `integration` into `main` by pull request. Every change takes that
   path; nothing is pushed to `main` directly ([`AI_RULES.md`](AI_RULES.md) §1).
3. `release.yml` tags `vYYYY.M.N` and publishes the bundles, `SHA256SUMS`
   and `NOTICE.md`. Every push to `main` that changes what a scan runs is a
   release, so `main` is always the newest one.
4. Every MicroHealth repository calls the scan `@main`, so its next run uses
   the new release with nothing to merge: the review is step 2, here. A
   repository that still pins a commit gets a pull request moving the pin
   (`scripts/bump_consumers.sh`, [`consumers.yaml`](consumers.yaml)); one on
   `@main` has no pin and is skipped.

## Repository security

This repository is public and its workflows hold credentials, so it is locked
down:

- Issues, discussions, the wiki and projects are off; interactions are limited
  to collaborators.
- `main` and the release tags are protected: no force pushes, no deletion, and
  changes to `main` go through a reviewed pull request from `integration`.
- Workflows from forks need a maintainer's approval before they run, and
  never receive secrets. No workflow uses `pull_request_target`.
- The default `GITHUB_TOKEN` is read-only; each job asks for what it needs.
  Only GitHub's and AWS's own actions may run, pinned by commit.
- AWS access is by OIDC only — no stored keys. The role trusts MicroHealth's
  repositories and is scoped to pulling the FIPS images and writing scan
  evidence.
- Secret scanning and push protection are on. `.github/secret_scanning.yml`
  skips only rule material whose fake credentials exist to be matched: the
  secret rules' test files (`rules/microhealth/generic/*.txt`), `upstream/`
  and `dist/`. Every other path is still scanned.

## FIPS

The scan runs in a container built FROM MicroHealth's FIPS 140-3 Python image.
Python, git and the AWS CLI there use the system OpenSSL with only the FIPS
provider (OpenSSL FIPS Provider 3.1.2, CMVP #4985).

Every image the workflows and scripts build starts FROM a FIPS base pinned by
tag and digest in [`fips-images.json`](fips-images.json), read through
`scripts/fips-image.sh`, which refuses anything but a `microhealthllc/fips-*`
image in MicroHealth's ECR pinned by `sha256`. The pins are kept out of the
workflow files on purpose: `upstream.yml` moves them daily
(`scripts/fips_bump.py`) and pushes with an Actions token, and GitHub never
lets such a token change `.github/workflows/`.

**Trivy** is built from source once per version (`engines.yml`) on
MicroHealth's FIPS Go image with the Go Cryptographic Module (`GOFIPS140`,
CMVP #5247); every Go module is checked against sum.golang.org, and every scan
refuses a binary whose sha256 is not the one `engine.json` records. Its
vulnerability database is downloaded on each run.

**ZAP is outside the FIPS claim.** It is Java, and its TLS is the JDK's. It is
a test tool attacking a target, not part of any product. Its release tarball
and scan scripts are refused unless their SHA-256 matches.

**Opengrep is outside the FIPS claim.** It is an OCaml binary linked against
musl and loads no OpenSSL. It contains an HTTPS client of its own (its
`validate` command uses it to fetch lints), so every scan runs with
`--network none`. The scan reads local files and writes a report. It performs
no cryptography that a FIPS boundary covers.

## Licenses

Everything here is used, and redistributed, only as its license allows. The
short version:

| What | License | Run it on MicroHealth's code (internal) | Ship it in a product MicroHealth sells | What the license asks, and how it is met |
|---|---|---|---|---|
| This repository's own files (`scripts/`, `tests/`, `rules/microhealth/`, `.github/`, root config and docs) | **MIT**, MicroHealth, LLC ([`LICENSE`](LICENSE)) | yes | yes | Keep the copyright and license notice: [`LICENSE`](LICENSE), shipped as `dist/licenses/MIT.txt` |
| GitLab rules headed MIT | MIT, GitLab Inc. | yes | yes | Keep GitLab's notice: [`NOTICE.md`](NOTICE.md) and `dist/licenses/upstream-gitlab-LICENSE.txt` ship with every bundle |
| GitLab's Go rules (from gosec) | Apache-2.0 | yes | yes | Ship the license text (`dist/licenses/Apache-2.0.txt`) and state the changes (every bundle's header and `NOTICE.md`) |
| GitLab's C rules (from flawfinder) | GPL-2.0 | yes | **no** | Ship the license text and the complete source (this repository); kept out of the product bundle |
| GitLab `rules/lgpl/` | LGPL-3.0 | yes | **no** | Ship the license texts, state the changes, keep the source available (this repository) |
| GitLab `rules/lgpl-cc/` and all of opengrep-rules | LGPL-2.1 **with the Commons Clause** | yes | **no** | As LGPL-2.1, plus no "Sell". Publishing them free and running them on our own code are not sales; they never enter the product bundle |
| GitLab `rules/gitlab/` | GitLab Enterprise Edition (proprietary) | **not used** | **not used** | Not copied into this repository at all |
| Opengrep, the engine | LGPL-2.1 | yes (downloaded at scan time) | only with its notice and source | Unmodified binary, pinned by sha256; every release attaches the engine's source for the pinned version |

How this is enforced, not just written down:

- [`licenses.yaml`](licenses.yaml) is the decision: which license may enter
  which bundle. The **product** bundle accepts **MIT and Apache-2.0 only**.
  The build fails on a rule whose license is not listed, and moving a license
  into the product bundle is a reviewed change to that file.
- The license of every rule is read from its own file's `# License:` header,
  not assumed from its folder, and recorded on the rule
  (`metadata.mh_license`) and in [`rules.lock.json`](rules.lock.json).
- Every bundle's header lists the licenses of the rules inside it and the
  changes made to them. [`NOTICE.md`](NOTICE.md) and the full text of every
  license (`dist/licenses/`) ship beside every bundle and with every release.
- The upstream files are kept unmodified under `upstream/`, so this
  repository is always the complete corresponding source of every bundle.

Two points are worth a lawyer's confirmation before relying on them in a
contract, and MicroHealth treats them conservatively until then:

1. **The Commons Clause** (GitLab `rules/lgpl-cc/`, opengrep-rules). Its rules
   are used on MicroHealth's own code and published here free of charge, never
   sold and never shipped in a product.
2. **Shipping the Opengrep binary inside a product** (Tueri Core's code scanner
   image). LGPL-2.1 allows it with the license text, a notice, and access to the
   source. The image carries all three: `dist/licenses/LGPL-2.1-only.txt`, a
   notice naming the version, and this repository's release copy of the source.

"Semgrep" appears in this repository only where an upstream license or rule
file names it (the Commons Clause's licensor, rule metadata). Those files are
reproduced as their licenses require and are not MicroHealth's use of the
name.
