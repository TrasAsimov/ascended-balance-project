# Elden Ring Ascended Balance Project

**v0.10.5 regression:** The player reports `Save data is corrupted`; keeping its other files and replacing only `regulation.bin` with v0.10.4 works. Candidate 1 also failed. Use [v0.10.4](https://github.com/TrasAsimov/ascended-balance-project/releases/tag/v0.10.4-jump-integrated) for the game-tested baseline. [Candidate 2](docs/bug_06_001_regulation_20261001.md) preserves all approved parameter data and removes unreferenced outer-container copies; startup, load/save and actual effect validation are still pending. No replacement release has been published.

[简体中文](README.zh-CN.md) · [Changelog](CHANGELOG.md) · [Game-tested baseline](https://github.com/TrasAsimov/ascended-balance-project/releases/tag/v0.10.4-jump-integrated)

An independent balance and compatibility project built on the **Ascended: Age of the Endless** mod for *Elden Ring*. The first phase makes more character builds viable while retaining Ascended's stronger enemies and distinctive encounters. Enemy, boss, and loot randomization is a later phase; it has **not** been implemented.

The current integrated test build is **v0.10.5**, available from GitHub Releases. It uses a 1.17.1-format `regulation.bin` so the owner's newer game content and starting classes can be tested. It still includes Ascended-derived resources; it is not a complete port of every original Ascended system to the newer game version. Own the base game and **all DLC packs** to access the mod's complete content.

## Armor and core balance in v0.10.5

The reviewed 2026-10-01 armor revision and core talisman balance are included in the complete package. The system covers **187 families and 741 named pieces**, with rewards for 165 families, restores official single-piece effects, and preserves compatible mod effects. See the [complete armor catalog and audit](docs/armor_core_integration_20261001.md) and [v0.10.5 installation and test notes](docs/v0.10.5.md).

| Core effect | Current coefficient |
|---|---:|
| Sorcery / incantation attack power | ×2.2 |
| Charged attack | ×3 |
| Jump attack | ×2 |
| Regular combo final hit | ×3.5 |
| Guard counter | ×4 |
| Backstab / critical | ×5 |
| Arrows / bolts | ×2 |
| Greatshield guard stamina consumption | ×0.5 (50% reduction) |

These coefficients keep their original filters; attack power is not a guarantee of identical final HP damage. Normal enemy stance durability is increased by 25% in 6,453 rows, excluding disabled and special high-value rows. Boss growth is retained. Same-kind armor bonuses replace the lower tier with the full-set total; different bonuses coexist. New changes pass static checks; in-game testing is pending. English archives are included; matching Chinese game archives remain pending.

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

1. Use the [v0.10.4 baseline](https://github.com/TrasAsimov/ascended-balance-project/releases/tag/v0.10.4-jump-integrated) while the v0.10.5 regression is investigated. For the single-file repair candidate, follow the dedicated bug report above. Do not use GitHub's auto-generated “Source code” ZIP as the mod package.
2. Use **ME3**. Extract the whole mod folder to a location such as `E:\me3\config\profiles\eldenring-mods\<mod-folder>\`, keeping its `ModEngine` directory and `ModEngine\launchmod_eldenring.bat` in place. Use a fresh folder: mixing with an older version can leave obsolete scripts, animations, or message files behind.
3. Back up saves and disable EAC for offline mod testing. Start Steam, then run `<mod-folder>\ModEngine\launchmod_eldenring.bat` to launch the mod. A new character is needed to test starting items; existing saves do not receive them automatically. The base game and **all DLC packs** are required for the full content.

Download `Ascended_Balance_v0.10.5_Armor_Core_Integrated.zip`. The Release includes `SHA256SUMS.txt`; package validation is recorded in [`changes/v0.10.5_package_manifest.json`](changes/v0.10.5_package_manifest.json).

## Repository map

- [`CHANGELOG.md`](CHANGELOG.md): the single maintained version history, current status, and known limitations.
- [`docs/vanilla_to_v0104_summary.md`](docs/vanilla_to_v0104_summary.md): historical v0.10.4 comparison against same-version 1.17.1 parameters; v0.10.5 additions are recorded separately in the integration audit.
- [`changes/vanilla_to_v0104_fields.csv.gz`](changes/vanilla_to_v0104_fields.csv.gz): all comparable changed fields, with row IDs, baseline values, and current values. Decompress before opening as CSV. Ascended's original changes and this project's changes are both included.
- [`changes/`](changes/): per-version parameter audit CSVs and manifests retained for traceability; historical `pending_` filenames do not necessarily describe the current release status.
- [`scripts/`](scripts/): build and audit scripts. They require the owner's own game/mod inputs and are not a one-command clean-room build.
- [`docs/zhocn_patch.md`](docs/zhocn_patch.md): bilingual instructions and the source patch for matching-version Simplified Chinese item descriptions. A ready-to-install Chinese binary awaits the owner's matching game archives.

The original and integrated game resource files are distributed as test build assets under Releases, not as source files in this Git tree. [Paramdex](https://github.com/soulsmods/Paramdex) supplies field definitions for the comparison; its data is not copied here.

## Credit

Ascended: Age of the Endless and *Elden Ring* belong to their respective creators. This project is an independent balance and compatibility effort, not an official update of Ascended or the game.

Armor follow-up: current source fixes wearer applicability masks and constructor reachability, and replaces armor/talisman lore with compact effects. See the [follow-up audit](docs/armor_activation_text_20261001.md). Runtime bonuses require retesting; the existing v0.10.5 download does not include this follow-up.
