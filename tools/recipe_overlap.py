#!/usr/bin/env python3
"""Recipe conflict / ambiguity report (ADDONS_VALIDATION §2.3, MD-07).

Loads vanilla 26.3 (client jar), the base's carried data + add-on tag overlays, and this add-on's
data; resolves item tags; then reports recipe pairs one input could satisfy at once:
  - crafting (shapeless, shaped, transmute; across kinds): a common grid exists. Shapeless and
    transmute are compared as multisets (bipartite matching of non-disjoint ingredients); a
    shaped recipe against a shaped one needs equal trimmed size and per-cell overlap (mirror too);
    shaped against shapeless compares the shaped cells as a multiset (a necessary condition).
  - farmersdelight:cooking: same ingredient count and a bipartite matching.
  - farmersdelight:cutting: overlapping input and overlapping tool (item_ability tools compare
    by ability name, so a knife tag and an ability never overlap: conservative).
  - smelting / smoking / blasting / campfire_cooking: same type and overlapping input.
Only pairs with at least one recipe from the add-on are judged; base-only pairs are counted.

Usage: recipe_overlap.py --base <farmersdelight-horizon> --vanilla <client jar> [--addon .] [--json]
Exit 1 if a pair with different results involves the add-on.
"""
import argparse
import json
import sys
import zipfile
from pathlib import Path

ITEM_TAG_DIRS = ("tags/item/", "tags/items/")


def tag_name(path: str):
    """'data/ns/tags/item/a/b.json' -> 'ns:a/b'."""
    parts = path.split("/")
    if len(parts) < 5 or parts[0] != "data" or parts[2] != "tags" or parts[3] not in ("item", "items"):
        return None
    return f"{parts[1]}:{'/'.join(parts[4:])[:-5]}"


def recipe_id(path: str):
    parts = path.split("/")
    if len(parts) < 4 or parts[0] != "data" or parts[2] != "recipe" or not path.endswith(".json"):
        return None
    return f"{parts[1]}:{'/'.join(parts[3:])[:-5]}"


def tree_files(root: Path):
    for p in sorted((root / "data").rglob("*.json")):
        yield p.relative_to(root).as_posix(), p.read_bytes()


def jar_files(jar: Path):
    with zipfile.ZipFile(jar) as z:
        for n in sorted(z.namelist()):
            if n.startswith("data/") and n.endswith(".json"):
                yield n, z.read(n)


class World:
    def __init__(self):
        self.tags: dict[str, list] = {}
        self.recipes: dict[str, tuple[str, dict]] = {}  # id -> (source, json)

    def add(self, source: str, files):
        for rel, data in files:
            t = tag_name(rel)
            if t:
                doc = json.loads(data)
                if doc.get("replace"):
                    self.tags[t] = []
                self.tags.setdefault(t, []).extend(doc.get("values", []))
                continue
            r = recipe_id(rel)
            if r:
                self.recipes[r] = (source, json.loads(data))

    def add_overlay(self, overlay: Path):
        doc = json.loads(overlay.read_text())
        for e in doc.get("entries", []):
            if e.get("kind") == "item":
                self.tags.setdefault(e["tag"], []).extend(e["ids"])

    def resolve_tag(self, name: str, seen=None) -> frozenset:
        seen = seen or set()
        if name in seen:
            return frozenset()
        seen.add(name)
        out = set()
        for v in self.tags.get(name, []):
            ref = v["id"] if isinstance(v, dict) else v
            if ref.startswith("#"):
                out |= self.resolve_tag(ref[1:], seen)
            else:
                out.add(ref)
        return frozenset(out)

    def ingredient(self, node) -> frozenset:
        """Set of item ids the ingredient accepts; raises ValueError on an unknown form."""
        if isinstance(node, str):
            return self.resolve_tag(node[1:]) if node.startswith("#") else frozenset([node])
        if isinstance(node, list):
            return frozenset().union(*(self.ingredient(n) for n in node)) if node else frozenset()
        if isinstance(node, dict):
            kind = node.get("fabric:type") or node.get("type")
            if kind == "farmersdelight:item_ability":
                return frozenset(["ability:" + node["action"]])
            if kind == "fabric:any":
                return frozenset().union(*(self.ingredient(n) for n in node["ingredients"]))
            if "item" in node:
                return frozenset([node["item"]])
            if "tag" in node:
                return self.resolve_tag(node["tag"])
            raise ValueError(f"ingredient form {kind or sorted(node)}")
        raise ValueError(f"ingredient {node!r}")


def perfect_matching(a: list, b: list) -> bool:
    if len(a) != len(b):
        return False
    match = [-1] * len(b)

    def augment(i, seen):
        for j in range(len(b)):
            if j not in seen and a[i] & b[j]:
                seen.add(j)
                if match[j] < 0 or augment(match[j], seen):
                    match[j] = i
                    return True
        return False

    return all(augment(i, set()) for i in range(len(a)))


def trim(pattern: list[str]) -> list[str]:
    rows = [r for r in pattern if r.strip()]
    if not rows:
        return []
    left = min(len(r) - len(r.lstrip()) for r in rows)
    width = max(len(r.rstrip()) for r in rows)
    return [r.ljust(width)[left:width] for r in rows]


def result_of(doc: dict):
    r = doc.get("result")
    if isinstance(r, str):
        return (r, 1)
    if isinstance(r, dict):
        if isinstance(r.get("item"), dict):  # cutting: {"item": {...}, "chance": ...}
            return result_of({"result": r["item"]}) + (r.get("chance", 1.0),)
        return (r.get("id") or r.get("item"), r.get("count", 1))
    if isinstance(r, list):  # cutting: several results
        return tuple(result_of({"result": x}) for x in r)
    return (None, None)


class Entry:
    def __init__(self, rid, source, kind, doc, w: World):
        self.id, self.source, self.kind, self.doc = rid, source, kind, doc
        self.result = result_of(doc)
        self.grid = None
        if kind == "shaped":
            pat = trim(doc["pattern"])
            key = {k: w.ingredient(v) for k, v in doc["key"].items()}
            self.grid = [[key[c] if c != " " else None for c in row] for row in pat]
            self.multiset = [c for row in self.grid for c in row if c is not None]
        elif kind == "shapeless":
            self.multiset = [w.ingredient(i) for i in doc["ingredients"]]
        elif kind == "transmute":
            self.multiset = [w.ingredient(doc["input"]), w.ingredient(doc["material"])]
        elif kind == "cooking_pot":
            self.multiset = [w.ingredient(i) for i in doc["ingredients"]]
        elif kind == "cutting":
            self.input = w.ingredient(doc["ingredients"][0] if "ingredients" in doc else doc["ingredient"])
            self.tool = w.ingredient(doc["tool"])
        else:  # furnace family
            self.input = w.ingredient(doc["ingredient"])


KINDS = {
    "minecraft:crafting_shaped": "shaped",
    "minecraft:crafting_shapeless": "shapeless",
    "minecraft:crafting_transmute": "transmute",
    "farmersdelight:cooking": "cooking_pot",
    "farmersdelight:cutting": "cutting",
    "minecraft:smelting": "smelting",
    "minecraft:smoking": "smoking",
    "minecraft:blasting": "blasting",
    "minecraft:campfire_cooking": "campfire_cooking",
}
CRAFTING = {"shaped", "shapeless", "transmute"}


def shaped_overlap(a: Entry, b: Entry) -> bool:
    ga, gb = a.grid, b.grid
    if len(ga) != len(gb) or len(ga[0]) != len(gb[0]):
        return False
    for mirror in (False, True):
        ok = True
        for ra, rb in zip(ga, gb):
            rb = rb[::-1] if mirror else rb
            for ca, cb in zip(ra, rb):
                if (ca is None) != (cb is None) or (ca is not None and not ca & cb):
                    ok = False
                    break
            if not ok:
                break
        if ok:
            return True
    return False


def overlaps(a: Entry, b: Entry) -> bool:
    if a.kind in CRAFTING and b.kind in CRAFTING:
        if a.kind == "shaped" and b.kind == "shaped":
            return shaped_overlap(a, b)
        return perfect_matching(a.multiset, b.multiset)
    if a.kind != b.kind:
        return False
    if a.kind == "cooking_pot":
        return perfect_matching(a.multiset, b.multiset)
    if a.kind == "cutting":
        return bool(a.input & b.input) and bool(a.tool & b.tool)
    return bool(a.input & b.input)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--vanilla", type=Path, required=True)
    ap.add_argument("--addon", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    w = World()
    w.add("vanilla", jar_files(args.vanilla))
    w.add("base", tree_files(args.base))
    for ov in sorted((args.base / "tools/addon_overlays").glob("*.json")):
        w.add_overlay(ov)
    w.add("addon", tree_files(args.addon))

    entries, skipped = [], []
    for rid, (source, doc) in sorted(w.recipes.items()):
        kind = KINDS.get(doc.get("type"))
        if not kind:
            continue
        try:
            entries.append(Entry(rid, source, kind, doc, w))
        except (ValueError, KeyError) as e:
            skipped.append((rid, source, str(e)))

    groups: dict[str, list[Entry]] = {}
    for e in entries:
        groups.setdefault("crafting" if e.kind in CRAFTING else e.kind, []).append(e)

    addon_hits, base_pairs = [], []
    for group in groups.values():
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if not overlaps(a, b):
                    continue
                if "addon" in (a.source, b.source):
                    addon_hits.append((a, b))
                else:
                    base_pairs.append((a.id, b.id))
    base_hits = len(base_pairs)

    addon_recipes = [e for e in entries if e.source == "addon"]
    conflicts = [(a, b) for a, b in addon_hits if a.result != b.result]
    report = {
        "recipes": len(entries),
        "addon_recipes": len(addon_recipes),
        "skipped_ingredient_forms": [{"id": r, "source": s, "why": y} for r, s, y in skipped],
        "base_only_overlaps": base_hits,
        "base_only_pairs": base_pairs,
        "addon_overlaps": [
            {"a": a.id, "b": b.id, "kind": a.kind + "/" + b.kind,
             "result_a": a.result, "result_b": b.result, "same_result": a.result == b.result}
            for a, b in addon_hits
        ],
        "addon_conflicts": len(conflicts),
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"recipes {report['recipes']} (addon {report['addon_recipes']}); "
              f"skipped {len(skipped)} with unknown ingredient forms "
              f"({sum(1 for s in skipped if s[1] == 'addon')} from the addon)")
        print(f"base-only overlapping pairs: {base_hits} (reference behaviour, not judged)")
        for o in report["addon_overlaps"]:
            tag = "same result" if o["same_result"] else "CONFLICT"
            print(f"  {tag}: {o['a']} {o['result_a']} <-> {o['b']} {o['result_b']} ({o['kind']})")
        print(f"addon conflicts (different results): {len(conflicts)}")
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
