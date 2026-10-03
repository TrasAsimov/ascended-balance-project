<!-- Historical v0.10.11: 小战士壶碎片1230由20%改40%；大亚历山大碎片1231撤销误加40%，恢复原防御500/异常200；血量2.5倍保留。 -->
# ELDEN RING: NIGHTTIDE

Current test build: [v0.10.16 Complete Caligo Test](https://github.com/TrasAsimov/ascended-balance-project/releases/tag/v0.10.16-caligo-full).

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

1. Back up saves. Download `Ascended_Balance_v0.10.16_Caligo_Full_Test.zip`, verify Release `SHA256SUMS.txt`, and extract into a new directory. The automatic Source code ZIP is not the mod.
2. Install ME3, then run `ModEngine/launchmod_eldenring.bat` with Steam available, offline. The supplied profile loads one `ModEngine/mod` directory and registers the talisman and HP-cap DLLs. Do not mix old profiles, files or parameter mods.
3. Check loading, saving and reloading before combat. `SHA256_FILES.txt` lists runtime checksums.

## Known limits

New modules passed static checks/simulations; game validation is pending. English item text is included. Chinese JSON is developer merge data; matching Chinese game archives remain unavailable. Attack-power coefficients are not guarantees of final HP damage; shared spell/effect rows can affect AI reuse. Historical jump testing does not establish whole-build validation. See [test steps](docs/v0.10.16.md).

Source, audits and historical notes stay in the repository through the developer index, outside player downloads. Ascended and Elden Ring belong to their creators; this is an independent project.


## Six talismans test

The v0.10.16 full test package includes four native slots plus two additional slots managed through the Site of Grace menu, the original author DLL, its INI and ME3 registration. Packaging checks passed; game validation remains pending. See the [integration handoff](docs/six_talisman_integration_20261003.md).

Credits: [Expanded Talisman Slots](https://www.nexusmods.com/eldenring/mods/10481) by [imCioco](https://www.nexusmods.com/profile/imCioco/mods). The user confirmed author consent for integration; the original v1.1.6 DLL is preserved.


## Complete Caligo integration

v0.10.16 includes the entire core and cumulative Caligo runtime in one ZIP, one `ModEngine/mod` directory and one `ModEngine/launchmod_eldenring.bat` entry. Install ME3 and extract into a clean directory. No separate expansion or old patches are needed. The supplied ME3 profile registers both native modules.

Nominal Caligo HP is 750000, phase threshold 60% of current maximum HP. The global HP-cap module requires APPLIED/ALREADY_APPLIED in its log; other actors configured above the old cap may also gain their full configured HP. Starscourge regeneration is 40/60/25 HP/s, FP remains 5/s. Existing non-fire resistance, combat/rewards, lake cleanup and road golem candidates are retained.

Static checks passed; runtime signature match, HP bar and full-road firing remain untested. Existing shared-resource and missing-reference risks remain. User requested this combined external test release; no original-author endorsement is claimed. Credits: DDMMDD09 (Caligo, Nexus8583), NymicRazor/Named-Blade (HP signature, Nexus5732), imCioco (Expanded Talisman Slots, Nexus10481). See [test guide](docs/v0.10.16.md).
