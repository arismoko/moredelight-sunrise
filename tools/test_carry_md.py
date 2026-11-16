#!/usr/bin/env python3
"""Unit tests for tools/carry_md.py on a fixture tree (needs the base checkout for carry_lib: --base or ../farmersdelight-horizon)."""
import json
import os
import sys
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import carry_md  # noqa: E402

BASE = Path(os.environ.get("FD_BASE", HERE.parent.parent / "farmersdelight-horizon"))
sys.path.insert(0, str(BASE / "tools"))
import carry_lib  # noqa: E402

carry_md.lib = carry_lib
with carry_md.RULES.open("rb") as f:
    RULES = tomllib.load(f)


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, "utf-8")


JAVA = """
        addon.food("diced_potatoes")
        // addon.food("hamburger_with_cheese")
        addon.knife("wooden_knife", ToolMaterial.WOOD)
        // addon.knife("bone_knife", ToolMaterial.WOOD)
        addon.food("toast").fast()
"""


class CarryMdTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.md, self.out, self.base = t / "md", t / "out", t / "base"
        gen, main = "src/main/generated/", "src/main/resources/"
        write(self.md, gen + "data/moredelight/recipe/toast.json", '{"ingredients":["#c:eggs"]}')
        write(self.md, gen + "data/farmersdelight/tags/item/tools/knives.json", '{"values":["moredelight:stone_knife"]}')
        write(self.md, main + "data/farmersdelight/recipe/bacon_sandwich.json", '{"x":1}')
        write(self.md, main + "data/farmersdelight/advancement/main/craft_knife.json", "{}")
        write(self.md, main + "data/create/cutting/x.json", "{}")
        write(self.md, main + "assets/moredelight/logo.png", "png")
        write(self.md, main + "fabric.mod.json", "{}")
        write(self.md, RULES["effect_tooltip"]["java"], JAVA)
        write(self.base, "data/c/tags/item/eggs.json", '{"values":[]}')
        self.jar = t / "v.jar"
        with zipfile.ZipFile(self.jar, "w") as z:
            z.writestr("data/minecraft/tags/item/planks.json", "{}")

    def tearDown(self):
        self.tmp.cleanup()

    def test_rules(self):
        m, log = carry_md.carry(self.md, self.out, RULES, self.base, self.jar)
        dests = {e["dest"]: e["rule"] for e in m["files"]}
        self.assertEqual(
            dests,
            {
                "assets/moredelight/logo.png": "copy",
                "icon.png": "copy_as",
                "data/moredelight/recipe/toast.json": "copy",
                "data/moredelight/recipe/bacon_sandwich_from_bread_slices.json": "relocate",
            },
        )
        self.assertEqual(
            (self.out / "data/moredelight/recipe/bacon_sandwich_from_bread_slices.json").read_text(), '{"x":1}'
        )
        overlay = json.loads((self.out / carry_md.OVERLAY_REL).read_text())
        self.assertEqual(
            [(e["tag"], e["ids"]) for e in overlay["entries"]],
            [
                ("farmersdelight:tools/knives", ["moredelight:stone_knife"]),
                ("ported_farmersdelight:effect_tooltip", ["moredelight:diced_potatoes", "moredelight:toast"]),
                ("ported_farmersdelight:knife_items", ["moredelight:wooden_knife"]),
            ],
        )
        self.assertTrue(any("MA2" in line for line in log))

    def test_unruled_file_fails(self):
        write(self.md, "src/main/resources/data/minecraft/recipe/bread.json", "{}")
        with self.assertRaises(carry_lib.CarryError):
            carry_md.carry(self.md, self.out, RULES, self.base, self.jar)

    def test_undefined_tag_fails(self):
        write(self.md, "src/main/generated/data/moredelight/recipe/x.json", '{"ingredients":["#c:nothing"]}')
        with self.assertRaises(carry_lib.CarryError):
            carry_md.carry(self.md, self.out, RULES, self.base, self.jar)


if __name__ == "__main__":
    unittest.main()
