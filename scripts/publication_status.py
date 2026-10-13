#!/usr/bin/env python3
"""Record SAST scan and SARIF publication outcomes independently."""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path


def status_from_outcomes(
    scan_outcome: str,
    publication_outcome: str,
    *,
    recorded_at_utc: str | None = None,
) -> dict[str, str]:
    scan_status = {
        "success": "success",
        "failure": "failed",
        "cancelled": "cancelled",
        "skipped": "not_run",
    }.get(scan_outcome, "unknown")
    publication_status = "published" if publication_outcome == "success" else "degraded"
    return {
        "scan_status": scan_status,
        "scan_step_outcome": scan_outcome,
        "sarif_publication_status": publication_status,
        "sarif_upload_step_outcome": publication_outcome,
        "recorded_at_utc": recorded_at_utc
        or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def summary_for_status(status: dict[str, str], run_url: str) -> str:
    publication = status["sarif_publication_status"].upper()
    scan = status["scan_status"].upper()
    lines = [
        "### SAST status",
        "",
        "| Control | Result |",
        "| --- | --- |",
        f"| Scan execution | **{scan}** (`{status['scan_step_outcome']}`) |",
        (
            f"| GitHub SARIF publication | **{publication}** "
            + f"(`{status['sarif_upload_step_outcome']}`) |"
        ),
        f"| Recorded (UTC) | `{status['recorded_at_utc']}` |",
        f"| Workflow run | {run_url} |",
        "",
    ]
    if publication == "DEGRADED":
        lines.extend(
            [
                "::warning::SARIF publication was not confirmed. "
                + "The scan result is reported separately; inspect the upload step "
                + "for Code Security, token-permission, licensing, or fork restrictions.",
                "",
            ]
        )
    if scan != "SUCCESS":
        lines.extend(
            [
                "::error::The SAST scan did not succeed. SARIF publication status "
                + "does not change the scanner outcome.",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    status = status_from_outcomes(
        os.environ["SCAN_OUTCOME"],
        os.environ["SARIF_UPLOAD_OUTCOME"],
    )
    status.update(
        {
            "repository": os.environ["GITHUB_REPOSITORY"],
            "commit": os.environ["GITHUB_SHA"],
            "ref": os.environ["GITHUB_REF"],
            "run_id": os.environ["GITHUB_RUN_ID"],
            "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        }
    )
    Path("publication-status.json").write_text(
        json.dumps(status, indent=2) + "\n",
        encoding="utf-8",
    )
    run_url = (
        f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}"
        f"/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    )
    summary = summary_for_status(status, run_url)
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
        stream.write(summary)
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
        stream.write(f"sarif_publication_status={status['sarif_publication_status']}\n")
        stream.write(f"recorded_at_utc={status['recorded_at_utc']}\n")
    print(summary, end="")


if __name__ == "__main__":
    main()
