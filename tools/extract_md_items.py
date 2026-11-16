#!/usr/bin/env python3
"""Read More Delight's item registrations out of MoreDelight.java (MD-03), as plain data, for the declaration table
check (tools/test_md_decls.py) and to write the first table (`--toml`).

Only the DelightLib builder calls MoreDelight.java uses are understood: knife(name, ToolMaterial.X) and
food(name) with nutrition, saturation, fast, bowlFood, withEffect(EFFECT, DURATION, amplifier, chance). Anything
else inside a food or knife chain fails, so a new upstream call cannot be skipped silently. The Java is read as
text (never compiled or run).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EFFECTS = {
    "ModEffects.NOURISHMENT": "farmersdelight:nourishment",
    "MobEffects.REGENERATION": "minecraft:regeneration",
}
DURATIONS = {"FoodValues.MEDIUM_DURATION": 3600}  # FD FoodValues.java:24
MATERIALS = {"ToolMaterial.WOOD": "wood", "ToolMaterial.STONE": "stone"}
KNOWN = {"nutrition", "saturation", "fast", "bowlFood", "withEffect", "attackSpeed", "build"}


def strip_comments(text: str) -> list[tuple[int, str]]:
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("//"):
            continue
        out.append((n, line.split("//", 1)[0]))
    return out


def chains(lines: list[tuple[int, str]]):
    """`addon.<kind>(...)` statements up to `;`, as (line, kind, text)."""
    buf, start, kind = [], None, None
    for n, line in lines:
        if start is None:
            m = re.search(r"\baddon\.(food|knife)\(", line)
            if not m:
                continue
            start, kind, buf = n, m.group(1), []
        buf.append(line.strip())
        if line.rstrip().endswith(";"):
            yield start, kind, " ".join(buf)
            start = None


def parse(text: str) -> list[dict]:
    items = []
    for line, kind, stmt in chains(strip_comments(text)):
        calls = re.findall(r"\.(\w+)\(([^()]*(?:\([^()]*\))?[^()]*)\)", stmt)
        head = re.match(r'addon\.(food|knife)\("([a-z0-9_]+)"(?:,\s*([\w.]+))?\)', stmt)
        if not head:
            raise ValueError(f"line {line}: cannot read {stmt[:60]}")
        item = {"id": head.group(2), "kind": kind, "line": line}
        if kind == "knife":
            item["material"] = MATERIALS[head.group(3)]
        effects = []
        for name, args in calls[1:]:
            if name not in KNOWN:
                raise ValueError(f"line {line}: unknown builder call .{name}()")
            a = [x.strip() for x in args.split(",")] if args.strip() else []
            if name == "nutrition":
                item["nutrition"] = int(a[0])
            elif name == "saturation":
                item["saturation_modifier"] = float(a[0].rstrip("fF"))
            elif name in ("fast", "bowlFood"):
                item[name] = True
            elif name == "withEffect":
                dur = DURATIONS.get(a[1]) or int(a[1])
                effects.append(
                    {"id": EFFECTS[a[0]], "duration": dur, "amplifier": int(a[2]), "chance": float(a[3].rstrip("fF"))}
                )
        if effects:
            item["effects"] = effects
        items.append(item)
    return items


def to_toml(items: list[dict], java_rel: str) -> str:
    out = [
        "# (Named *.toml.in: the Horizon packager refuses .toml files outside src/.)",
        "# More Delight's 33 items as DelightLib builds them (MD-03). Rows in registration order (= creative tab order).",
        "# Values are checked against MoreDelight.java by tools/test_md_decls.py; tools/gen_md_decls.py writes",
        "# data/moredelight/horizon/item/*.json and creative_tab/tab.json. `source` cites the Java line.",
        "",
    ]
    for it in items:
        out.append(f"[{it['id']}]")
        out.append(f'source = "{java_rel}:{it["line"]}"')
        if it["kind"] == "knife":
            out.append(f'knife = "{it["material"]}"')
        else:
            out.append(f"nutrition = {it['nutrition']}")
            out.append(f"saturation_modifier = {it['saturation_modifier']}")
            for flag in ("fast", "bowlFood"):
                if it.get(flag):
                    out.append(f"{'bowl' if flag == 'bowlFood' else 'fast'} = true")
            for e in it.get("effects", []):
                out.append(
                    f'effects = [{{ id = "{e["id"]}", duration = {e["duration"]}, amplifier = {e["amplifier"]}, '
                    f'chance = {e["chance"]} }}]'
                )
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("java", type=Path)
    ap.add_argument("--toml", action="store_true", help="print a decl table")
    args = ap.parse_args()
    items = parse(args.java.read_text("utf-8"))
    if args.toml:
        print(to_toml(items, "MDj/MoreDelight.java"))
    else:
        for it in items:
            print(it)
    return 0


if __name__ == "__main__":
    sys.exit(main())
