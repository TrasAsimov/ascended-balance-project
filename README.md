<!-- Historical v0.10.11: 小战士壶碎片1230由20%改40%；大亚历山大碎片1231撤销误加40%，恢复原防御500/异常200；血量2.5倍保留。 -->
# Elden Ring Ascended Balance Project

Current test build: [v0.10.15 Integration Test](https://github.com/TrasAsimov/ascended-balance-project/releases/tag/v0.10.15-integration).

[简体中文](README.zh-CN.md) · [Changelog](CHANGELOG.md) · [Developer docs](docs/INDEX.md)

Independent Ascended balance project using 1.17.1-format parameters. Requires the base game and all DLC. Randomization is not implemented.

## Features

- Empowered Soul minor-boss counting repaired using allocated flags. Tracks 181 encounters (150 base game, 31 DLC): each grants max HP/FP/stamina +0.2% and weapon attack power/sorcery/incantation damage +0.1%, additive within this group. Previous kills in the current journey count; repeat use refreshes without duplicates. Remembrance/Bayle rewards remain separate. English descriptions explain scope and numbers.

- All 12 origins start without the grace return item. Keepsakes offer ten build talismans including Magic Scorpion and Greatshield; None grants nothing. Names and help are updated in all three English menus. Existing saves are unaffected.

- Upgrade-dependent physical melee boosts; +0 unchanged. Modeled max-stat physical AR: Watchdog Staff ~5000, Ghiza Wheel ~2800. Serpent-Hunter offensive reinforcement gains disabled; upgrading may still consume materials. Casters and spells retain current balance.
- Eight base memory slots. New light-greatsword class: two swords with Wing Stance, Warrior Jar Shard and Winged Sword Insignia. Bullfighter class: Leontiel sword, civilian clothing, Warrior Jar Shard. No starting spirit ashes for either new class; changes apply to new characters.
- Single-piece bonuses on 18 Tarnished Pack armor configurations. Leontiel 2–3 pieces: skill damage +10%; 4 pieces: +20%, replacing the lower tier. Clearer reduced-hit-stagger captions.
- Warrior Jar Shard (small, 1230): skill damage +20% → +40%. Shard of Alexander (large, 1231): erroneous +40% removed; original defense/status effects and descriptions restored. Base HP growth becomes 2.5× vanilla rather than 2×.
- Normal Baldachin buff: 30 minutes. Shield Grease: 300,000 seconds. Runtime lifecycle requires testing.
- All v0.10.9 fixes retained, including Greatshield 80%, weapon statuses, Watchdog Ashes, 10/5 FP regeneration, hearts, spell status 50% and jump script.

## Install

1. Back up saves. Download `Ascended_Balance_v0.10.15_Integrated_Test.zip`, verify Release `SHA256SUMS.txt`, and extract into a new directory. The automatic Source code ZIP is not the mod.
2. Run `ModEngine/launchmod_eldenring.bat` with Steam available, offline. ME3 users point the mod directory to `ModEngine/mod` and register the real path to `ModEngine/ExpandedTalismanSlots.dll` in their actual profile under `[[natives]]`, keeping the INI beside the DLL and avoiding duplicate registration. One active regulation, no root backup; do not mix old files or other parameter mods.
3. Check loading, saving and reloading before combat. `SHA256_FILES.txt` lists runtime checksums.

## Known limits

New modules passed static checks/simulations; game validation is pending. English item text is included. Chinese JSON is developer merge data; matching Chinese game archives remain unavailable. Attack-power coefficients are not guarantees of final HP damage; shared spell/effect rows can affect AI reuse. Historical jump testing does not establish whole-build validation. See [test steps](docs/v0.10.15.md).

Source, audits and historical notes stay in the repository through the developer index, outside player downloads. Ascended and Elden Ring belong to their creators; this is an independent project.


## Six talismans test

The v0.10.15 full test package includes four native slots plus two additional slots managed through the Site of Grace menu, the original author DLL, its INI and ME2 registration. Packaging checks passed; game validation remains pending. See the [integration handoff](docs/six_talisman_integration_20261003.md).

Credits: [Expanded Talisman Slots](https://www.nexusmods.com/eldenring/mods/10481) by [imCioco](https://www.nexusmods.com/profile/imCioco/mods). The user confirmed author consent for integration; the original v1.1.6 DLL is preserved.

## v0.10.15 integration

Starscourge regeneration is halved: the three effects change from 80/120/50 to 40/60/25 HP per second. FP remains 5/s. Reapply the remembrance; activation, duration and other effects are retained. English descriptions match.

The separate private Caligo expansion consolidates T1/T2/T3/Hotfix04 and this regeneration change. Install over a clean v0.10.15 core and launch `ModEngine/launch_caligo_v0115.bat`. Caligo assets are excluded from the public core because redistribution permission remains unconfirmed. The signature-gated HP cap module affects the global engine cap and requires APPLIED/ALREADY_APPLIED in its log. Nominal Caligo HP is 750000, phase change 60%; HP and full-road firing remain unverified in game. See [integration checks](docs/v0.10.15.md).
