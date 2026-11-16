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

## MD-03 Item declarations and creative tab — PASS — 2026-11-16
- base: farmersdelight-horizon 39d0d5e (`3.6.30-horizon.2`) | addon commit: (this commit)
- `tools/extract_md_items.py` reads `MoreDelight.java` as text (DelightLib `knife`/`food` chains; an unknown builder
  call fails) → `tools/decl/md_items.toml.in` (33 rows, registration order, `source` = Java line);
  `tools/gen_md_decls.py [--check]` → `data/moredelight/horizon/item/*.json` (33) + `creative_tab/tab.json`.
- knives = FD `knifeItem(material)` as the base declares its knives: wooden 59 durability / +0.5 damage / speed 2.0 /
  enchantability 15 / `#minecraft:wooden_tool_materials`; stone 131 / +1.5 / 4.0 / 5 /
  `#minecraft:stone_tool_materials`; attack speed −2.0 (MQ1), stack 1. Foods: saturation = nutrition × modifier × 2
  (Java float, shortest decimal), default consumable, 0.8 s for the 6 toasts + toast, `apply_effects` per
  `withEffect` (Nourishment 3600 on 6 meals, Regeneration 100 on 2 salads; MobEffectInstance defaults, so particles
  shown), bowl foods stack 16 with bowl remainder + `use_remainder`. Chocolate popsicle has no effect (MQ5). Tab:
  literal title "More Delight" (MQ2), icon cooked chicken. Nourishment is declared by the base, so AD14's second
  pass is not needed.
- `tools/test_md_decls.py` 4 OK (table = Java extraction; knife/food/tab values).
- in game (fd-port, FDM6, offscreen): `/give` of all 33 ids works with their English names; survival with hunger:
  toast not eaten after 0.6 s, eaten within 0.95 s (0.8 s); carrot soup not eaten after 0.95 s, eaten by 1.75 s,
  leaves a bowl and gives Nourishment (3593 t left when read); mashed potatoes "can only stack up to 16", stone knife
  "up to 1"; creative page 2 shows the tab "More Delight" with the cooked-chicken icon and 33 items in order with
  their textures (`../run/shots/md-03/md-tab.png`). Knife tooltip lines were not read (the generated attribute
  values are unit-tested; the knives' behaviour is MD-04/MD-09).
- next: MD-04 (first playable slice).

## MD-04 First playable slice — PASS — 2026-11-16 — **MDM1 closed**
- base: farmersdelight-horizon 39d0d5e (`3.6.30-horizon.2`) | build pin afe471cf | addon commit: (this commit)
- single player (fd-port instance, world FDM6, survival, offscreen; pad at 60000,200,60000, forceloaded):
  - `moredelight:stone_knife` crafted in the inventory grid from cobblestone over a stick (result 131/131);
  - potato placed on the FD cutting board, cut with the stone knife → 1 `diced_potatoes`, knife damage 1;
  - bread on the board, cut → 4 `bread_slice`, knife damage 2;
  - a bread slice in a furnace with coal → `toast` after ~203 game ticks (recipe 200; polling included);
  - toast + honey bottle in the grid → `toast_with_honey`, the glass bottle stays in the grid;
  - eating (hunger first): diced potatoes food +2; toast with honey not eaten after 0.6 s, eaten by 0.95 s, +5.
- persistence: potato left on the board and the knife at damage 2 → save & quit, game restarted → the board still
  holds and renders the potato, the knife still has damage 2 (screenshot 6).
- multiplayer (dedicated server `run/fd-server`, re-exported with base 39d0d5e; MD package in the server's and both
  clients' `horizon-mods/`): server log "content from 2 mod(s)"; Alice and Bob joined; Bob placed a potato on a
  board and cut it with a stone knife → 1 diced potatoes, his knife damage 1 (screenshot 7). The server pad was
  removed afterwards.
- tool notes: a right-click while the crosshair is on a furnace reopens it, so `use-item` failed with "the container
  screen is open" until the view was turned to the sky; fast `key N` + click sequences need ~1 s pauses or the click
  uses the previous slot. The rig's windowed clients stalled again (Bob kept a stale position); `run/mp/client.sh`
  now passes extra arguments (e.g. `--offscreen`); a fresh join fixed the position. The dedicated-server export now
  goes to `run/server-export-new` (on disk) because /tmp filled up.
- evidence: `../run/shots/md-04/` (1 craft, 2 board, 3 diced, 4 slices, 5 toast with honey, 6 after restart, 7 Bob).
- next: MD-05 (skillet/stove/campfire items).

## MD-05 Skillet/stove/campfire items — PASS — 2026-11-16
- base: farmersdelight-horizon 39d0d5e (`3.6.30-horizon.2`) | addon commit: (this commit; no file change)
- in game (FDM6 pad, survival, player hands where the plan says so):
  - furnace: FD fried egg (`#c:foods/cooked_egg`) → `omelette`; smoker: bread slice → `toast`;
  - campfire (player right-click with a fried egg): total 600 → omelette dropped after ~624 game ticks (polling);
  - FD stove (player right-click): egg slot total 600 → omelette (picked up at tick 837, campfire's at 1061);
  - placed FD skillet on a lit stove: a stack of 2 bread slices taken, `CookTimeTotal` 120 (= 600 × 0.2, FD skillet
    formula) → 2 toasts ejected;
  - held FD skillet next to the stove, bread slice in the off hand, use held 6.5 s → slice −1, toast +1.
- evidence: `../run/shots/md-05.png`, game log; values read with `data get block`.
- next: MD-06 (cooking-pot meals).

## MD-06 Cooking-pot meals (12) — IN PROGRESS (stopped at the user's request) — 2026-11-16
- base: farmersdelight-horizon 39d0d5e (`3.6.30-horizon.2`) | addon commit: (this commit; no file change)
- done in game (FDM6, row of 12 lit FD stoves + pots at x 59994..60005, y 200/201, z 59996; pad forceloaded at
  59990,59990): each pot filled with `data merge` (one concrete item per recipe ingredient/tag + a bowl in the
  container slot): `CookTimeTotal` 400 from the recipe; all 12 `moredelight:cooking/*` meals cooked and were served
  into the output slot (8) with the bowl: carrot soup, 3 cooked rice, 2 creamy pasta, 4 diced potatoes meals,
  mashed potatoes (2× diced potatoes), potato salad.
- hopper above a pot (60007,202,59996) inserted `moredelight:diced_potatoes` ×2 and a milk bottle into the pot.
- save/restart mid-cook: CookTime 272 / 239 before quitting → 294 / 262 read ~22 ticks after reloading (kept, not
  reset, not instant; `tick freeze` is not saved).
- still to do: eat a rice meal and read Nourishment 3:00 (carrot soup's Nourishment already PASS in MD-03); the
  fixture "the 12 recipes parse in the base codec"; then record PASS.
- next: finish MD-06, then MD-07.

## MD-06 Cooking-pot meals (12) — PASS — 2026-11-16
- base: farmersdelight-horizon b9e88cf (package `3.6.30-horizon.2` unchanged; the new commit adds a test only) |
  addon commit: (this commit; no file change)
- in game (earlier entry): all 12 `moredelight:cooking/*` meals cooked in the FD pot with a bowl, hopper insert,
  save/restart mid-cook keeps CookTime.
- Nourishment: FDM6, survival on Easy, food 8, ate `moredelight:cooked_rice_with_beef` (hold use 3 s, looking at the
  sky; looking at the stove the click goes to the stove): `farmersdelight:nourishment` amplifier 0, 3571 t left
  when read (3600 = 3:00), bowl returned, food 20. Screenshot `../run/shots/md-06/rice-nourishment.png`. Restored
  creative + Peaceful; random_tick_speed 3.
- fixture: base `recipes::cooking::addon_dir_recipes_parse` on `data/moredelight/recipe/cooking`: 12 parsed by the
  base codec, every one Meals / 400 t / 1.0 XP / bowl container.
- AD14 second pass: not needed; the item declarations already carry Nourishment (MD-03).
- deltas: none new.
- next: MD-07 (crafted foods and relocated bacon sandwich).

## MD-07 Crafted foods and relocated bacon sandwich — PASS — 2026-11-16
- base: farmersdelight-horizon b9e88cf (package `3.6.30-horizon.2`) | addon commit: (this commit)
- in game (fd-port, FDM6, survival, crafting table at 60002,200,60005; driven through `run/ctl` grid slots 100+ /
  result 200; log `../run/shots/md-07/craft.log`): all 15 MD crafting foods crafted once with the expected result —
  simple/with-egg/loaded hamburger, steak/porkchop/tomato/egg-with-bacon/chicken-with-egg-and-tomato sandwiches,
  chicken salad, chocolate popsicle (shaped), 5 toasts. `loaded_hamburger` from bread, FD beef patty, cabbage leaf
  (`#c:foods/leafy_green`), tomato, cooked bacon, fried egg, onion (`../run/shots/md-07/loaded-hamburger.png`).
- MA1: `moredelight:bacon_sandwich_from_bread_slices` (2 bread slices) **and** FD's `farmersdelight:bacon_sandwich`
  (loaf) both give `farmersdelight:bacon_sandwich` (`../run/shots/md-07/ma1-bacon-slices.png`).
- MQ6: `egg_with_bacon_sandwich` crafted from 2 toasts (toast in `#c:bread_slices`).
- toast with honey leaves the glass bottle in the grid (vanilla remainder).
- `tools/recipe_overlap.py` (ADDONS_VALIDATION §2.3; `--base ../farmersdelight-horizon --vanilla
  ../minecraft-26.3-client.jar`): vanilla + base (+ add-on tag overlays) + MD = 1708 recipes resolved, none skipped
  (`farmersdelight:item_ability` tools compared by ability name); MD's 38 recipes overlap nothing (MA1 vs loaf: 5 vs 4
  ingredients). One base-only pair, reference behaviour, not judged: `farmersdelight:cake_from_milk_bottle` vs
  `minecraft:cake`. Fixtures `tools/test_recipe_overlap.py` 5 OK (shaped/tag conflict, shaped vs shapeless, tag merge
  with counts, same result, cutting tool overlap incl. `fabric:any` abilities). Limit: a tag tool and an ability tool
  are never treated as overlapping.
- test-world notes: FDM6 inventory moved to a chest at 60003,200,60004 (27 stacks) when it filled up; a few spilled
  `/give` materials were left to despawn. Restored creative + Peaceful.
- deltas: none new (MA1 as planned).
- next: MD-08 (MDM2 demo).

## MD-08 MDM2 demo — PASS — 2026-11-16 — **MDM2 closed**
- base: farmersdelight-horizon 4e906d6 (package `3.6.30-horizon.2` unchanged) | addon commit: (this commit; no file change)
- recorded tour (fd-port, FDM6, survival/Easy; recording `../run/horizon-home/instances/fd-port/recordings/
  2026-11-16_11-05-07-md-08-demo`, exported `…/repro/2026-11-16_11-05-07-md-08-demo.zip`; log
  `../run/shots/md-08/tour.log`, shots `1-pot-cooking.png`, `2-pot-done.png`, `3-nourishment.png`):
  fried egg right-clicked onto the FD stove → omelette after 30 s (600 t); new lit stove + pot at 60009,200/201,59996
  filled through its menu (milk bottle, rice, beef, bowl in 307) → `cooked_rice_with_beef` taken from 308; loaded
  hamburger crafted; rice meal eaten → Nourishment 3571 t left.
- save & quit + restart: every MD stack identical, pot state kept, Nourishment 3102 → 3093 t (load gap).
- guest: the offline developer session refuses `lan open` ("single-player only"), so the guest ran on the dedicated
  server rig as in M3/M5/M7 and MD-04 (`run/fd-server`, client `run/mp` B = Bob, offscreen; pad at
  60000..60016,199 in FDServer, forceload removed afterwards): Bob filled a pot through its menu →
  `cooked_rice_with_beef` taken (0 → 1) (`bob-pot-done.png`) and crafted a `tomato_sandwich` (log `bob.log`). With
  MD-04's guest cut of a potato by MD's cutting recipe this also closes BX-10's client-sync half.
- MD removed (copy `FDM6noMD`, `mod.ported_moredelight:false`): the world opens with no dialog and **no mismatch
  warning**: the save's `fml.LoadingModList` records only `ported_farmersdelight` (content-only mods are never listed,
  so `mod_mismatch` cannot fire for them; recorded as engine observation **E-40**). MD stacks in the inventory read
  as `minecraft:air` with their counts; a pot's saved output keeps the raw id `moredelight:mashed_potatoes`. After
  saving without MD and re-enabling it, every MD stack and the pot output came back unchanged. Copy moved to
  `../run/trash/FDM6noMD-md08`; the instance's mod list restored (`mod.ported_moredelight:true`).
- side finding (user report during this task): creative tab names overlap on page 2 → base E-39 (engine).
- deltas: none new.
- next: MD-09 (knife parity via the base overlay).

## MD-09 Knife parity (base overlay) — PASS — 2026-11-16
- base: farmersdelight-horizon (MD-09 base commit after 356d9ef; package `3.6.30-horizon.2`) | addon commit: (this commit)
- carry R8: every `addon.knife(...)` gets a `ported_farmersdelight:knife_items` overlay entry (DelightLib knives are FD
  KnifeItems); base pin moved to 356d9ef; test_carry_md 3 OK; carry --check 225 files.
- in game (fd-port, FDM6, survival, row at z 59993 / kill area x 59994 z 59991; screenshots `../run/shots/md-09/`):
  stone knife: pumpkin → carved pumpkin facing the clicked side, 4 seeds, knife −1; cake → bites 1 + cake slice;
  apple pie → bites 1 + pie slice; red candle cake → cake[bites=1] + red candle + slice; 30 short grass → 10 straw
  (Q1 30%); mature rice panicles → `rice` + straw (control with bread: `rice_panicle`); 7 pig kills → 3 ham
  (knife scavenging, 50%; log `scavenge.log`); Backstabbing applied, Sweeping Edge refused ("cannot support that
  enchantment"), Sharpness applied; wooden knife at 58 damage carved once more and broke (59 uses).
- not checked: chicken feather (`ctl hunt` could not hit the chickens; same attacker-knife condition as the ham row,
  which passed); knife knockback −0.1 for MD knives (code path is the tag now; not measured).
- incident: the first kill loop summoned pigs inside the MD-06 stove row (z 59996); the user noticed; mobs removed, loop moved.
- test world restored: creative, Peaceful, random_tick_speed 3; game quit.
- deltas: none new.
- next: BX-03 (base), then MD-10.
