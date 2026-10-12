# Notices

The rule bundles built from this repository contain rules from these sources.
Each rule's own license is recorded in its `metadata.mh_license` and in
`rules.lock.json`; `licenses.yaml` decides which bundle a license may enter.

## GitLab SAST rules

https://gitlab.com/gitlab-org/security-products/sast-rules — vendored
unmodified under `upstream/gitlab/` at the commit `sources.yaml` pins.

- MIT rules: Copyright (c) 2011-present GitLab Inc. Permission is hereby
  granted, free of charge, to any person obtaining a copy of this software and
  associated documentation files (the "Software"), to deal in the Software
  without restriction, including without limitation the rights to use, copy,
  modify, merge, publish, distribute, sublicense, and/or sell copies of the
  Software, and to permit persons to whom the Software is furnished to do so,
  subject to the following conditions: The above copyright notice and this
  permission notice shall be included in all copies or substantial portions of
  the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
  EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
  OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
  ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
  DEALINGS IN THE SOFTWARE.
- Go rules derived from gosec: Apache License 2.0, (c) gosec authors
  (https://github.com/securego/gosec). https://www.apache.org/licenses/LICENSE-2.0
- C rules derived from flawfinder: GPL 2.0 (internal bundle only).
- `rules/lgpl` (LGPL-3.0) and `rules/lgpl-cc` (LGPL-2.1 with the Commons
  Clause): internal bundle only. Their LICENSE files are vendored beside them.
- Rules under the GitLab Enterprise Edition license are not vendored.

## Opengrep rules

https://github.com/opengrep/opengrep-rules (archived 2025-11-28) — vendored
unmodified under `upstream/opengrep/`. GNU LGPL 2.1 with the Commons Clause
License Condition v1.0, licensor Semgrep, Inc.; see `upstream/opengrep/LICENSE`.
Internal bundle only: the Commons Clause forbids selling a product or service
whose value derives substantially from these rules.

## MicroHealth rules

`rules/microhealth/`: Copyright (c) MicroHealth, LLC. MIT (see LICENSE).
