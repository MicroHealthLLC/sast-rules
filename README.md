# sast-rules

MicroHealth's static application security testing (SAST): the rules, and the
one GitHub Actions workflow every MicroHealth repository runs to apply them.

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
| The rules are exactly the ones reviewed | The caller pins this workflow by commit; the workflow reads that commit from the job's OIDC token and checks out the rules at it. `dist/<bundle>.yaml` must match `dist/SHA256SUMS`. Nothing is fetched from a rule registry. |
| The engine is exactly the one reviewed | The Opengrep binary is downloaded from its GitHub release and must match the sha256 in `engine.json`, or the run stops. |
| The scan cannot reach the network | It runs in a container with `--network none`. |
| No source code in the build log | The engine's text output is discarded; results are only in the report files. |
| Validated cryptography around the scan | The container is built FROM MicroHealth's FIPS 140-3 Python image; git, the AWS CLI and Python use the system OpenSSL with only the FIPS provider. See [FIPS](#fips) for what is outside that claim. |
| A report says which rules ran | Every JSON report carries `ruleset.rules_evaluated`. A finding whose rule did not run is never treated as fixed. |
| A failed upload never hides a failed scan | The scan is a blocking step; the SARIF upload is not. Both outcomes are recorded separately (`publication-status.json`). |

`tests/test_workflow.py` fails if any of these controls is removed.

## Use it in a repository

`.github/workflows/sast.yml`:

```yaml
name: SAST
on:
  schedule:
    - cron: "30 2 * * *"
  workflow_dispatch:
permissions:
  contents: read
jobs:
  sast:
    permissions: {contents: read, actions: read, security-events: write, id-token: write}
    uses: MicroHealthLLC/sast-rules/.github/workflows/opengrep.yml@<commit-sha> # vYYYY.M.N
    with:
      aws_region: ${{ vars.AWS_REGION_EAST_1 }}
      s3_bucket: ${{ vars.SECURITY_REPORTS_S3_BUCKET }}
    secrets: inherit
```

| Input | Default | Meaning |
|---|---|---|
| `bundle` | `internal` | `internal` (every rule MicroHealth may run on its own code) or `product` (permissive licenses only) |
| `project` | repository name | The Tueri Core project the report belongs to |
| `aws_region` | — | Region of the evidence bucket |
| `s3_bucket` | empty | Evidence bucket; empty skips the upload (Tueri Core then never sees the run) |
| `exclude` | empty | Extra paths to skip, one glob per line. A `.sastignore` file at the repository root is read too. |
| `fail_on_findings` | `false` | Fail the job when a finding is reported that is not suppressed inline |

Secret `AWS_ROLE`: an OIDC role that can pull MicroHealth's FIPS image from ECR
and, when `s3_bucket` is set, write to the bucket. The job needs
`id-token: write`. Outputs: `findings`, `rules_commit`. Artifact
`sast-reports`: `sast.json`, `sast.sarif`, `publication-status.json`.

The report lands at `s3://<bucket>/<project>/sast/dt=<day>/run-<id>/sast.json`,
and the SARIF in GitHub code scanning under the category `sast`.

**Suppress a finding inline**, with the full rule id and the reason it does
not apply, on the line (or the line above):

```python
import xml.etree.ElementTree as ET  # noopengrep: mh.opengrep.python.lang.security.use-defused-xml.use-defused-xml — parsing goes through _safe_parse
```

A suppression without a reason is a lie a security tool tells itself.

## Where the rules come from

| Source | Path | License | Bundles | Updates |
|---|---|---|---|---|
| [GitLab sast-rules](https://gitlab.com/gitlab-org/security-products/sast-rules) | `upstream/gitlab/` | per file: MIT, Apache-2.0 (gosec), GPL-2.0 (flawfinder), LGPL, LGPL + Commons Clause | by license | daily check for a new release → pull request |
| [opengrep-rules](https://github.com/opengrep/opengrep-rules) (archived 2025-11-28) | `upstream/opengrep/` | LGPL-2.1 + Commons Clause | internal | frozen |
| MicroHealth | `rules/microhealth/` | MIT | internal, product | written here |

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
with its reason.

## Changing rules (MicroHealth)

- **Never edit `upstream/`.** Turn a rule off or re-grade it in
  [`overrides.yaml`](overrides.yaml); a reason is required. Or copy it into
  `rules/microhealth/` and change the copy.
- A new rule goes in `rules/microhealth/<language>/<name>.yaml`, with a test
  file of the same name beside it (`# ruleid:` and `# ok:` comments).
- `python3 scripts/build.py` rebuilds `dist/` and the lock. CI fails if they
  were not rebuilt, if any rule does not load in the pinned engine, or if a
  rule test fails.
- GitLab's `security-severity` words (`Low`, `High`) become the numbers GitHub
  code scanning requires; the original is kept as
  `metadata.mh_upstream_security_severity`.

## How updates reach every repository

1. `upstream.yml` (daily) opens one pull request per kind of update: a new
   GitLab release, with the rules added, changed, retired and relicensed
   listed; a new Opengrep release; newer FIPS image digests.
2. A MicroHealth maintainer reviews and merges it.
3. `release.yml` tags `vYYYY.M.N`, publishes the bundles, `SHA256SUMS` and
   `NOTICE.md`, and opens a pull request in every repository listed in
   [`consumers.yaml`](consumers.yaml) moving its pin
   (`scripts/bump_consumers.sh`).
4. Each repository merges its pull request when it is ready to run the new
   rules. Nothing changes in a repository without a reviewed merge.

## Repository security

This repository is public and its workflows hold credentials, so it is locked
down:

- Issues, discussions, the wiki and projects are off; interactions are limited
  to collaborators.
- `main` and the release tags are protected: no force pushes, no deletion, and
  changes to `main` go through a reviewed pull request.
- Workflows from forks need a maintainer's approval before they run, and
  never receive secrets. No workflow uses `pull_request_target`.
- The default `GITHUB_TOKEN` is read-only; each job asks for what it needs.
  Only GitHub's and AWS's own actions may run, pinned by commit.
- AWS access is by OIDC only — no stored keys. The role trusts MicroHealth's
  repositories and is scoped to pulling the FIPS images and writing scan
  evidence.
- Secret scanning and push protection are on.

## FIPS

The scan runs in a container built FROM MicroHealth's FIPS 140-3 Python image.
Python, git and the AWS CLI there use the system OpenSSL with only the FIPS
provider (OpenSSL FIPS Provider 3.1.2, CMVP #4985).

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
