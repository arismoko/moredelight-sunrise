# More Delight — Horizon port

A content-only [Horizon](https://github.com/arismoko/horizon) mod porting More Delight 26.09.16 (Minecraft 26.3), an
add-on for Farmer's Delight: wooden and stone knives, 31 foods (rice and pasta meals, mashed and diced potatoes,
salads, carrot soup, hamburgers, sandwiches, bread slices and toasts), their cooking-pot, cutting-board, crafting and
furnace recipes, advancements and 34 translations.

Version `26.9.16-horizon.1`, for the Farmer's Delight Horizon port `3.6.30-horizon.2` exactly.

## Install

1. Install the Farmer's Delight Horizon port (`ported_farmersdelight`) first; this mod refuses to load without it,
   or with another version of it.
2. Copy `ported_moredelight.hmod` into the instance's `horizon-mods/` folder and turn it on with a line
   `mod.ported_moredelight:true` in `horizon-mods.txt` beside `options.txt`.

**Multiplayer:** every player needs the Horizon client with the same Farmer's Delight port and this mod.

## Building from source

```sh
cargo horizon-mod build      # target/horizon-mod/ported_moredelight.hmod
cargo horizon-mod check target/horizon-mod/ported_moredelight.hmod
```

## Licence

This port's own files are MIT (`LICENSE`). More Delight's data and assets are MIT, © 2024 Axperty
(`LICENSE-moredelight`). See `NOTICE`.
