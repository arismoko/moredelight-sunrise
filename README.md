# More Delight — Horizon port

A content-only [Horizon](https://github.com/arismoko/horizon) mod porting More Delight 26.09.16 (Minecraft 26.3), an
add-on for Farmer's Delight: wooden and stone knives, 31 foods (rice and pasta meals, mashed and diced potatoes,
salads, carrot soup, hamburgers, sandwiches, bread slices and toasts), their cooking-pot, cutting-board, crafting and
furnace recipes, advancements and 34 translations.

Version `26.9.16-horizon.2`, for the Farmer's Delight Horizon port `3.6.30-horizon.3` exactly (validated with its
commit `c2ac486`, tag `v3.6.30-horizon.3`).

## Install

1. Install the Farmer's Delight Horizon port (`ported_farmersdelight`) first; this mod refuses to load without it,
   or with another version of it.
2. Copy `ported_moredelight.hmod` into the instance's `horizon-mods/` folder and turn it on with a line
   `mod.ported_moredelight:true` in `horizon-mods.txt` beside `options.txt`.

**Multiplayer:** every player needs the Horizon client with the same Farmer's Delight port and this mod.

**Removing the mod from a world:** Horizon gives no warning (content-only mods are not recorded in the save, engine
observation E-40). More Delight items read as empty stacks while the mod is off; if the world is saved and the mod
is turned back on, they come back.

## Differences from More Delight

The port keeps More Delight's behaviour, quirks included. An add-on cannot ship files in Farmer's Delight's
namespace, so two of More Delight's changes to Farmer's Delight are different:

- **MA1:** More Delight replaces FD's bacon sandwich recipe with one made from 2 bread slices. Here the bread-slice
  recipe (`moredelight:bacon_sandwich_from_bread_slices`) is added and FD's bread recipe stays.
- **MA2:** More Delight changes FD's "craft a knife" advancement. Here FD's advancement is unchanged, so More Delight
  knives do not grant it.

More Delight's knives work as Farmer's Delight knives (cutting board, carving, cake and pie slices, straw, scavenging,
Backstabbing) and its foods show FD's effect tooltips, through the base's `knife_items` and `effect_tooltip` tags.

Kept as in More Delight:

- knives use FD's attack values (+0.5 + material damage, −2.0 speed), not the ones More Delight's code passes (MQ1);
- the creative tab is titled "More Delight" in every language (MQ2);
- the chocolate popsicle has no effect (MQ5);
- toast counts as a bread slice in recipes (`c:bread_slices`, MQ6).

## Building from source

More Delight's files under `assets/`, `data/` and `icon.png` are written by `tools/carry_md.py` from a More Delight
checkout at the pinned commit (`tools/carry_rules_md.toml.in`); never edit them by hand. The carry imports the base's
`tools/carry_lib.py` from a farmersdelight-horizon checkout at the pinned base commit and needs the Minecraft 26.3
client jar (read as a zip) for the tag check:

```sh
python3 tools/carry_md.py --md <MoreDelight> --base <farmersdelight-horizon> --vanilla <client.jar> --check
FD_BASE=<farmersdelight-horizon> python3 tools/test_carry_md.py
cargo horizon-mod build      # target/horizon-mod/ported_moredelight.hmod
cargo horizon-mod check target/horizon-mod/ported_moredelight.hmod
```

## Credits and licence

More Delight is by Axperty; Farmer's Delight by vectorwing and its contributors, and Farmer's Delight Refabricated by
MehVahdJukaar and contributors. This port's own files are MIT (`LICENSE`). More Delight's data and assets are MIT,
© 2024 Axperty (`LICENSE-moredelight`). See `NOTICE`.
