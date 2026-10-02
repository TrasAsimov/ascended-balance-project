<!-- Historical v0.10.11: 小战士壶碎片1230由20%改40%；大亚历山大碎片1231撤销误加40%，恢复原防御500/异常200；血量2.5倍保留。 -->
# Elden Ring Ascended Balance Project

Current test build: [v0.10.12](https://github.com/TrasAsimov/ascended-balance-project/releases/tag/v0.10.12-starting-keepsakes).

[简体中文](README.zh-CN.md) · [Changelog](CHANGELOG.md) · [Developer docs](docs/INDEX.md)

Independent Ascended balance project using 1.17.1-format parameters. Requires the base game and all DLC. Randomization is not implemented.

## Features

- All 12 origins start without the grace return item. Keepsakes offer ten build talismans including Magic Scorpion and Greatshield; None grants nothing. Names and help are updated in all three English menus. Existing saves are unaffected.

- Upgrade-dependent physical melee boosts; +0 unchanged. Modeled max-stat physical AR: Watchdog Staff ~5000, Ghiza Wheel ~2800. Serpent-Hunter offensive reinforcement gains disabled; upgrading may still consume materials. Casters and spells retain current balance.
- Eight base memory slots. New light-greatsword class: two swords with Wing Stance, Shard of Alexander and Winged Sword Insignia. Bullfighter class: Leontiel sword, civilian clothing, Shard of Alexander. No starting spirit ashes for either new class; changes apply to new characters.
- Single-piece bonuses on 18 Tarnished Pack armor configurations. Leontiel 2–3 pieces: skill damage +10%; 4 pieces: +20%, replacing the lower tier. Clearer reduced-hit-stagger captions.
- Warrior Jar Shard (small, 1230): skill damage +20% → +40%. Shard of Alexander (large, 1231): erroneous +40% removed; original defense/status effects and descriptions restored. Base HP growth becomes 2.5× vanilla rather than 2×.
- Normal Baldachin buff: 30 minutes. Shield Grease: 300,000 seconds. Runtime lifecycle requires testing.
- All v0.10.9 fixes retained, including Greatshield 80%, weapon statuses, Watchdog Ashes, 10/5 FP regeneration, hearts, spell status 50% and jump script.

## Install

1. Back up saves. Download `Ascended_Balance_v0.10.12_Starting_Keepsakes.zip`, verify Release `SHA256SUMS.txt`, and extract into a new directory. The automatic Source code ZIP is not the mod.
2. Run `ModEngine/launchmod_eldenring.bat` with Steam available, offline. ME3 users point the mod directory to `ModEngine/mod`. One active regulation, no root backup; do not mix old files or other parameter mods.
3. Check loading, saving and reloading before combat. `SHA256_FILES.txt` lists runtime checksums.

## Known limits

New modules passed static checks/simulations; game validation is pending. English item text is included. Chinese JSON is developer merge data; matching Chinese game archives remain unavailable. Attack-power coefficients are not guarantees of final HP damage; shared spell/effect rows can affect AI reuse. Historical jump testing does not establish whole-build validation. See [test steps](docs/v0.10.12.md).

Source, audits and historical notes stay in the repository through the developer index, outside player downloads. Ascended and Elden Ring belong to their creators; this is an independent project.
