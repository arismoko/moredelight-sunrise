#!/usr/bin/env python3
"""Generate More Delight's engine item declarations and creative tab from tools/decl/md_items.toml.in (MD-03).

Knives are FD's `ModItems.knifeItem(material)` (the base port's knife declarations: attack damage 0.5 + material
bonus, attack speed −2.0 (MQ1: DelightLib's own values are never passed), tool rules incorrect-for-material / FD
knife mineable at material speed / instant-mine tag, weapon 1, enchantability and repair tag from the material,
stack 1). Foods are DelightLib `FoodBuilder#build`: `FoodProperties(nutrition, saturationModifier)` (saturation =
nutrition × modifier × 2, in float), `Consumables.defaultFood()` (0.8 s with `fast`), one `apply_effects` per
`withEffect` (MobEffectInstance defaults: particles and icon shown), `bowlFood` = stack 16 + bowl remainder
(FD `ConsumableItem#finishUsingItem` hands it back: `use_remainder`). The tab is DelightAddon's: literal title
"More Delight" (MQ2), icon cooked chicken, items in registration order.

Usage: gen_md_decls.py [--check]
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import target  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
TABLE = REPO / "tools" / "decl" / "md_items.toml.in"
OUT = REPO / "data" / "moredelight" / target.DECL_DIR
NS = "moredelight"

# Vanilla 26.3 ToolMaterial.WOOD / STONE (durability, speed, attack bonus, enchantability, repair tag, incorrect tag).
MATERIALS = {
    "wood": (59, 2.0, 0.0, 15, "#minecraft:wooden_tool_materials", "#minecraft:incorrect_for_wooden_tool"),
    "stone": (131, 4.0, 1.0, 5, "#minecraft:stone_tool_materials", "#minecraft:incorrect_for_stone_tool"),
}


def f32(x: float) -> float:
    """The shortest decimal that is the same Java float."""
    v = struct.unpack("f", struct.pack("f", x))[0]
    for digits in range(1, 10):
        r = round(v, digits)
        if struct.unpack("f", struct.pack("f", r))[0] == v:
            return r
    return v


def knife(material: str) -> dict:
    durability, speed, bonus, enchant, repair, incorrect = MATERIALS[material]
    return {
        "template": "minecraft:stick",
        "max_stack_size": 1,
        "components": {
            "minecraft:max_damage": durability,
            "minecraft:damage": 0,
            "minecraft:enchantable": {"value": enchant},
            "minecraft:repairable": {"items": repair},
            "minecraft:attribute_modifiers": [
                {"type": "minecraft:attack_damage", "id": "minecraft:base_attack_damage", "amount": 0.5 + bonus,
                 "operation": "add_value", "slot": "mainhand"},
                {"type": "minecraft:attack_speed", "id": "minecraft:base_attack_speed", "amount": -2.0,
                 "operation": "add_value", "slot": "mainhand"},
            ],
            "minecraft:tool": {
                "rules": [
                    {"blocks": incorrect, "correct_for_drops": False},
                    {"blocks": "#farmersdelight:mineable/knife", "speed": speed, "correct_for_drops": True},
                    {"blocks": "#farmersdelight:knife_instantly_mines", "speed": 3.4028234663852886e38},
                ],
                "default_mining_speed": 1.0,
                "damage_per_block": 1,
                "can_destroy_blocks_in_creative": False,
            },
            "minecraft:weapon": {"item_damage_per_attack": 1},
        },
    }


def food(row: dict) -> dict:
    sat = f32(f32(row["nutrition"] * f32(row["saturation_modifier"])) * 2.0)
    consumable: dict = {}
    if row.get("fast"):
        consumable["consume_seconds"] = 0.8
    effects = row.get("effects", [])
    if effects:
        consumable["on_consume_effects"] = []
        for e in effects:
            entry = {"type": "minecraft:apply_effects",
                     "effects": [{"id": e["id"], "duration": e["duration"], "amplifier": e["amplifier"]}]}
            if e["chance"] != 1.0:
                entry["probability"] = e["chance"]
            consumable["on_consume_effects"].append(entry)
    out: dict = {"template": "minecraft:stick"}
    if row.get("bowl"):
        out["max_stack_size"] = 16
        out["crafting_remainder"] = "minecraft:bowl"
    out["components"] = {"minecraft:food": {"nutrition": row["nutrition"], "saturation": sat},
                         "minecraft:consumable": consumable}
    if row.get("bowl"):
        out["components"]["minecraft:use_remainder"] = {"id": "minecraft:bowl"}
    return out


def render() -> dict[str, bytes]:
    with TABLE.open("rb") as f:
        table = tomllib.load(f)
    files = {}
    for name, row in table.items():
        decl = knife(row["knife"]) if "knife" in row else food(row)
        files[f"item/{name}.json"] = decl
    files["creative_tab/tab.json"] = {
        "title": "More Delight",
        "icon": "minecraft:cooked_chicken",
        "items": [f"{NS}:{name}" for name in table],
    }
    return {rel: (json.dumps(d, indent=2) + "\n").encode() for rel, d in files.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files = render()
    existing = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*.json")} if OUT.exists() else set()
    if args.check:
        bad = [r for r, b in files.items() if not (OUT / r).exists() or (OUT / r).read_bytes() != b]
        bad += sorted(existing - set(files))
        for r in bad:
            print(f"out of date: {r}", file=sys.stderr)
        if not bad:
            print(f"decl check ok: {len(files)} files")
        return 1 if bad else 0
    for rel in existing - set(files):
        (OUT / rel).unlink()
    for rel, body in files.items():
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
    print(f"wrote {len(files)} declaration file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
