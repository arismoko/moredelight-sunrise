#!/usr/bin/env python3
"""Deterministically carry More Delight's data and assets into this repo (ADDONS_PLAN §5.4, MD-02).

Usage:
  carry_md.py --md <MoreDelight checkout> --base <farmersdelight-horizon checkout> --vanilla <client jar>
  carry_md.py ... --check          # verify the repo matches (CI)
  carry_md.py ... --out <dir>      # write into another tree

Rules (tools/carry_rules_md.toml.in): R1 copy MD's own namespace and `c` tags byte for byte; R2 exclude
integrations; R3 MD's FD-namespace knives tag becomes an overlay entry; R4 MD's bacon-sandwich override ships under
a moredelight id (MA1); R5 MD's craft_knife override is dropped (MA2); R6 every food gets an effect-tooltip overlay
entry; R8 every knife gets a `ported_farmersdelight:knife_items` overlay entry (MD-09); R7 every tag the output references must be defined by vanilla 26.3, the base or the output. Every source
file must match exactly one rule. The overlay goes to tools/overlay/moredelight.json, for the base carry (BX-02).
The base's carry_lib.py is imported from the --base checkout, which must be at the pinned commit.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
import tempfile
import tomllib
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / "tools" / "carry_rules_md.toml.in"
MANIFEST_REL = "tools/carry_manifest.json"
OVERLAY_REL = "tools/overlay/moredelight.json"
OWNED = {"moredelight"}
lib = None  # carry_lib from the base checkout


def load_lib(base: Path, pinned: str):
    global lib
    sys.path.insert(0, str(base / "tools"))
    import carry_lib  # noqa: E402

    lib = carry_lib
    head = lib.git_head(base)
    if head != pinned:
        raise SystemExit(f"base checkout is at {head}, rules pin {pinned}")


def food_ids(java: str) -> list[str]:
    """`addon.food("x")` calls in MoreDelight.java, skipping commented-out lines (three are, for 26.3)."""
    ids = []
    for line in java.splitlines():
        if line.lstrip().startswith("//"):
            continue
        ids += re.findall(r'\baddon\.food\("([a-z0-9_]+)"\)', line)
    return [f"moredelight:{i}" for i in ids]


def knife_ids(java: str) -> list[str]:
    """`addon.knife("x", ...)` calls in MoreDelight.java: DelightLib's KnifeBuilder builds `new KnifeItem` (FD's class)."""
    ids = []
    for line in java.splitlines():
        if line.lstrip().startswith("//"):
            continue
        ids += re.findall(r'\baddon\.knife\("([a-z0-9_]+)"', line)
    return [f"moredelight:{i}" for i in ids]


def classify(rel: str, rules: dict) -> tuple[str, dict | None]:
    hits = []
    for r in rules.get("relocate", []):
        if rel == r["from"]:
            hits.append(("relocate", r))
    for r in rules.get("drop", []):
        if rel == r["path"]:
            hits.append(("drop", r))
    for r in rules.get("overlay_tag", []):
        if rel == r["path"]:
            hits.append(("overlay", r))
    if any(fnmatch.fnmatchcase(rel, p) for p in rules["exclude"]["patterns"]):
        hits.append(("exclude", None))
    if any(rel.startswith(p) for p in rules["copy"]["include_prefixes"]):
        hits.append(("copy", None))
    if len(hits) != 1:
        raise lib.CarryError(f"{rel}: matches {[h[0] for h in hits] or 'no'} rule(s); exactly one expected")
    return hits[0]


def source_of(rules: dict, md: Path, rel_in_repo: str) -> dict:
    return {
        "repo": rules["source"]["repo"],
        "commit": rules["source"]["sha"],
        "file": rel_in_repo,
        "sha256": lib.sha256((md / rel_in_repo).read_bytes()),
    }


def carry(md: Path, out: Path, rules: dict, base: Path, vanilla: Path) -> tuple[dict, list[str]]:
    files = lib.collect(md, rules["source"]["roots"], [""], [])
    entries, log, overlay_entries = [], [], []

    def emit(dest: str, data: bytes, src: str, src_data: bytes, rule: str):
        p = out / dest
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.read_bytes() != data:
            p.write_bytes(data)
        entries.append(
            {
                "source": src,
                "dest": dest,
                "sha256_source": lib.sha256(src_data),
                "sha256_dest": lib.sha256(data),
                "rule": rule,
            }
        )

    for rel in sorted(files):
        root, path = files[rel]
        data = path.read_bytes()
        kind, rule = classify(rel, rules)
        src = f"{root}/{rel}"
        if kind == "copy":
            emit(rel, data, src, data, "copy")
        elif kind == "relocate":
            emit(rule["to"], data, src, data, "relocate")
            log.append(f"relocated {rel} -> {rule['to']} (MA1)")
        elif kind == "drop":
            log.append(f"dropped {rel} ({rule['delta']})")
        elif kind == "overlay":
            ids = [v if isinstance(v, str) else v["id"] for v in json.loads(data)["values"]]
            overlay_entries.append(
                {"tag": rule["tag"], "kind": rule["kind"], "ids": ids, "source": source_of(rules, md, src)}
            )
            log.append(f"overlay {rel} -> {rule['tag']} ({len(ids)} ids)")
        for c in rules.get("copy_as", []):
            if rel == c["from"]:
                emit(c["to"], data, src, data, "copy_as")

    et = rules["effect_tooltip"]
    foods = food_ids((md / et["java"]).read_text("utf-8"))
    overlay_entries.append(
        {"tag": et["tag"], "kind": et["kind"], "ids": foods, "source": source_of(rules, md, et["java"])}
    )
    ki = rules["knife_items"]
    knives = knife_ids((md / ki["java"]).read_text("utf-8"))
    overlay_entries.append(
        {"tag": ki["tag"], "kind": ki["kind"], "ids": knives, "source": source_of(rules, md, ki["java"])}
    )
    overlay = {
        "addon": "moredelight",
        "note": "Generated by moredelight-horizon tools/carry_md.py; copy into the base's tools/addon_overlays/.",
        "entries": overlay_entries,
    }
    overlay_bytes = (json.dumps(overlay, indent=2) + "\n").encode("utf-8")
    p = out / OVERLAY_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(overlay_bytes)

    dests = [e["dest"] for e in entries]
    bad = lib.fence_violations(dests, OWNED)
    if bad:
        raise lib.CarryError(f"outside the namespace fence: {bad}")
    # R7: the tag universe is vanilla 26.3 + the base + this output.
    defined = lib.tags_in_zip(vanilla) | lib.tags_in_tree(base) | lib.tags_in_rels(dests)
    refs = {}
    for d in dests:
        if d.startswith("data/") and d.endswith(".json"):
            r = lib.tag_references(json.loads((out / d).read_text("utf-8")))
            if r:
                refs[d] = r
    missing = lib.undefined_tags(refs, defined)
    if missing:
        raise lib.CarryError(f"undefined tags: {missing}")

    manifest = {
        "md_repo": rules["source"]["repo"],
        "md_sha": rules["source"]["sha"],
        "base_sha": rules["base"]["sha"],
        "rules_sha256": lib.sha256(RULES.read_bytes()),
        "overlay_sha256": lib.sha256(overlay_bytes),
        "log": log,
        "files": sorted(entries, key=lambda e: e["dest"]),
    }
    return manifest, log


def counts(manifest: dict) -> list[tuple[str, int]]:
    c: Counter[str] = Counter()
    for e in manifest["files"]:
        d = e["dest"]
        for prefix, name in (
            ("assets/moredelight/items/", "item definitions"),
            ("assets/moredelight/models/", "models"),
            ("assets/moredelight/textures/", "textures"),
            ("assets/moredelight/lang/", "lang"),
            ("data/moredelight/recipe/", "recipes"),
            ("data/moredelight/advancement/", "advancements"),
            ("data/c/tags/", "c tag files"),
        ):
            if d.startswith(prefix):
                c[name] += 1
        c[f"rule {e['rule']}"] += 1
    c["total files"] = len(manifest["files"])
    return sorted(c.items())


def check(args, rules) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        manifest, _ = carry(args.md, t, rules, args.base, args.vanilla)
        lib.write_manifest(t / MANIFEST_REL, manifest)
        problems = []
        for rel in (MANIFEST_REL, OVERLAY_REL):
            if not (REPO / rel).exists() or (REPO / rel).read_bytes() != (t / rel).read_bytes():
                problems.append(f"{rel} differs")
        for e in manifest["files"]:
            ours = REPO / e["dest"]
            if not ours.exists():
                problems.append(f"missing {e['dest']}")
            elif lib.sha256(ours.read_bytes()) != e["sha256_dest"]:
                problems.append(f"drift {e['dest']}")
    for p in problems[:50]:
        print(p, file=sys.stderr)
    if problems:
        print(f"carry check FAILED: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(f"carry check ok: {len(manifest['files'])} files")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--md", required=True, type=Path)
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--vanilla", required=True, type=Path, help="minecraft 26.3 client jar (read as a zip)")
    ap.add_argument("--out", type=Path, default=REPO)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    with RULES.open("rb") as f:
        rules = tomllib.load(f)
    load_lib(args.base, rules["base"]["sha"])
    head = lib.git_head(args.md)
    if head != rules["source"]["sha"]:
        print(f"More Delight checkout is at {head}, rules pin {rules['source']['sha']}", file=sys.stderr)
        return 2
    try:
        if args.check:
            return check(args, rules)
        old = lib.read_manifest(args.out / MANIFEST_REL)
        manifest, log = carry(args.md, args.out, rules, args.base, args.vanilla)
        stale = lib.remove_stale(args.out, old, manifest)
        lib.write_manifest(args.out / MANIFEST_REL, manifest)
    except lib.CarryError as e:
        print(f"carry FAILED: {e}", file=sys.stderr)
        return 1
    for line in log:
        print(line)
    for name, n in counts(manifest):
        print(f"{name:22} {n}")
    if stale:
        print(f"removed {len(stale)} stale file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
