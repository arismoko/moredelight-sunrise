#!/usr/bin/env python3
"""MD-03 checks: the declaration table equals what MoreDelight.java registers (MD checkout: $MD_SRC or
../sources/MoreDelight), and the generated declarations carry the expected values."""
import json
import os
import sys
import tomllib
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import extract_md_items  # noqa: E402
import gen_md_decls  # noqa: E402

MD = Path(os.environ.get("MD_SRC", HERE.parent.parent / "sources" / "MoreDelight"))
JAVA = MD / "src/main/java/com/axperty/moredelight/MoreDelight.java"


class TableMatchesJava(unittest.TestCase):
    def test_rows(self):
        with gen_md_decls.TABLE.open("rb") as f:
            table = tomllib.load(f)
        java = extract_md_items.parse(JAVA.read_text("utf-8"))
        self.assertEqual(list(table), [i["id"] for i in java])
        for it in java:
            row = table[it["id"]]
            self.assertEqual(row["source"], f"MDj/MoreDelight.java:{it['line']}")
            if it["kind"] == "knife":
                self.assertEqual(row["knife"], it["material"])
                continue
            self.assertEqual(row["nutrition"], it["nutrition"])
            self.assertEqual(row["saturation_modifier"], it["saturation_modifier"])
            self.assertEqual(row.get("fast", False), it.get("fast", False))
            self.assertEqual(row.get("bowl", False), it.get("bowlFood", False))
            self.assertEqual(row.get("effects", []), it.get("effects", []))


class GeneratedValues(unittest.TestCase):
    def setUp(self):
        self.files = {k: json.loads(v) for k, v in gen_md_decls.render().items()}

    def test_counts_and_tab(self):
        self.assertEqual(len([k for k in self.files if k.startswith("item/")]), 33)
        tab = self.files["creative_tab/tab.json"]
        self.assertEqual(tab["title"], "More Delight")  # MQ2: literal
        self.assertEqual(tab["items"][:3], ["moredelight:wooden_knife", "moredelight:stone_knife",
                                            "moredelight:diced_potatoes"])

    def test_knives(self):
        for name, durability, damage, speed in (("wooden_knife", 59, 0.5, 2.0), ("stone_knife", 131, 1.5, 4.0)):
            c = self.files[f"item/{name}.json"]["components"]
            self.assertEqual(c["minecraft:max_damage"], durability)
            self.assertEqual(c["minecraft:attribute_modifiers"][0]["amount"], damage)
            self.assertEqual(c["minecraft:attribute_modifiers"][1]["amount"], -2.0)
            self.assertEqual(c["minecraft:tool"]["rules"][1]["speed"], speed)
            self.assertEqual(self.files[f"item/{name}.json"]["max_stack_size"], 1)

    def test_foods(self):
        rice = self.files["item/cooked_rice_with_chicken_cuts.json"]
        self.assertEqual(rice["components"]["minecraft:food"], {"nutrition": 14, "saturation": 22.4})
        self.assertEqual(rice["max_stack_size"], 16)
        self.assertEqual(rice["components"]["minecraft:use_remainder"], {"id": "minecraft:bowl"})
        eff = rice["components"]["minecraft:consumable"]["on_consume_effects"][0]["effects"][0]
        self.assertEqual((eff["id"], eff["duration"]), ("farmersdelight:nourishment", 3600))
        self.assertEqual(self.files["item/toast.json"]["components"]["minecraft:consumable"], {"consume_seconds": 0.8})
        self.assertEqual(self.files["item/chocolate_popsicle.json"]["components"]["minecraft:consumable"], {})  # MQ5


if __name__ == "__main__":
    unittest.main()
