#!/usr/bin/env python3
"""MD-11: lang key audit for More Delight.

Core keys: `item.moredelight.<id>` for every declared item (`data/moredelight/horizon/item/*.json`) and every
translate key in the carried advancements (title and description). en_us.json must have them all (exit 1
otherwise); every locale file must be valid JSON. Prints, per locale, the core keys it lacks (the game then shows
en_us's text, as on Fabric), and `--strict` also fails on those.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANG = ROOT / "assets/moredelight/lang"


def translate_keys(node, out: set) -> None:
    if isinstance(node, dict):
        if isinstance(node.get("translate"), str):
            out.add(node["translate"])
        for v in node.values():
            translate_keys(v, out)
    elif isinstance(node, list):
        for v in node:
            translate_keys(v, out)


def core_keys() -> set:
    keys = {f"item.moredelight.{p.stem}" for p in (ROOT / "data/moredelight/horizon/item").glob("*.json")}
    for p in (ROOT / "data/moredelight/advancement").rglob("*.json"):
        display = json.loads(p.read_text("utf-8")).get("display")
        if display:
            translate_keys({k: display.get(k) for k in ("title", "description")}, keys)
    return keys


def main() -> int:
    strict = "--strict" in sys.argv
    locales = {f.stem: json.loads(f.read_text("utf-8")) for f in sorted(LANG.glob("*.json"))}
    core = core_keys()
    missing_en = sorted(k for k in core if k not in locales["en_us"])
    print(f"{len(locales)} locales, {len(core)} core keys")
    if missing_en:
        print("en_us lacks:", ", ".join(missing_en))
        return 1
    gaps = 0
    for name, table in locales.items():
        lacks = sorted(k for k in core if k not in table)
        gaps += len(lacks)
        if lacks:
            print(f"  {name}: lacks {len(lacks)}: {', '.join(lacks)}")
    print(f"lang ok ({gaps} locale gaps fall back to en_us)")
    return 1 if strict and gaps else 0


if __name__ == "__main__":
    sys.exit(main())
