# Elden Ring Ascended Balance Project

Current test build: [v0.10.9](https://github.com/TrasAsimov/ascended-balance-project/releases/tag/v0.10.9-final-integration).

[简体中文](README.zh-CN.md) · [Changelog](CHANGELOG.md) · [Developer docs](docs/INDEX.md)

Independent Ascended balance project using 1.17.1-format parameters. Requires the base game and all DLC. Randomization is not implemented.

## Features

- 187 armor families, 741 named pieces; official single-piece effects and compatible Mod bonuses. Effect blocks show actual set counts. Bandit Mask belongs to Raptor/Bandit; shields retain effect text only.
- Charged heavy attacks +300%, sorcery/incantation attack power +220%; other core bonuses retained. Greatshield Talisman reduces remaining guard stamina cost by 80%.
- Official inherent weapon statuses and labels restored; extra poison/rot passives removed. Watchdog's Staff accepts compatible Ashes of War.
- Normal Baldachin's Blessing use buff lasts 120 seconds. Blessed Blue Dew restores 10 FP/s; audited equipment, Starlight Shards and Radahn regeneration restore 5 FP/s.
- Manual heart refresh includes 181 minor-boss encounters and separate Bayle reward. Player-spell positive status buildup remains 50% of the former Mod value. Extra custom penalties removed; attack statuses preserved.
- Four initial talisman slots, approved growth/weapon balance, enemy stance revisions, night event and inherited jump script.

## Install

1. Back up saves. Download `Ascended_Balance_v0.10.9_Final_Integration.zip`, verify Release `SHA256SUMS.txt`, and extract into a new directory. The automatic Source code ZIP is not the mod.
2. Run `ModEngine/launchmod_eldenring.bat` with Steam available, offline. ME3 users point the mod directory to `ModEngine/mod`. One active regulation, no root backup; do not mix old files or other parameter mods.
3. Check loading, saving and reloading before combat. `SHA256_FILES.txt` lists runtime checksums.

## Known limits

New modules passed static checks/simulations; game validation is pending. English item text is included. Chinese JSON is developer merge data; matching Chinese game archives remain unavailable. Attack-power coefficients are not guarantees of final HP damage; shared spell/effect rows can affect AI reuse. Historical jump testing does not establish whole-build validation. See [test steps](docs/v0.10.9.md).

Source, audits and historical notes stay in the repository through the developer index, outside player downloads. Ascended and Elden Ring belong to their creators; this is an independent project.
