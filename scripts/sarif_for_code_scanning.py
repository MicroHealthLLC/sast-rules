#!/usr/bin/env python3
"""Write the copy of a SARIF report that is uploaded to GitHub code scanning.

Opengrep puts a result suppressed in source (a `noopengrep: <rule id>` comment
with its reason) into its SARIF with `suppressions: [{"state": "accepted"}]`.
GitHub code scanning opens an alert for it anyway, so every reviewed and
justified suppression became a failing "new alert" on the pull request that
added its comment, and the only way to clear the check was to dismiss each one
by hand in the UI, where the reason does not live.

The copy for GitHub leaves out the results whose suppression was accepted;
everything else is passed through unchanged. Nothing is lost: the full report
(sast.sarif, with the suppressed results and their state) is still the one
published as the run's artifact, and sast.json is what reaches the results
destination. A suppression whose state is "underReview" or "rejected" is not a
suppression yet, so that result is kept. SARIF 2.1.0 §3.35.3: a suppression
with no "state" is accepted.

Usage: sarif_for_code_scanning.py <in.sarif> <out.sarif>
Prints "<kept> <dropped>".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def is_suppressed(result: dict[str, Any]) -> bool:
    return any(s.get("state", "accepted") == "accepted" for s in result.get("suppressions") or [])


def for_code_scanning(sarif: dict[str, Any]) -> tuple[dict[str, Any], int, int]:
    kept = dropped = 0
    for run in sarif.get("runs") or []:
        results = run.get("results")
        if results is None:
            continue
        keep = [r for r in results if not is_suppressed(r)]
        dropped += len(results) - len(keep)
        kept += len(keep)
        run["results"] = keep
    return sarif, kept, dropped


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[-2], file=sys.stderr)
        return 2
    sarif, kept, dropped = for_code_scanning(json.loads(Path(argv[1]).read_text()))
    Path(argv[2]).write_text(json.dumps(sarif))
    print(f"{kept} {dropped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
