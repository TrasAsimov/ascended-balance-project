# Elden Ring Ascended Balance Project

[简体中文](README.zh-CN.md) · [Changelog](CHANGELOG.md) · [Latest test build](https://github.com/TrasAsimov/ascended-balance-project/releases/tag/v0.10.4-jump-integrated)

An independent balance and compatibility project built on the **Ascended: Age of the Endless** mod for *Elden Ring*. The first phase makes more character builds viable while retaining Ascended's stronger enemies and distinctive encounters. Enemy, boss, and loot randomization is a later phase; it has **not** been implemented.

The current integrated test build is **v0.10.4**. It uses a 1.17.1-format `regulation.bin` so the owner's newer game content and starting classes can be tested. It still includes Ascended-derived resources; it is not a complete port of every original Ascended system to the newer game version. Own the base game and **all DLC packs** to access the mod's complete content.

## Pending armor and core damage integration

The user-approved 2026-10-01 armor revision and core talisman targets are implemented in [`systems/armor/`](systems/armor/), with the [integration audit](docs/armor_core_integration_20261001.md). Static checks pass; in-game testing is pending. This source submission does not create a new download package or Release; v0.10.4 remains the published release.

## What changed

| Area | Current direction |
|---|---|
| Build variety | Rebalanced the FP economy and reviewed all 217 player spells and incantations. Many spell hitboxes, damage parameters, and related effects were revised so magic and incantations can compete with heavy charged attacks. |
| Difficulty and survival | Restored Ascended's enemy base HP and regional HP multipliers after an overcorrection made encounters too easy. Player base HP follows twice the game's Vigor growth curve; carrying a weapon no longer adds an unrelated HP multiplier or fixed elemental attack. |
| Equipment | Restored original weapon skills for affected equipment, audited 2,550 weapon rows, and adjusted talismans such as Dagger, Curved Sword, Twinblade, Axe, Claw, Greatshield, and Arrow's Sting. English in-game captions were updated to match the intended effects. |
| Stance and critical attacks | Restored official critical-attack pairings and audited all 7,187 NPC rows. Contact dimensions were corrected on eligible models and Ascended variants. Some custom animation interactions still require in-game testing. |
| Player experience | Four talisman slots from the start, revised HP/FP/stamina display and growth, revised Bandit/Vagabond starting gear, Torrent item parameters, and the starter Empowered Soul. |
| Remembrances | Twenty-one ordinary remembrance effects target +5% maximum HP and +2.5% attack power per eligible boss, with a corresponding spell effect. The unified heart and non-stacking behavior need further in-game validation. Four special remembrances retain their distinct effects. |
| Night and movement | A common event aims to return the world to 23:45 after time changes. The current-version player HKS restores Ascended's 1.4 jump movement scale without reverting new weapon skills to the old 1.16 mapping. The jump and the new sword's skill were tested by the player. |

These are the **current intended and integrated changes**, not a claim that every boss, weapon, event, or localization has passed exhaustive playtesting. Faster or more forgiving parry timing, full Chinese in-game text, the final unified-heart action, and randomization remain separate work items.

## Install and test

1. Download the complete ZIP from the [v0.10.4 release](https://github.com/TrasAsimov/ascended-balance-project/releases/tag/v0.10.4-jump-integrated). Do not use GitHub's auto-generated “Source code” ZIP as the mod package.
2. Use **ME3**. Extract the whole mod folder to a location such as `E:\me3\config\profiles\eldenring-mods\<mod-folder>\`, keeping its `ModEngine` directory and `ModEngine\launchmod_eldenring.bat` in place. Use a fresh folder: mixing with an older version can leave obsolete scripts, animations, or message files behind.
3. Back up saves and disable EAC for offline mod testing. Start Steam, then run `<mod-folder>\ModEngine\launchmod_eldenring.bat` to launch the mod. A new character is needed to test starting items; existing saves do not receive them automatically. The base game and **all DLC packs** are required for the full content.

The v0.10.4 complete ZIP SHA-256 is `007b4f0b8dff4d6bab6ad7bcec25ba28386df839c9f589849df23efcfad70136`.

## Repository map

- [`CHANGELOG.md`](CHANGELOG.md): the single maintained version history, current status, and known limitations.
- [`docs/vanilla_to_v0104_summary.md`](docs/vanilla_to_v0104_summary.md): same-version 1.17.1 parameter comparison by table.
- [`changes/vanilla_to_v0104_fields.csv.gz`](changes/vanilla_to_v0104_fields.csv.gz): all comparable changed fields, with row IDs, baseline values, and current values. Decompress before opening as CSV. Ascended's original changes and this project's changes are both included.
- [`changes/`](changes/): per-version parameter audit CSVs and manifests retained for traceability; historical `pending_` filenames do not necessarily describe the current release status.
- [`scripts/`](scripts/): build and audit scripts. They require the owner's own game/mod inputs and are not a one-command clean-room build.
- [`docs/zhocn_patch.md`](docs/zhocn_patch.md): bilingual instructions and the source patch for matching-version Simplified Chinese item descriptions. A ready-to-install Chinese binary awaits the owner's matching game archives.

The original and integrated game resource files are distributed as test build assets under Releases, not as source files in this Git tree. [Paramdex](https://github.com/soulsmods/Paramdex) supplies field definitions for the comparison; its data is not copied here.

## Credit

Ascended: Age of the Endless and *Elden Ring* belong to their respective creators. This project is an independent balance and compatibility effort, not an official update of Ascended or the game.
