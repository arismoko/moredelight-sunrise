#!/usr/bin/env python3
"""Fixtures for recipe_overlap.py: conflicts are found, near-misses are not."""
import io
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import recipe_overlap  # noqa: E402


def write(root: Path, rel: str, doc):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc))


def shapeless(ings, result, count=1):
    return {"type": "minecraft:crafting_shapeless", "ingredients": ings, "result": {"id": result, "count": count}}


class OverlapTest(unittest.TestCase):
    def run_report(self, addon_recipes: dict, base_recipes: dict = None):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            jar = t / "client.jar"
            with zipfile.ZipFile(jar, "w") as z:
                z.writestr("data/minecraft/tags/item/planks.json",
                           json.dumps({"values": ["minecraft:oak_planks", "minecraft:birch_planks"]}))
                z.writestr("data/minecraft/recipe/stick.json", json.dumps({
                    "type": "minecraft:crafting_shaped", "pattern": ["#", "#"],
                    "key": {"#": "#minecraft:planks"}, "result": {"id": "minecraft:stick", "count": 4}}))
            base, addon = t / "base", t / "addon"
            write(base, "data/c/tags/item/bread_slices.json", {"values": ["test:slice"]})
            (base / "tools/addon_overlays").mkdir(parents=True)
            for rid, doc in (base_recipes or {}).items():
                ns, path = rid.split(":")
                write(base, f"data/{ns}/recipe/{path}.json", doc)
            write(addon, "data/c/tags/item/bread_slices.json", {"values": ["test:toast"]})
            for rid, doc in addon_recipes.items():
                ns, path = rid.split(":")
                write(addon, f"data/{ns}/recipe/{path}.json", doc)
            out = io.StringIO()
            with redirect_stdout(out):
                code = recipe_overlap.main(["--base", str(base), "--vanilla", str(jar),
                                            "--addon", str(addon), "--json"])
            return code, json.loads(out.getvalue())

    def test_shaped_conflict_with_vanilla_via_tag(self):
        code, r = self.run_report({"md:fake": {
            "type": "minecraft:crafting_shaped", "pattern": ["A", "A"],
            "key": {"A": "minecraft:birch_planks"}, "result": {"id": "md:thing"}}})
        self.assertEqual(code, 1)
        self.assertEqual(r["addon_conflicts"], 1)

    def test_shapeless_vs_shaped_multiset_conflict(self):
        code, r = self.run_report({"md:fake": shapeless(["minecraft:oak_planks", "#minecraft:planks"], "md:x")})
        self.assertEqual(code, 1)

    def test_merged_tag_and_counts(self):
        # toast joins c:bread_slices from the addon; 2 slices + tomato vs base 1 slice + tomato: no overlap.
        base = {"fd:one": shapeless(["#c:bread_slices", "test:tomato"], "fd:a")}
        code, r = self.run_report({"md:two": shapeless(["test:toast", "test:toast", "test:tomato"], "md:b")}, base)
        self.assertEqual((code, r["addon_overlaps"]), (0, []))
        code, r = self.run_report({"md:one": shapeless(["test:toast", "test:tomato"], "md:b")}, base)
        self.assertEqual(code, 1)

    def test_same_result_is_not_a_conflict(self):
        base = {"fd:a": shapeless(["test:x"], "fd:a")}
        code, r = self.run_report({"md:a": shapeless(["test:x"], "fd:a")}, base)
        self.assertEqual(code, 0)
        self.assertTrue(r["addon_overlaps"][0]["same_result"])

    def test_cutting_needs_tool_overlap(self):
        def cut(tool, result):
            return {"type": "farmersdelight:cutting", "ingredients": ["test:log"], "tool": tool,
                    "result": [{"item": {"id": result}}]}
        base = {"fd:cut": cut({"fabric:type": "farmersdelight:item_ability", "action": "axe_strip"}, "fd:bark")}
        code, _ = self.run_report({"md:cut": cut("#c:tools/knife", "md:x")}, base)
        self.assertEqual(code, 0)
        code, _ = self.run_report({"md:cut": cut({"fabric:type": "fabric:any", "ingredients": [
            {"fabric:type": "farmersdelight:item_ability", "action": "axe_strip"}]}, "md:x")}, base)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
