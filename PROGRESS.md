# PROGRESS — More Delight → Horizon port

Plan: `../addons/ADDONS_PLAN.md` §10.1 (MD-01…MD-12), rules `../addons/ADDONS_HANDOFF.md` §4. Each entry names the
base (`ported_farmersdelight`) commit and version it was validated with.

## MD-01 Repository skeleton, manifest, pins — PASS — 2026-11-16
- base: farmersdelight-horizon 39d0d5e (`3.6.30-horizon.2`) | build pin afe471cf | addon commit: (this commit)
- pins re-verified by cloning: MoreDelight `26.3-fabric` = `360e6117…` (unchanged), DelightLib `f0017bf3…` (detached,
  branch `3.6.24/26.3-fabric`). Release lookup (Modrinth/CurseForge) not retried: UNVERIFIED, as in the source lock.
- content-only package (no `[native]`, no Cargo): `horizon-mod.toml` id `ported_moredelight`, version
  `26.9.16-horizon.1`, `namespaces = ["moredelight"]`, `side = "both"`, `[dependencies] ported_farmersdelight =
  "=3.6.30-horizon.2"`. LICENSE (port, MIT), LICENSE-moredelight + `third_party/moredelight/LICENSE` (verbatim MD
  LICENSE, which also carries FD's MIT notice), NOTICE, README (install, D9 multiplayer rule), CI (JSON parses).
- found: a **content** package keeps only `assets/`, `data/` and the manifest (root `LICENSE*`/`NOTICE*` files are
  packaged for code mods only, `manifest.md` "Source paths"), so the licence texts also ship as
  `assets/moredelight/licenses/{moredelight,notice,port}.txt` (lower-case names: the packager refuses `NOTICE.txt`
  as "not a plain assets/ or data/ path"). They are copies of the root files; CI compares them.
- `cargo horizon-mod check`: "ported_moredelight 26.9.16-horizon.1 (mod, API 0.2, both) … no code: content only".
- in game (fd-port instance with `horizon-mods/ported_moredelight.hmod` + `horizon-mods.txt`
  `mod.ported_moredelight:true`): "content from 2 mod(s)"; the title screen's Mods list shows "More Delight (Horizon
  port) 26.9.16-horizon.1" beside "Farmer's Delight (Horizon …) 3.6.30-horizon.2" (screenshot). With the dependency
  renamed to a mod that is not installed, startup is refused: "ported_moredelight requires missing mod
  ported_farmersdelight_absent" (the base itself is compiled into the instance's native build, so it cannot be left
  out of fd-port; the refusal path is the same `Missing` check).
- evidence: `../run/shots/md-01/` (mods-screen.png, missing.log, crash report).
- next: MD-02 (deterministic MD carry).

## MD-02 Deterministic MD carry — PASS — 2026-11-16
- base: farmersdelight-horizon 39d0d5e (`3.6.30-horizon.2`) | addon commit: (this commit)
- `tools/carry_md.py` + `tools/carry_rules_md.toml.in`: imports the base's `carry_lib.py` from `--base` (checked at the
  pinned base commit), MD checked at `360e6117…`; every source file must match exactly one rule (copy, exclude,
  relocate, drop, overlay) or the carry fails. R1 copy `assets/moredelight/`, `data/moredelight/`, `data/c/tags/`;
  R2 exclude Casualness/Create/Expanded Delight/Nutritious Feast/Supplementaries data and `fabric.mod.json`;
  R3 knives tag → overlay; R4 `bacon_sandwich` → `moredelight:bacon_sandwich_from_bread_slices` (content unchanged,
  MA1); R5 `craft_knife` advancement dropped and logged (MA2); R6 effect-tooltip overlay = the 31 `addon.food(...)`
  ids of `MoreDelight.java` (3 commented-out foods skipped); R7 tag universe (vanilla 26.3 jar + base + output):
  0 undefined. Namespace fence check: 0 files outside `moredelight` / `c` tags. Also `logo.png` → `icon.png`.
- counts (as plan §5.4): 33 item definitions, 33 models, 41 textures, 34 lang, 38 recipes (37 + 1 relocated),
  41 advancements, 3 `c` tag files; 225 files (+ logo and icon); overlay `tools/overlay/moredelight.json`: knives
  2 ids, effect_tooltip 31 ids. `--check` byte-identical on rerun ("carry check ok: 225 files").
- `tools/test_carry_md.py` 3 OK (rules on a fixture tree, unruled file fails, undefined tag fails).
- package: 229 entries, `cargo horizon-mod check` clean.
- note: the base keeps its initial MD overlay (knives only) until BX-03 adds the `effect_tooltip` tag; the base's copy
  is then replaced with this generated file.
- next: MD-03 (item declarations and creative tab).
