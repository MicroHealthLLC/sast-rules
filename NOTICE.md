# Notices

This file ships beside every rule bundle (`dist/NOTICE.md`), with the full
text of every license involved (`dist/licenses/`). Each rule's own license is
also recorded on the rule itself (`metadata.mh_license`) and in
`rules.lock.json`. `licenses.yaml` decides which license may enter which
bundle, and the build fails on a license it does not list.

## Changes MicroHealth makes to upstream rules

The files under `upstream/` are the upstream files, unmodified. The bundles
in `dist/` are built from them by `scripts/build.py`, which changes each rule
in exactly these ways and no others:

- its `id` is prefixed `mh.<source>.` (opengrep rules are also qualified by
  folder and file name, as the original registry did);
- `metadata.mh_source`, `metadata.mh_upstream_id` and `metadata.mh_license`
  are added;
- a word in `metadata.security-severity` (`Low`, `High`, …) is replaced by a
  number, and the original is kept as `metadata.mh_upstream_security_severity`;
- `overrides.yaml` is applied (rules turned off or re-graded, each with its
  reason).

Changes are made by MicroHealth, LLC. The date of each change is the date of
the commit in https://github.com/MicroHealthLLC/sast-rules that built the
bundle; that repository is the complete corresponding source of every bundle.

## GitLab SAST rules

https://gitlab.com/gitlab-org/security-products/sast-rules, vendored
unmodified under `upstream/gitlab/` at the release and commit `sources.yaml`
pins. Each file states its own license in a `# License:` header:

| Files | License | Bundles | Text |
|---|---|---|---|
| `csharp/`, `java/`, `javascript/`, `python/`, `scala/`, one `go/` rule | MIT, Copyright (c) 2011-present GitLab Inc. | internal, product | `licenses/upstream-gitlab-LICENSE.txt` |
| `go/` (derived from gosec, https://github.com/securego/gosec) | Apache License 2.0, (c) gosec authors | internal, product | `licenses/Apache-2.0.txt` |
| `c/` (derived from flawfinder) | GNU GPL 2.0, Copyright (c) 1989, 1991 Free Software Foundation, Inc. | internal | `licenses/GPL-2.0-only.txt` |
| `rules/lgpl/` | GNU LGPL 3.0 | internal | `licenses/upstream-gitlab-rules-lgpl-LICENSE.txt`, `licenses/LGPL-3.0-only.txt`, `licenses/GPL-3.0-only.txt` |
| `rules/lgpl-cc/` | GNU LGPL 2.1 with the Commons Clause License Condition v1.0 | internal | `licenses/upstream-gitlab-rules-lgpl-cc-LICENSE.txt` |

GitLab's `rules/gitlab/` folder is **not** vendored or bundled. Its LICENSE is
GitLab's Enterprise Edition license, which requires a GitLab subscription.

The MIT license of GitLab's rules:

> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to
> deal in the Software without restriction, including without limitation the
> rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
> sell copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions: The above copyright
> notice and this permission notice shall be included in all copies or
> substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS",
> WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
> TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
> NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
> FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
> TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
> THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Opengrep rules

https://github.com/opengrep/opengrep-rules (archived 2025-11-28), vendored
unmodified under `upstream/opengrep/` at the commit `sources.yaml` pins.
GNU LGPL 2.1 with the Commons Clause License Condition v1.0; the licensor
named in its LICENSE is Semgrep, Inc. Full text:
`licenses/upstream-opengrep-LICENSE.txt` and `licenses/LGPL-2.1-only.txt`.

**Internal bundle only.** The Commons Clause withholds the right to "Sell"
the software: to provide, for a fee, a product or service whose value
derives entirely or substantially from it. MicroHealth runs these rules on
its own code and publishes them here free of charge; neither is a sale. They
are never placed in the product bundle.

## MicroHealth rules

`rules/microhealth/`: Copyright (c) 2026 MicroHealth, LLC. MIT; see
`LICENSE` (shipped as `licenses/MIT.txt`).

## The scan engine

The workflow runs Opengrep (https://github.com/opengrep/opengrep), GNU LGPL
2.1, downloaded unmodified from its GitHub release at the version and sha256
`engine.json` pins. This repository does not redistribute it. Each release of
this repository attaches the engine's complete source for the pinned version
(`opengrep-<version>-source.tar.gz`), so that anyone MicroHealth gives the
binary to can obtain the source from the same place as the rules.
