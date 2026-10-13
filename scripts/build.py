#!/usr/bin/env python3
"""Build the rule bundles and the lock file from the vendored sources.

    python3 scripts/build.py           # rewrite dist/ and rules.lock.json
    python3 scripts/build.py --check   # fail if either is not what the sources build

Inputs (all in this repository, nothing is fetched):
  sources.yaml     where each source came from and how its license is read
  licenses.yaml    which license may go in which bundle
  overrides.yaml   rules we turn off, re-grade, or give an allow-list, each
                   with its reason
                   (a source's `categories` keeps all but security rules out)
  upstream/<src>/  vendored upstream rule files, never edited by hand
  rules/<src>/     rules MicroHealth writes

Outputs:
  dist/<bundle>.yaml   one rules file per bundle, every id rewritten to
                       `mh.<source>.<upstream id>` so a moved upstream file or a
                       renamed folder never changes a finding's identity
  dist/SHA256SUMS      what the shared workflow verifies before it scans
  dist/NOTICE.md       the attributions every bundle carries
  rules.lock.json      every rule ever shipped: source, upstream path, license,
                       content hash, bundles, status. A rule that leaves its
                       source is kept as `retired`, never dropped, so a consumer
                       can tell "the rule stopped running" from "the code was
                       fixed" (Tueri Core must not auto-resolve on the former).

The build fails on: an unclassified license, a duplicate id, a rule whose
license is not allowed in a bundle that would contain it, an override with no
reason, or an override naming a rule that does not exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
LOCK = ROOT / "rules.lock.json"
BUNDLES = ("internal", "product")
SKIP_PARTS = {".git", ".github", "stats", "scripts", "qa", "spec", "mappings", "ci", "tests"}

_LICENSE_HEADER = re.compile(r"^#\s*License:\s*(?:License:\s*)?(.+?)\s*$", re.MULTILINE)


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def rule_files(base: Path):
    """Every file under `base` whose YAML is a rules document."""
    for path in sorted(base.rglob("*")):
        if path.suffix not in (".yml", ".yaml") or not path.is_file():
            continue
        rel = path.relative_to(base)
        if (
            SKIP_PARTS & set(rel.parts)
            or ".test." in path.name
            or path.name.startswith(".")
            or rel == Path("template.yaml")  # opengrep-rules' authoring template
        ):
            continue
        try:
            doc = load_yaml(path)
        except yaml.YAMLError:
            continue
        if isinstance(doc, dict) and isinstance(doc.get("rules"), list):
            yield path, rel, doc


def classify(text: str, header_map: dict[str, str]) -> str | None:
    """The license key of one rule file, from its `# License:` header."""
    m = _LICENSE_HEADER.search(text)
    if not m:
        return None
    header = m.group(1)
    for pattern, key in header_map.items():
        if re.search(pattern, header):
            return key
    return None


# GitHub code scanning reads `security-severity` as a CVSS-style number and
# refuses the whole SARIF upload when one rule carries a word ("Low"), which
# GitLab's rules do. A word becomes the midpoint of GitHub's band for it; the
# upstream value is kept beside it, so nothing is lost and the grading is
# visible.
_SEVERITY_SCORE = {"critical": "9.5", "high": "8.0", "medium": "5.5", "low": "2.0", "info": "0.0"}


def _numeric_security_severity(meta: dict) -> None:
    value = meta.get("security-severity")
    if value is None:
        return
    try:
        float(str(value))
        return
    except ValueError:
        pass
    score = _SEVERITY_SCORE.get(str(value).strip().lower())
    meta["mh_upstream_security_severity"] = value
    if score is None:
        del meta["security-severity"]
    else:
        meta["security-severity"] = score


def allow_entries(overrides: dict, ids, errors: list[str]) -> dict[str, list[dict]]:
    """`overrides.yaml` `allow:` → {rule id: [entries]}.

    An entry names rules by id, or by a prefix ending in `*`, and the
    `not-regex` a finding is dropped for when its text overlaps a match.
    Every entry must give its reason and match at least one rule.
    """
    by_rule: dict[str, list[dict]] = {}
    for n, entry in enumerate(overrides.get("allow") or []):
        where = f"overrides.yaml: allow[{n}]"
        if not isinstance(entry, dict):
            errors.append(f"{where} is not a mapping")
            continue
        if not str(entry.get("reason") or "").strip():
            errors.append(f"{where} has no reason")
        regex = entry.get("not-regex")
        if not isinstance(regex, str) or not regex.strip():
            errors.append(f"{where} has no not-regex")
            continue
        try:
            re.compile(regex)
        except re.error as exc:
            errors.append(f"{where}: not-regex does not compile ({exc})")
            continue
        names = entry.get("rules")
        if not isinstance(names, list) or not names:
            errors.append(f"{where} names no rules")
            continue
        for name in names:
            name = str(name)
            hits = [i for i in ids if (i.startswith(name[:-1]) if name.endswith("*") else i == name)]
            if not hits:
                errors.append(f"{where}: {name} names no rule")
            for rid in hits:
                by_rule.setdefault(rid, []).append(entry)
    return by_rule


def apply_allow(rule: dict, entries: list[dict]) -> str | None:
    """Add each entry's `pattern-not-regex` to `rule`. Returns an error, or None.

    Only a search-mode rule can be narrowed this way; a taint rule has no
    single place a not-regex belongs, so asking for one is an error.
    """
    if rule.get("mode", "search") != "search":
        return f"{rule['id']}: allow applies to search-mode rules only"
    nots = [{"pattern-not-regex": e["not-regex"]} for e in entries]
    if "patterns" in rule:
        rule["patterns"] = [*rule["patterns"], *nots]
        return None
    for key in ("pattern", "pattern-regex", "pattern-either"):
        if key in rule:
            rule["patterns"] = [{key: rule.pop(key)}, *nots]
            return None
    return f"{rule['id']}: no pattern to narrow"


def rule_hash(rule: dict) -> str:
    return hashlib.sha256(json.dumps(rule, sort_keys=True).encode()).hexdigest()


def collect(sources: dict, licenses: dict) -> tuple[list[dict], list[str]]:
    rules: list[dict] = []
    errors: list[str] = []
    header_map = licenses.get("headers", {})
    for name, src in sources["sources"].items():
        base = ROOT / src["path"]
        if not base.exists():
            errors.append(f"source {name}: {src['path']} does not exist")
            continue
        for path, rel, doc in rule_files(base):
            if src["license"] == "per-file":
                lic = classify(path.read_text(encoding="utf-8"), header_map)
                if lic is None:
                    errors.append(f"{path.relative_to(ROOT)}: license header not recognised")
                    continue
            else:
                lic = src["license"]
            # The registry's own scheme: folders, file stem, rule id.
            prefix = ".".join((*rel.parent.parts, path.stem)) if src.get("qualify_by_path") else ""
            for rule in doc["rules"]:
                if not isinstance(rule, dict) or "id" not in rule:
                    errors.append(f"{path.relative_to(ROOT)}: a rule without an id")
                    continue
                upstream_id = str(rule["id"])
                local = f"{prefix}.{upstream_id}" if prefix else upstream_id
                category = str((rule.get("metadata") or {}).get("category") or "")
                rules.append(
                    {
                        "category": category,
                        "excluded": (
                            f"category {category or '(none)'}: only "
                            f"{', '.join(src['categories'])} rules are published (sources.yaml)"
                        )
                        if src.get("categories") and category not in src["categories"]
                        else None,
                        "id": f"mh.{name}.{local}",
                        "source": name,
                        "upstream_id": upstream_id,
                        "path": str(path.relative_to(ROOT)),
                        "license": lic,
                        "rule": rule,
                    }
                )
    return rules, errors


def build(check: bool) -> int:
    sources = load_yaml(ROOT / "sources.yaml")
    licenses = load_yaml(ROOT / "licenses.yaml")
    overrides = load_yaml(ROOT / "overrides.yaml")
    allowed = {k: set(v.get("bundles", [])) for k, v in licenses["licenses"].items()}

    rules, errors = collect(sources, licenses)
    seen: dict[str, str] = {}
    for r in rules:
        if r["id"] in seen:
            errors.append(f"duplicate id {r['id']}: {seen[r['id']]} and {r['path']}")
        seen[r["id"]] = r["path"]
        if r["license"] not in allowed:
            errors.append(f"{r['path']}: license {r['license']!r} is not in licenses.yaml")

    disabled = overrides.get("disabled") or {}
    regraded = overrides.get("severity") or {}
    for rid, why in disabled.items():
        if not str(why or "").strip():
            errors.append(f"overrides.yaml: disabled {rid} has no reason")
        if rid not in seen:
            errors.append(f"overrides.yaml: disabled {rid} names no rule")
    for rid, spec in regraded.items():
        if not str((spec or {}).get("reason", "")).strip():
            errors.append(f"overrides.yaml: severity {rid} has no reason")
        if rid not in seen:
            errors.append(f"overrides.yaml: severity {rid} names no rule")
    allow = allow_entries(overrides, seen, errors)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    previous = json.loads(LOCK.read_text()) if LOCK.exists() else {"rules": {}}
    lock_rules: dict[str, dict] = {}
    bundles: dict[str, list[dict]] = {b: [] for b in BUNDLES}
    for r in sorted(rules, key=lambda x: x["id"]):
        rule = dict(r["rule"])
        rule["id"] = r["id"]
        if r["id"] in regraded:
            rule["severity"] = regraded[r["id"]]["to"]
        if r["id"] in allow:
            problem = apply_allow(rule, allow[r["id"]])
            if problem:
                print(f"overrides.yaml: {problem}", file=sys.stderr)
                return 1
        meta = dict(rule.get("metadata") or {})
        _numeric_security_severity(meta)
        meta.update(
            {
                "mh_source": r["source"],
                "mh_upstream_id": r["upstream_id"],
                "mh_license": r["license"],
            }
        )
        rule["metadata"] = meta
        off = r["id"] in disabled or r["excluded"]
        in_bundles = [] if off else sorted(allowed[r["license"]])
        for b in in_bundles:
            bundles[b].append(rule)
        entry = {
            "source": r["source"],
            "upstream_id": r["upstream_id"],
            "path": r["path"],
            "license": r["license"],
            "sha256": rule_hash(rule),
            "bundles": in_bundles,
            "status": "disabled" if r["id"] in disabled else "excluded" if r["excluded"] else "active",
        }
        if r["id"] in disabled:
            entry["reason"] = disabled[r["id"]]
        elif r["excluded"]:
            entry["reason"] = r["excluded"]
        if r["id"] in allow:
            entry["allow"] = [str(e["reason"]).strip() for e in allow[r["id"]]]
        lock_rules[r["id"]] = entry
    for rid, old in previous.get("rules", {}).items():
        if rid not in lock_rules:
            lock_rules[rid] = {**old, "status": "retired", "bundles": []}

    pins = {
        name: {k: src[k] for k in ("url", "ref", "commit") if k in src}
        for name, src in sources["sources"].items()
    }
    notice = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
    outputs: dict[Path, str] = {}
    for b, items in bundles.items():
        licenses_in = sorted({r["metadata"]["mh_license"] for r in items})
        header = (
            f"# sast-rules bundle `{b}` — built by scripts/build.py; do not edit.\n"
            f"# {len(items)} rules. Sources: "
            + ", ".join(f"{n}@{p.get('commit', 'local')[:12]}" for n, p in pins.items())
            + f"\n# Licenses of the rules in this bundle: {', '.join(licenses_in)}.\n"
            "# Each rule's own license is its metadata.mh_license.\n"
            "# MODIFIED from the upstream rules (MicroHealth, LLC): each rule's id is\n"
            "# prefixed `mh.<source>.`, metadata.mh_source / mh_upstream_id / mh_license\n"
            "# are added, a word in metadata.security-severity is replaced by a number\n"
            "# (the original kept as mh_upstream_security_severity), and overrides.yaml\n"
            "# is applied. Nothing else is changed. The date of each change is the date\n"
            "# of the sast-rules commit that built this file; the unmodified upstream\n"
            "# files and the build are in https://github.com/MicroHealthLLC/sast-rules.\n"
            "# Attributions: NOTICE.md; full license texts: licenses/ (both shipped\n"
            "# beside this file).\n"
        )
        body = yaml.safe_dump(
            {"rules": items}, sort_keys=False, allow_unicode=True, width=1_000_000
        )
        outputs[DIST / f"{b}.yaml"] = header + body
    outputs[DIST / "NOTICE.md"] = notice
    # The full text of every license a bundle may carry ships with the bundles.
    for lic in sorted((ROOT / "licenses").glob("*.txt")):
        outputs[DIST / "licenses" / lic.name] = lic.read_text(encoding="utf-8")
    outputs[DIST / "licenses" / "MIT.txt"] = (ROOT / "LICENSE").read_text(encoding="utf-8")
    # ... and each upstream LICENSE file as vendored (the Commons Clause and
    # its licensor are only stated there).
    for lic in sorted((ROOT / "upstream").rglob("LICENSE*")):
        name = "upstream-" + "-".join(lic.relative_to(ROOT / "upstream").parts) + ".txt"
        outputs[DIST / "licenses" / name] = lic.read_text(encoding="utf-8")
    sums = "".join(
        f"{hashlib.sha256(outputs[DIST / f'{b}.yaml'].encode()).hexdigest()}  {b}.yaml\n"
        for b in BUNDLES
    )
    outputs[DIST / "SHA256SUMS"] = sums
    lock = {
        "comment": "Generated by scripts/build.py. Retired and disabled rules stay listed.",
        "sources": pins,
        "bundles": {b: len(items) for b, items in bundles.items()},
        "rules": dict(sorted(lock_rules.items())),
    }
    outputs[LOCK] = json.dumps(lock, indent=1, sort_keys=False) + "\n"

    if check:
        stale = [
            str(p.relative_to(ROOT))
            for p, text in outputs.items()
            if not p.exists() or p.read_text(encoding="utf-8") != text
        ]
        if stale:
            print("Out of date (run python3 scripts/build.py): " + ", ".join(stale), file=sys.stderr)
            return 1
        print("dist/ and rules.lock.json match the sources.")
        return 0
    (DIST / "licenses").mkdir(parents=True, exist_ok=True)
    for p, text in outputs.items():
        p.write_text(text, encoding="utf-8")
    counts = ", ".join(f"{b}={len(items)}" for b, items in bundles.items())
    retired = sum(1 for e in lock_rules.values() if e["status"] == "retired")
    excluded = sum(1 for e in lock_rules.values() if e["status"] == "excluded")
    print(f"Built {counts}; {len(disabled)} disabled, {excluded} excluded, {retired} retired.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    return build(ap.parse_args().check)


if __name__ == "__main__":
    sys.exit(main())
