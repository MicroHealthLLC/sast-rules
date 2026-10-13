#!/usr/bin/env python3
"""One report for one security scan: SAST, Trivy (repository and images), the
SBOMs and ZAP, from the artifacts security-scan.yml's jobs left.

    combine_reports.py <artifacts-dir> <out-dir>

Environment: ENABLED_<SCANNER> (true/false) and RESULT_<SCANNER> (the job's
result: success | failure | cancelled | skipped) for SAST, TRIVY, SBOM, ZAP;
FAIL_ON (none | critical | high | medium | low); the GITHUB_* run variables;
RULES_COMMIT.

Writes <out-dir>/security-report.json and security-report.md, appends the
Markdown to $GITHUB_STEP_SUMMARY, and exits 1 when FAIL_ON is met — or when
a scanner that was switched on did not produce its report, because a scan
that did not run must never read as a clean one. A scanner's counts are null
unless it ran; zero means it ran and found nothing.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")
# The scale Tueri Core maps SAST severities onto (backend/app/parsers/sast.py).
_SAST = {"ERROR": "HIGH", "WARNING": "MEDIUM", "INFO": "LOW"}
_ZAP = {"3": "HIGH", "2": "MEDIUM", "1": "LOW", "0": "UNKNOWN"}
_THRESHOLD = {"critical": 1, "high": 2, "medium": 3, "low": 4}


def _zero() -> dict[str, int]:
    return {s: 0 for s in SEVERITIES}


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _status(name: str, have_report: bool) -> str:
    if os.environ.get(f"ENABLED_{name}", "false") != "true":
        return "disabled"
    if have_report:
        return "ran"
    result = os.environ.get(f"RESULT_{name}", "")
    return "not_run" if result in ("skipped", "cancelled") else "failed"


def sast(art: Path) -> dict:
    report = _load(art / "sast-reports" / "sast.json")
    out: dict = {"status": _status("SAST", isinstance(report, dict)), "findings": None}
    if isinstance(report, dict):
        counts = _zero()
        for r in report.get("results") or []:
            extra = r.get("extra") or {}
            if extra.get("is_ignored"):
                continue
            counts[_SAST.get(str(extra.get("severity", "")).upper(), "UNKNOWN")] += 1
        ruleset = report.get("ruleset") or {}
        out.update(
            findings=counts,
            suppressed_inline=sum(
                1 for r in report.get("results") or [] if (r.get("extra") or {}).get("is_ignored")
            ),
            engine_errors=len(report.get("errors") or []),
            rules=len(ruleset.get("rules_evaluated") or []),
            bundle=ruleset.get("bundle"),
            engine=ruleset.get("engine"),
        )
    return out


def _trivy_counts(report: dict) -> dict[str, dict[str, int]]:
    kinds = {"vulnerabilities": _zero(), "secrets": _zero(), "misconfigurations": _zero()}
    for res in report.get("Results") or []:
        for v in res.get("Vulnerabilities") or []:
            kinds["vulnerabilities"][v.get("Severity", "UNKNOWN") if v.get("Severity") in SEVERITIES else "UNKNOWN"] += 1
        for s in res.get("Secrets") or []:
            kinds["secrets"][s.get("Severity", "UNKNOWN") if s.get("Severity") in SEVERITIES else "UNKNOWN"] += 1
        for m in res.get("Misconfigurations") or []:
            if m.get("Status", "FAIL") == "FAIL":
                kinds["misconfigurations"][m.get("Severity", "UNKNOWN") if m.get("Severity") in SEVERITIES else "UNKNOWN"] += 1
    return kinds


def _target_name(t: dict) -> str:
    """The artifact name trivy.yml gives a target (its `dest` step)."""
    if t.get("kind") == "repo":
        return "repository"
    tail = str(t.get("ref", "")).rsplit("/", 1)[-1]
    tail = re.split(r"[:@]", tail, maxsplit=1)[0]
    return re.sub(r"[^A-Za-z0-9._-]", "-", tail)


def trivy_and_sbom(art: Path) -> tuple[dict, dict]:
    targets, documents = [], []
    for d in sorted(art.glob("trivy-*")):
        name = d.name[len("trivy-") :]
        report = _load(d / ("trivy-fs.json" if name == "repository" else "trivy-image.json"))
        targets.append(
            {
                "target": name,
                "status": "ran" if isinstance(report, dict) else "failed",
                "findings": _trivy_counts(report) if isinstance(report, dict) else None,
            }
        )
        bom = _load(d / "sbom.cdx.json")
        if isinstance(bom, dict):
            documents.append({"target": name, "components": len(bom.get("components") or [])})
    # A planned target that left no artifact at all (its job failed before
    # uploading) is a failed target, never an absent one.
    try:
        planned = json.loads(os.environ.get("TRIVY_TARGETS") or "[]")
    except ValueError:
        planned = []
    seen = {t["target"] for t in targets}
    for t in planned if isinstance(planned, list) else []:
        name = _target_name(t)
        if name not in seen:
            targets.append({"target": name, "status": "failed", "findings": None})
            seen.add(name)
    t_ok = (
        bool(targets)
        and all(t["status"] == "ran" for t in targets)
        and os.environ.get("RESULT_TRIVY", "success") in ("success", "")
    )
    trivy = {"status": _status("TRIVY", t_ok), "targets": targets}
    if trivy["status"] == "failed" and any(t["status"] == "ran" for t in targets):
        trivy["status"] = "partial"
    sbom = {
        "status": "disabled"
        if os.environ.get("ENABLED_SBOM", "false") != "true"
        else ("ran" if documents and len(documents) == len(targets) else "failed" if targets else _status("TRIVY", False)),
        "documents": documents,
    }
    return trivy, sbom


def zap(art: Path) -> dict:
    status_doc = _load(art / "zap-reports" / "zap-status.json") or {}
    report = _load(art / "zap-reports" / "zap.json")
    if os.environ.get("ENABLED_ZAP", "false") != "true":
        return {"status": "disabled", "alerts": None}
    out = {
        "status": status_doc.get("status") or _status("ZAP", isinstance(report, dict)),
        "reason": status_doc.get("reason"),
        "target": status_doc.get("target"),
        "scan": status_doc.get("scan"),
        "alerts": None,
    }
    if isinstance(report, dict) and out["status"] == "ran":
        counts = _zero()
        for site in report.get("site") or []:
            for a in site.get("alerts") or []:
                counts[_ZAP.get(str(a.get("riskcode")), "UNKNOWN")] += 1
        out["alerts"] = counts
    return out


def totals(scanners: dict) -> dict[str, int]:
    t = _zero()
    s = scanners["sast"].get("findings")
    for sev in SEVERITIES:
        t[sev] += (s or {}).get(sev, 0)
        for target in scanners["trivy"]["targets"]:
            for kind in (target.get("findings") or {}).values():
                t[sev] += kind.get(sev, 0)
        t[sev] += (scanners["zap"].get("alerts") or {}).get(sev, 0)
    return t


def markdown(doc: dict) -> str:
    rows = ["### Security scan", "", "| Scanner | Status | Critical | High | Medium | Low |", "|---|---|---|---|---|---|"]

    def row(label: str, status: str, counts: dict | None) -> None:
        c = counts or {}
        cells = [str(c.get(s, "—")) if counts is not None else "—" for s in ("CRITICAL", "HIGH", "MEDIUM", "LOW")]
        rows.append(f"| {label} | **{status}** | " + " | ".join(cells) + " |")

    sc = doc["scanners"]
    row("SAST (Opengrep)", sc["sast"]["status"], sc["sast"].get("findings"))
    for t in sc["trivy"]["targets"]:
        merged = None
        if t.get("findings"):
            merged = _zero()
            for kind in t["findings"].values():
                for k, v in kind.items():
                    merged[k] += v
        row(f"Trivy: {t['target']}", t["status"], merged)
    if not sc["trivy"]["targets"]:
        row("Trivy", sc["trivy"]["status"], None)
    row("ZAP DAST" + (f" ({sc['zap'].get('target')})" if sc["zap"].get("target") else ""), sc["zap"]["status"], sc["zap"].get("alerts"))
    sbom = sc["sbom"]
    rows += ["", f"SBOM: **{sbom['status']}**" + "".join(f" · {d['target']}: {d['components']} components" for d in sbom["documents"])]
    if sc["zap"].get("reason"):
        rows += ["", f"ZAP: {sc['zap']['reason']}"]
    rows += ["", f"Rules: sast-rules `{doc.get('rules_commit', '')[:12]}` · run {doc.get('run_url', '')}", ""]
    return "\n".join(rows)


def main(argv: list[str]) -> int:
    art, out = Path(argv[0]), Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    trivy, sbom = trivy_and_sbom(art)
    scanners = {"sast": sast(art), "trivy": trivy, "sbom": sbom, "zap": zap(art)}
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    doc = {
        "schema": "microhealth.security-scan/1",
        "repository": repo,
        "commit": os.environ.get("SCAN_COMMIT") or os.environ.get("GITHUB_SHA"),
        "branch": os.environ.get("SCAN_BRANCH") or os.environ.get("GITHUB_REF_NAME"),
        "event": os.environ.get("GITHUB_EVENT_NAME"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_url": f"{server}/{repo}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
        "rules_commit": os.environ.get("RULES_COMMIT", ""),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "scanners": scanners,
    }
    doc["totals"] = totals(scanners)
    (out / "security-report.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    md = markdown(doc)
    (out / "security-report.md").write_text(md, encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(md)
    print(md)

    rc = 0
    for name in ("sast", "trivy", "sbom", "zap"):
        if scanners[name]["status"] in ("failed", "partial"):
            print(f"::error::{name} was switched on and did not produce its report.")
            rc = 1
    level = _THRESHOLD.get(os.environ.get("FAIL_ON", "none").lower())
    if level:
        hit = {s: doc["totals"][s] for s in SEVERITIES[:level] if doc["totals"][s]}
        if hit:
            print(f"::error::Findings at or above {os.environ['FAIL_ON']}: {hit}")
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
