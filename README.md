# sast-rules

MicroHealth's static-analysis (SAST) rules and the one workflow every
MicroHealth repository uses to run them. The engine is
[Opengrep](https://github.com/opengrep/opengrep) (LGPL-2.1), pinned by version
and sha256 in `engine.json`.

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
    uses: MicroHealthLLC/sast-rules/.github/workflows/opengrep.yml@<commit-sha> # vYYYY.MM.N
    with:
      aws_region: ${{ vars.AWS_REGION_EAST_1 }}
      s3_bucket: ${{ vars.SECURITY_REPORTS_S3_BUCKET }}
    secrets: inherit
```

Inputs: `bundle` (`internal`, the default, or `product`), `project` (Tueri Core
project; default the repository name), `exclude` (globs, one per line; a
`.sastignore` file at the repository root is read too), `fail_on_findings`.
`AWS_ROLE` must be able to pull from MicroHealth's ECR (the scanner image is
built FROM the FIPS Python image) and write to the bucket.

The report lands at `s3://<bucket>/<project>/sast/dt=<day>/run-<id>/sast.json`,
where Tueri Core ingests it, and the SARIF in GitHub code scanning under the
category `sast`.

Suppress one finding inline with a reason:
`# noopengrep: mh.gitlab.python_crypto_rule-hash-md5 — <why it does not apply>`.
The engine matches a trailing part of the id too, so existing comments naming
the old registry ids keep working.

## Where the rules come from

| Source | Path | License | Bundles | Updates |
|---|---|---|---|---|
| [GitLab sast-rules](https://gitlab.com/gitlab-org/security-products/sast-rules) | `upstream/gitlab/` | per file: MIT, Apache-2.0 (gosec), GPL-2.0 (flawfinder), LGPL, Commons Clause | by license (below) | daily check for a new tag → PR |
| [opengrep-rules](https://github.com/opengrep/opengrep-rules) (archived 2025-11-28) | `upstream/opengrep/` | LGPL-2.1 + Commons Clause | internal | frozen |
| MicroHealth | `rules/microhealth/` | MIT | internal, product | written here |

`licenses.yaml` decides which license may enter which bundle:

- **internal**: everything we may run on our own code (using a rule is not
  selling it, so the Commons Clause permits it).
- **product**: MIT and Apache-2.0 only. This is what ships inside a product
  customers pay for (Tueri Core's Code module scanner). Copyleft and the
  Commons Clause stay out unless counsel decides otherwise; the build fails if
  one gets in.
- GitLab EE-licensed rules are not vendored at all.

Nothing is downloaded from a rule registry at scan time.

## Rule ids are stable

Every rule is published as `mh.<source>.<upstream id>` (opengrep's are
qualified by folder and file, as the original registry did). A finding's
identity in Tueri Core includes the rule id, so an upstream folder move must
never change it.

`rules.lock.json` lists every rule ever shipped, with its source, license,
content hash, bundles and status. A rule that leaves upstream is kept as
`retired`; one we turn off is `disabled`, with its reason. Each scan report
names the rules it ran (`ruleset.rules_evaluated`), so Tueri Core never reads
"this rule stopped running" as "the code was fixed".

## Changing rules

- **Never edit `upstream/`.** Turn a rule off or re-grade it in
  `overrides.yaml` (a reason is required), or copy it into `rules/microhealth/`
  and change the copy.
- Write a rule in `rules/microhealth/<lang>/<name>.yaml` with a test file of
  the same name beside it (`# ruleid:` / `# ok:` comments).
- `python3 scripts/build.py` rebuilds `dist/` and the lock; CI fails if they
  were not rebuilt (`--check`), if any rule fails to load in the pinned
  Opengrep, or if a rule test fails.

## How updates reach every repository

1. `upstream.yml` (daily) opens one PR per kind of update: GitLab's newest tag
   (with the rules added, changed, retired and relicensed listed), a new
   Opengrep release, newer FIPS image digests.
2. A person reviews and merges it.
3. `release.yml` tags `vYYYY.MM.N`, publishes the bundles, and opens a PR in
   every repository in `consumers.yaml` moving its pin
   (`scripts/bump_consumers.sh`; needs the `GH_PAT` secret).
4. Each repository merges its PR when it is ready to run the new rules.

## FIPS

The scan runs in a container built FROM MicroHealth's FIPS Python image, and
every Python, git and AWS call goes through the system OpenSSL with only the
FIPS provider. Opengrep itself is an OCaml binary linked against musl. It loads
no OpenSSL, so it is **outside the FIPS claim**. It does contain an HTTPS
client (`opengrep validate` uses it to fetch lints), so every scan runs with
`--network none`. The scan reads local files and writes a report; it performs
no cryptography that a FIPS boundary covers.
