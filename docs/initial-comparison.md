# Ascended 参数差异清单（第一轮）

**对照对象**：上传的 Ascended `regulation.bin` 与随后上传的原版 `regulation.bin`。  
**重要限制**：Ascended 文件内部版本为 `11601000`，原版为 `11711000`；对应 1.16 与 1.17.1 两代参数。以下是**两份文件的实际差异**，并非已经排除官方更新的“作者改动最终清单”。同版本 1.16 原版尚缺。跨版本新增、删除及数值变更只能列为候选差异。清单中没有改动任何游戏文件。

## 结论与优先级

1. **FP 经济最值得先查**：`Magic.mp` 的 200 条差异全部是 Ascended 值更高；`SwordArtsParam.useMagicPoint_L2` 的 237 条差异也全部更高。这直接影响法术、祷告和战技 Build 的持续输出，但最终体验还取决于玩家 FP、补给和回蓝机制。
2. **敌人基础数值显著变化**：`NpcParam.hp` 有 2,680 条差异，其中 2,380 条 Ascended 值较高；`superArmorDurability` 有 1,182 条差异，其中 1,175 条较高。参数行是基础值，实战血量/失衡还会受区域、倍率、特效和事件影响，不能把表中的数值直接当作游戏内 Boss 血条。
3. **装备与攻击机制重写范围很大**：武器 3,439 条共同行不同，3,106 条涉及一个常驻特效槽；NPC 攻击表有 10,238 条仅在 Ascended 文件中出现的 ID，另有 10,380 条共同行不同。仅凭 `regulation.bin` 无法说明这些新攻击的触发条件；还要查资源、地图和事件。
4. **掉落与物品数量变化**：地图掉落 2,898 条共同行不同，敌人掉落 2,628 条，主要差异集中在物品数量与掉落权重相关字段。

## 文件与方法

| 项目 | Ascended | 上传的原版 |
|---|---:|---:|
| BND 内部版本 | `11601000` | `11711000` |
| SHA-256 | `fffe741fb5acd3545857c5edf2b3e1540753f875f58002c3f7f5b9d1d31e5df2` | `766521f9508de3a3532df61c45a1c2d93340f1ff7ed8306ab20df761712ca2ab` |
| 参数表 | 194 | 194 |
| 可解析参数行 | 189,800 | 179,332 |

逐表按同名参数、同行 ID 比较原始行字节。共有 49 张表显示差异，145 张表在可比行内容上相同；但其中 10 张的行结构长度跨版本改变，不能做字段级比较。仅 Ascended 有的行 10,894 条，仅新版原版有的行 426 条；共同行字节不同 45,441 条，完全一致 133,455 条，另有 10 条行长度不同。**这些数字是文件间差异，不是可归因于作者的改动数。**

字段名取自 [Paramdex](https://github.com/soulsmods/Paramdex) 的 Elden Ring 定义和行名。194 张表中 179 张的字段定义与双方行长度吻合；其余表只做行级统计。字段级比较还受字段定义版本、别名和填充字节影响，以下重点展示有明确玩法含义的字段。

## 具体数值示例

以下“新版原版”列属于 `11711000`，请勿当作 `11601000` 同版本基准。

| 参数表 | 行 ID | Paramdex 行名 | 字段 | Ascended | 新版原版 |
|---|---:|---|---|---:|---:|
| Magic | 4000 | [Sorcery] Glintstone Pebble | `mp` | 41 | 7 |
| Magic | 4021 | [Sorcery] Comet | `mp` | 200 | 24 |
| Magic | 4710 | [Sorcery] Rock Sling | `mp` | 125 | 18 |
| Magic | 6900 | [Incantation] Lightning Spear | `mp` | 77 | 18 |
| Magic | 6210 | [Incantation] Black Flame | `mp` | 200 | 18 |
| Magic | 6421 | [Incantation] Heal | `mp` | 250 | 32 |
| SwordArtsParam | 100 | Lion's Claw | `useMagicPoint_L2` | 80 | 20 |
| SwordArtsParam | 101 | Impaling Thrust | `useMagicPoint_L2` | 80 | 9 |
| SwordArtsParam | 204 | Bloody Slash | `useMagicPoint_L2` | 80 | 6 |
| SwordArtsParam | 801 | Bloodhound's Step | `useMagicPoint_L2` | 60 | 5 |
| NpcParam | 21300014 | Margit, the Fell Omen | `hp` | 8500 | 2521 |
| NpcParam | 47500014 | Godrick the Grafted (Stormveil Castle) | `hp` | 20000 | 3354 |
| NpcParam | 47300000 | Starscourge Radahn | `hp` | 20000 | 2585 |
| NpcParam | 21200056 | Malenia, Blade of Miquella | `hp` | 25000 | 2489 |
| NpcParam | 21300014 | Margit, the Fell Omen | `superArmorDurability` | 9000.0 | 80.0 |
| NpcParam | 47500014 | Godrick the Grafted (Stormveil Castle) | `superArmorDurability` | 9000.0 | 105.0 |
| NpcParam | 21200056 | Malenia, Blade of Miquella | `superArmorDurability` | 9000.0 | 80.0 |
| EquipParamWeapon | 3180000 | Claymore | `correctStrength` | 200.0 | 49.0 |
| EquipParamWeapon | 2000000 | Longsword | `residentSpEffectId` | 3160 | -1 |
| EquipParamWeapon | 3180000 | Claymore | `spEffectBehaviorId0` | 6202080 | -1 |
| AtkParam_Npc | 2110420 | [Maliketh] Standing Omega Sword Beam | `atkPhys` | 2000 | 200 |
| AtkParam_Pc | 40070 | Glintstone Arc | `atkPhysCorrection` | 350 | 100 |

`superArmorDurability` 是参数名，不能把其 9000 对 80 的比例直接当作实际削韧效率；`residentSpEffectId` 和 `spEffectBehaviorId0` 是引用 ID，需要追踪目标特效才能确定实际玩法效果。法术和战技的 `mp`/`useMagicPoint_L2` 是明确的直接消耗字段。

## 全部有差异的参数表

“共同行不同”按字节判定；版本升级或填充字段也可能造成差异。10 张行长度变化表单列“结构差异”。

| 参数表 | 仅 Ascended 有 | 仅新版原版有 | 共同行不同 | 共同行一致 | 行长度（Ascended / 原版） |
|---|---:|---:|---:|---:|---:|
| `ActionButtonParam` | 0 | 1 | 0 | 399 | 100 / 100 |
| `AssetEnvironmentGeometryParam` | 0 | 2 | 0 | 24,104 | 320 / 320 |
| `AtkParam_Npc` | 10,238 | 0 | 10,380 | 2,475 | 456 / 456 |
| `AtkParam_Pc` | 0 | 26 | 1,503 | 9,488 | 456 / 456 |
| `AttackElementCorrectParam` | 0 | 2 | 0 | 184 | 128 / 128 |
| `BaseChrSelectMenuParam` | 0 | 2 | 0 | 15 | 32 / 32 |
| `BehaviorParam_PC` | 0 | 24 | 33 | 13,808 | 32 / 32 |
| `BuddyParam` | 1 | 1 | 139 | 30 | 160 / 160 |
| `BuddyStoneParam` | 0 | 0 | 303 | 1 | 64 / 64 |
| `Bullet` | 0 | 91 | 5,783 | 9,601 | 272 / 272 |
| `CalcCorrectGraph` | 0 | 0 | 27 | 50 | 80 / 80 |
| `CharMakeMenuListItemParam` | 0 | 2 | 0 | 228 | 16 / 16 |
| `CharaInitParam` | 0 | 33 | 393 | 2,847 | 320 / 320 |
| `EnemyCommonParam` | 0 | 0 | 0 | 0 | 256 / 264 |
| `EquipMtrlSetParam` | 0 | 4 | 0 | 841 | 52 / 52 |
| `EquipParamAccessory` | 1 | 0 | 156 | 1 | 96 / 96 |
| `EquipParamGem` | 0 | 0 | 2 | 240 | 96 / 96 |
| `EquipParamGoods` | 11 | 3 | 1,492 | 834 | 176 / 176 |
| `EquipParamProtector` | 0 | 18 | 753 | 67 | 416 / 416 |
| `EquipParamWeapon` | 2 | 82 | 3,439 | 115 | 664 / 664 |
| `FaceParam` | 0 | 8 | 15 | 550 | 240 / 240 |
| `GameSystemCommonParam` | 0 | 0 | 0 | 0 | 1024 / 1032 |
| `GraphicsCommonParam` | 0 | 0 | 0 | 0 | 256 / 264 |
| `HitMtrlParam` | 0 | 0 | 51 | 0 | 100 / 100 |
| `ItemLotParam_enemy` | 19 | 0 | 2,628 | 2,507 | 152 / 152 |
| `ItemLotParam_map` | 20 | 29 | 2,898 | 2,665 | 152 / 152 |
| `LoadBalancerNewDrawDistScaleParam_ps5` | 0 | 0 | 0 | 0 | 48 / 56 |
| `LoadBalancerNewDrawDistScaleParam_xss` | 0 | 0 | 0 | 0 | 48 / 56 |
| `LoadBalancerNewDrawDistScaleParam_xsx` | 0 | 0 | 0 | 0 | 48 / 56 |
| `Magic` | 0 | 0 | 204 | 113 | 168 / 168 |
| `MenuCommonParam` | 0 | 0 | 0 | 0 | 256 / 264 |
| `MimicryEstablishmentTexParam` | 0 | 0 | 0 | 0 | 16 / 24 |
| `NpcAiBehaviorProbability` | 0 | 5 | 0 | 279 | 400 / 400 |
| `NpcParam` | 142 | 6 | 4,816 | 2,223 | 736 / 736 |
| `NpcThinkParam` | 0 | 1 | 1,031 | 1,183 | 228 / 228 |
| `PhantomParam` | 0 | 0 | 48 | 17 | 56 / 56 |
| `PlayerCommonParam` | 0 | 0 | 0 | 0 | 256 / 264 |
| `ReinforceParamWeapon` | 0 | 26 | 22 | 891 | 128 / 128 |
| `RideParam` | 0 | 4 | 0 | 94 | 64 / 64 |
| `SfxBlockResShareParam` | 0 | 0 | 0 | 0 | 4 / 8 |
| `ShopLineupParam` | 0 | 19 | 191 | 1,086 | 52 / 52 |
| `SpEffectParam` | 459 | 29 | 8,639 | 2,686 | 912 / 912 |
| `SpEffectSetParam` | 0 | 1 | 0 | 401 | 16 / 16 |
| `SpEffectVfxParam` | 0 | 3 | 0 | 1,510 | 164 / 164 |
| `SwordArtsParam` | 1 | 3 | 255 | 20 | 32 / 32 |
| `ThrowParam` | 0 | 0 | 191 | 1,603 | 128 / 128 |
| `WeatherParam` | 0 | 0 | 15 | 147 | 68 / 68 |
| `WepAbsorpPosParam` | 0 | 1 | 0 | 69 | 96 / 96 |
| `WorldMapPieceParam` | 0 | 0 | 34 | 0 | 64 / 64 |

## 各重点表的字段清单

表内数字是**该字段出现不同值的共同行数**，不是调整幅度。部分参数含升级阶段、不同敌人形态或多个物品变体，因此行数不等于独立武器、Boss 或法术个数。

### 玩家流派与装备

| 参数表 | 差异最多的字段（改变行数） |
|---|---|
| `Magic` | `mp` 200；`mp_charge` 93；`stamina` 51；`refType` 41；`stamina_charge` 29；`aiUseJudgeId` 20；`slotLength` 13；`subCategory2` 10；`requirementFaith` 8；`consumeType6` 4 |
| `SwordArtsParam` | `useMagicPoint_L2` 237；`useMagicPoint_R2` 60；`useMagicPoint_R1` 24；`aiUsageId` 14；`artsSpeedType` 8；`useMagicPoint_L1` 2；`isRefRightArts` 1 |
| `EquipParamWeapon` | `residentSpEffectId` 3,106；`wepRegainHp` 2,786；`residentSpEffectId1` 2,778；`residentSpEffectId2` 2,348；`staminaGuardDef` 1,734；`isEnhance` 1,591；`physGuardCutRate` 1,186；`spEffectBehaviorId1` 1,124；`toughnessCorrectRate` 856；`spEffectBehaviorId0` 764 |
| `AtkParam_Pc` | `pad4` 845；`atkPhysCorrection` 326；`atkMagCorrection` 302；`atkThunCorrection` 302；`atkDarkCorrection` 301；`atkFireCorrection` 296；`spEffectId1` 95；`statusAilmentAtkPowerCorrectRate` 75；`atkBehaviorId` 61；`atkMag` 50 |
| `SpEffectParam` | `pad3` 8,341；`effectEndurance` 379；`cycleOccurrenceSpEffectId` 343；`changeHpRate` 342；`changeHpPoint` 340；`spCategory` 162；`bCurrHPIndependeMaxHP` 143；`atkEnemyDmgCorrectRate_Magic` 102；`atkEnemyDmgCorrectRate_Fire` 101；`atkEnemyDmgCorrectRate_Thunder` 101 |
| `CalcCorrectGraph` | `stageMaxGrowVal1` 23；`stageMaxGrowVal3` 23；`stageMaxGrowVal4` 23；`stageMaxGrowVal2` 22；`stageMaxVal3` 18；`stageMaxVal2` 17；`stageMaxVal1` 16；`stageMaxVal4` 7；`adjPt_maxGrowVal0` 5；`adjPt_maxGrowVal1` 5 |
| `ReinforceParamWeapon` | `correctStrengthRate` 22；`correctAgilityRate` 22；`correctMagicRate` 22；`correctFaithRate` 22；`correctLuckRate` 22 |
| `EquipParamAccessory` | `rarity` 146；`sfxVariationId` 117；`shopLv` 117；`trophySGradeId` 117；`trophySeqId` 117；`vagrantItemLotId` 117；`vagrantBonusEneDropItemLotId` 117；`vagrantItemEneDropItemLotId` 117；`residentSpEffectId1` 2；`refId` 1 |
| `EquipParamProtector` | `residentSpEffectId` 701；`rarity` 639；`toughnessCorrectRate` 598；`residentSpEffectId2` 450；`invisibleFlag_SexVer18` 399；`pad404` 324；`residentSpEffectId3` 291；`invisibleFlag_SexVer77` 186；`invisibleFlag_SexVer95` 91；`isDrop` 64 |
| `EquipParamGoods` | `goodsUseAnim` 1,035；`consumeHP` 924；`rarity` 310；`maxNum` 121；`maxRepositoryNum` 96；`pad1` 80；`pad3` 71；`potGroupId` 38；`refId_default` 36；`consumeMP` 36 |
| `CharaInitParam` | `soulLv` 350；`baseFai` 290；`baseMag` 254；`baseVit` 189；`equip_Wep_Right` 188；`baseEnd` 184；`equip_Wep_Left` 183；`equip_Helm` 182；`baseStr` 179；`baseDex` 178 |

### 敌人与攻击

| 参数表 | 差异最多的字段（改变行数） |
|---|---|
| `NpcParam` | `pad12` 4,539；`pad1` 4,536；`turnVellocity` 3,503；`hp` 2,680；`superArmorDurability` 1,182；`weakPartsDamageRate` 1,179；`hitHeight` 977；`getSoul` 907；`defFlickPower` 875；`hitRadius` 701 |
| `AtkParam_Npc` | `pad4` 8,268；`spEffectId1` 5,552；`spEffectId2` 4,527；`spEffectId0` 4,261；`atkFire` 3,123；`atkMag` 2,347；`spEffectId3` 2,293；`atkThun` 1,946；`atkPhys` 1,056；`atkDark` 872 |
| `Bullet` | `spEffectId0` 3,164；`homingBeginDist` 2,272；`spEffectId1` 1,506；`initVellocity` 1,295；`maxVellocity` 1,144；`homingAngle` 1,090；`spEffectId2` 999；`numShoot` 908；`shootAngleInterval` 760；`shootAngle` 754 |
| `NpcThinkParam` | `TeamAttackEffectivity` 697；`backhomeBattleDist` 662；`backhomeDist` 660；`maxBackhomeDist` 659；`isGuard_Act` 630；`nose_dist` 437；`goalAction_ToCaution` 216；`goalAction_ToCautionImportant` 183；`goalAction_ToSearchLv2` 182；`goalAction_ToDisappear` 182 |
| `ThrowParam` | `throwFollowingEndEasingTime` 180；`diffAngMyToDef` 17；`Dist` 15；`DiffAngMin` 13；`DiffAngMax` 13；`atkAnimId` 13；`upperYRange` 12；`lowerYRange` 12；`sphereCastRadiusRateTop` 12；`sphereCastRadiusRateLow` 12 |
| `BuddyStoneParam` | `overwriteActivateRegionEntityId` 266；`activateRange` 37；`overwriteReturnRange` 20；`warnRegionEntityId` 16 |

### 掉落与商店

| 参数表 | 差异最多的字段（改变行数） |
|---|---|
| `ItemLotParam_enemy` | `lotItemNum01` 2,152；`lotItemBasePoint02` 1,624；`lotItemBasePoint01` 1,522；`lotItemNum02` 57；`lotItemId01` 19；`lotItemCategory01` 18；`enableLuck02` 14；`lotItemId02` 14；`lotItemNum03` 14；`lotItemNum04` 14 |
| `ItemLotParam_map` | `lotItemNum01` 2,727；`lotItemId01` 903；`lotItemCategory01` 211；`lotItemNum02` 24；`lotItemNum03` 22；`getItemFlagId` 6；`lotItemNum04` 4；`lotItemCategory02` 2；`lotItemId02` 2；`lotItemBasePoint01` 1 |
| `ShopLineupParam` | `eventFlag_forRelease` 91；`sellQuantity` 73；`eventFlag_forStock` 32；`value` 30；`setNum` 19；`equipId` 15；`nameMsgId` 4；`equipType` 1；`mtrlId` 1 |

## 附录 A：全部 200 条法术／祷告基础 FP 差异

| ID | 名称 | Ascended FP | 新版原版 FP |
|---:|---|---:|---:|
| 4000 | [Sorcery] Glintstone Pebble | 41 | 7 |
| 4001 | [Sorcery] Great Glintstone Shard | 50 | 12 |
| 4010 | [Sorcery] Swift Glintstone Shard | 30 | 5 |
| 4020 | [Sorcery] Glintstone Cometshard | 80 | 17 |
| 4021 | [Sorcery] Comet | 200 | 24 |
| 4030 | [Sorcery] Shard Spiral | 62 | 14 |
| 4040 | [Sorcery] Glintstone Stars | 62 | 12 |
| 4050 | [Sorcery] Star Shower | 160 | 23 |
| 4060 | [Sorcery] Crystal Barrage | 62 | 14 |
| 4070 | [Sorcery] Glintstone Arc | 45 | 9 |
| 4080 | [Sorcery] Cannon of Haima | 160 | 38 |
| 4090 | [Sorcery] Crystal Burst | 60 | 14 |
| 4100 | [Sorcery] Shatter Earth | 55 | 10 |
| 4110 | [Sorcery] Rock Blaster | 100 | 22 |
| 4120 | [Sorcery] Gavel of Haima | 75 | 22 |
| 4130 | [Sorcery] Terra Magicus | 200 | 20 |
| 4140 | [Sorcery] Starlight | 55 | 9 |
| 4200 | [Sorcery] Comet Azur | 100 | 40 |
| 4210 | [Sorcery] Founding Rain of Stars | 144 | 27 |
| 4220 | [Sorcery] Stars of Ruin | 250 | 32 |
| 4300 | [Sorcery] Glintblade Phalanx | 85 | 18 |
| 4301 | [Sorcery] Carian Phalanx | 90 | 24 |
| 4302 | [Sorcery] Greatblade Phalanx | 133 | 30 |
| 4360 | [Sorcery] Rennala's Full Moon | 350 | 47 |
| 4361 | [Sorcery] Ranni's Dark Moon | 350 | 57 |
| 4370 | [Sorcery] Magic Downpour | 80 | 18 |
| 4380 | [Sorcery] Loretta's Greatbow | 200 | 24 |
| 4381 | [Sorcery] Loretta's Mastery | 300 | 39 |
| 4390 | [Sorcery] Magic Glintblade | 44 | 12 |
| 4400 | [Sorcery] Glintstone Icecrag | 400 | 12 |
| 4410 | [Sorcery] Zamor Ice Storm | 88 | 17 |
| 4420 | [Sorcery] Freezing Mist | 85 | 20 |
| 4430 | [Sorcery] Carian Greatsword | 65 | 12 |
| 4431 | [Sorcery] Adula's Moonblade | 90 | 22 |
| 4440 | [Sorcery] Carian Slicer | 33 | 4 |
| 4450 | [Sorcery] Carian Piercer | 75 | 17 |
| 4460 | [Sorcery] Scholar's Armament | 50 | 25 |
| 4470 | [Sorcery] Scholar's Shield | 60 | 30 |
| 4480 | [Sorcery] Lucidity | 30 | 10 |
| 4490 | [Sorcery] Frozen Armament | 40 | 20 |
| 4500 | [Sorcery] Shattering Crystal | 120 | 21 |
| 4510 | [Sorcery] Crystal Release | 155 | 34 |
| 4520 | [Sorcery] Crystal Torrent | 90 | 20 |
| 4600 | [Sorcery] Ambush Shard | 65 | 13 |
| 4610 | [Sorcery] Night Shard | 50 | 7 |
| 4620 | [Sorcery] Night Comet | 110 | 21 |
| 4630 | [Sorcery] Thops's Barrier | 21 | 7 |
| 4640 | [Sorcery] Carian Retaliation | 30 | 8 |
| 4641 | [Sorcery] Carian Retaliation (Unused 1) | 30 | 8 |
| 4642 | [Sorcery] Carian Retaliation (Unused 2) | 30 | 8 |
| 4650 | [Sorcery] Eternal Darkness | 75 | 25 |
| 4660 | [Sorcery] Unseen Blade | 65 | 13 |
| 4670 | [Sorcery] Unseen Form | 60 | 20 |
| 4700 | [Sorcery] Meteorite | 130 | 30 |
| 4701 | [Sorcery] Meteorite of Astel | 230 | 60 |
| 4710 | [Sorcery] Rock Sling | 125 | 18 |
| 4720 | [Sorcery] Gravity Well | 168 | 12 |
| 4721 | [Sorcery] Collapsing Stars | 350 | 18 |
| 4800 | [Sorcery] Magma Shot | 95 | 16 |
| 4810 | [Sorcery] Gelmir's Fury | 109 | 16 |
| 4820 | [Sorcery] Roiling Magma | 120 | 28 |
| 4830 | [Sorcery] Rykard's Rancor | 350 | 23 |
| 4900 | [Sorcery] Briars of Sin | 55 | 6 |
| 4910 | [Sorcery] Briars of Punishment | 88 | 9 |
| 5000 | [Sorcery] Rancorcall | 150 | 12 |
| 5001 | [Sorcery] Ancient Death Rancor | 450 | 21 |
| 5010 | [Sorcery] Explosive Ghostflame | 200 | 29 |
| 5020 | [Sorcery] Fia's Mist | 75 | 25 |
| 5030 | [Sorcery] Tibia's Summons | 88 | 17 |
| 5040 | [Sorcery] Death Lightning | 177 | 28 |
| 5100 | [Sorcery] Oracle Bubbles | 66 | 12 |
| 5110 | [Sorcery] Great Oracular Bubble | 99 | 16 |
| 6000 | [Incantation] Catch Flame | 55 | 10 |
| 6001 | [Incantation] O, Flame! | 76 | 16 |
| 6010 | [Incantation] Flame Sling | 55 | 11 |
| 6020 | [Incantation] Flame Fall Upon Them | 110 | 16 |
| 6030 | [Incantation] Whirl, O Flame | 65 | 19 |
| 6040 | [Incantation] Flame Cleanse Me | 21 | 14 |
| 6050 | [Incantation] Flame Grant Me Strength | 60 | 28 |
| 6060 | [Incantation] Flame Protect Me | 60 | 30 |
| 6100 | [Incantation] Giantsflame Take Thee | 300 | 30 |
| 6110 | [Incantation] Flame of The Fell God | 300 | 34 |
| 6120 | [Incantation] Burn, O Flame! | 150 | 26 |
| 6210 | [Incantation] Black Flame | 200 | 18 |
| 6220 | [Incantation] Surge, O Flame | 33 | 1 |
| 6230 | [Incantation] Scouring Black Flame | 122 | 21 |
| 6240 | [Incantation] Black Flame Ritual | 155 | 30 |
| 6250 | [Incantation] Black Flame Blade | 30 | 15 |
| 6260 | [Incantation] Black Flame's Protection | 60 | 30 |
| 6270 | [Incantation] Noble Presence | 88 | 20 |
| 6300 | [Incantation] Bloodflame Talons | 88 | 12 |
| 6310 | [Incantation] Bloodboon | 88 | 13 |
| 6320 | [Incantation] Bloodflame Blade | 40 | 20 |
| 6330 | [Incantation] Barrier of Gold | 60 | 30 |
| 6340 | [Incantation] Protection of The Erdtree | 60 | 30 |
| 6400 | [Incantation] Rejection | 55 | 9 |
| 6410 | [Incantation] Wrath of Gold | 155 | 40 |
| 6420 | [Incantation] Urgent Heal | 150 | 16 |
| 6421 | [Incantation] Heal | 250 | 32 |
| 6422 | [Incantation] Great Heal | 350 | 45 |
| 6423 | [Incantation] Lord's Heal | 650 | 55 |
| 6424 | [Incantation] Erdtree Heal | 1000 | 65 |
| 6430 | [Incantation] Blessing's Boon | 60 | 30 |
| 6431 | [Incantation] Blessing of The Erdtree | 120 | 60 |
| 6440 | [Incantation] Cure Poison | 21 | 7 |
| 6441 | [Incantation] Lord's Aid | 36 | 12 |
| 6450 | [Incantation] Flame Fortification | 40 | 20 |
| 6460 | [Incantation] Magic Fortification | 40 | 20 |
| 6470 | [Incantation] Lightning Fortification | 40 | 20 |
| 6480 | [Incantation] Divine Fortification | 40 | 20 |
| 6490 | [Incantation] Lord's Divine Fortification | 60 | 30 |
| 6500 | [Incantation] Night Maiden's Mist | 88 | 20 |
| 6510 | [Incantation] Assassin's Approach | 45 | 15 |
| 6520 | [Incantation] Shadow Bait | 66 | 15 |
| 6530 | [Incantation] Darkness | 70 | 24 |
| 6600 | [Incantation] Golden Vow | 90 | 47 |
| 6700 | [Incantation] Discus of Light | 55 | 3 |
| 6701 | [Incantation] Triple Rings of Light | 155 | 23 |
| 6710 | [Incantation] Radagon's Rings of Light | 133 | 21 |
| 6720 | [Incantation] Elden Stars | 300 | 41 |
| 6730 | [Incantation] Law of Regression | 155 | 55 |
| 6740 | [Incantation] Immutable Shield | 120 | 15 |
| 6750 | [Incantation] Litany of Proper Death | 88 | 17 |
| 6760 | [Incantation] Law of Causality | 88 | 22 |
| 6770 | [Incantation] Order's Blade | 42 | 22 |
| 6780 | [Incantation] Order Healing | 30 | 15 |
| 6800 | [Incantation] Bestial Sling | 45 | 7 |
| 6810 | [Incantation] Stone of Gurranq | 200 | 15 |
| 6820 | [Incantation] Beast Claw | 60 | 10 |
| 6830 | [Incantation] Gurranq's Beast Claw | 99 | 21 |
| 6840 | [Incantation] Bestial Vitality | 36 | 18 |
| 6900 | [Incantation] Lightning Spear | 77 | 18 |
| 6910 | [Incantation] Ancient Dragons' Light Strike | 155 | 36 |
| 6920 | [Incantation] Lightning Strike | 99 | 19 |
| 6921 | [Incantation] Frozen Lightning Spear | 144 | 29 |
| 6930 | [Incantation] Honed Bolt | 88 | 12 |
| 6940 | [Incantation] Ancient Dragons' Light Spear | 177 | 25 |
| 6941 | [Incantation] Fortissax's Light Spear | 200 | 35 |
| 6950 | [Incantation] Lansseax's Glaive | 155 | 22 |
| 6960 | [Incantation] Electrify Armament | 57 | 27 |
| 6970 | [Incantation] Vyke's Dragonbolt | 144 | 35 |
| 6971 | [Incantation] Dragonbolt Blessing | 40 | 20 |
| 7000 | [Incantation] Dragonfire | 144 | 28 |
| 7001 | [Incantation] Agheel's Flame | 244 | 36 |
| 7010 | [Incantation] Magma Breath | 144 | 30 |
| 7011 | [Incantation] Theodorix's Magma | 244 | 45 |
| 7020 | [Incantation] Dragonice | 155 | 36 |
| 7021 | [Incantation] Borealis's Mist | 255 | 48 |
| 7030 | [Incantation] Rotten Breath | 155 | 36 |
| 7031 | [Incantation] Ekzykes's Decay | 255 | 48 |
| 7040 | [Incantation] Glintstone Breath | 133 | 28 |
| 7041 | [Incantation] Smarag's Glint Breath | 255 | 36 |
| 7050 | [Incantation] Placidusax's Ruin | 600 | 62 |
| 7060 | [Incantation] Dragonclaw | 166 | 24 |
| 7080 | [Incantation] Dragonmaw | 190 | 34 |
| 7090 | [Incantation] Greyoll's Roar | 300 | 50 |
| 7200 | [Incantation] Pest Threads | 160 | 19 |
| 7210 | [Incantation] Swarm of Flies | 78 | 14 |
| 7220 | [Incantation] Poison Mist | 75 | 18 |
| 7230 | [Incantation] Poison Armament | 30 | 15 |
| 7240 | [Incantation] Scarlet Aeonia | 300 | 48 |
| 7300 | [Incantation] Inescapable Frenzy | 155 | 22 |
| 7310 | [Incantation] The Flame of Frenzy | 88 | 16 |
| 7311 | [Incantation] Unendurable Frenzy | 188 | 22 |
| 7320 | [Incantation] Frenzied Burst | 144 | 24 |
| 7330 | [Incantation] Howl of Shabriri | 144 | 21 |
| 7500 | [Incantation] Aspects of the Crucible: Tail | 99 | 20 |
| 7510 | [Incantation] Aspects of the Crucible: Horns | 99 | 18 |
| 7520 | [Incantation] Aspects of the Crucible: Breath | 99 | 28 |
| 7530 | [Incantation] Black Blade | 200 | 26 |
| 7900 | [Incantation] Fire's Deadly Sin | 99 | 26 |
| 7903 | [Incantation] Golden Light Fortification | 60 | 30 |
| 2004320 | [Sorcery] Rellana's Twin Moons | 850 | 47 |
| 2004500 | [Sorcery] Glintstone Nail | 400 | 10 |
| 2004510 | [Sorcery] Glintstone Nails | 400 | 23 |
| 2004700 | [Sorcery] Blades of Stone | 550 | 18 |
| 2004910 | [Sorcery] Impenetrable Thorns | 800 | 15 |
| 2006200 | [Sorcery] Vortex of Putrescence | 850 | 29 |
| 2006210 | [Sorcery] Mass of Putrescence | 850 | 41 |
| 2006300 | [Incantation] Furious Blade of Ansbach | 250 | 18 |
| 2006400 | [Incantation] Heal from Afar | 600 | 45 |
| 2006650 | [Incantation] Aspects of the Crucible: Thorns | 150 | 14 |
| 2006670 | [Incantation] Minor Erdtree | 300 | 30 |
| 2006700 | [Incantation] Light of Miquella | 2000 | 48 |
| 2006710 | [Incantation] Multilayered Ring of Light | 600 | 23 |
| 2006800 | [Incantation] Roar of Rugalea | 300 | 17 |
| 2006900 | [Incantation] Knight's Lightning Spear | 300 | 29 |
| 2006920 | [Incantation] Electrocharge | 200 | 26 |
| 2007000 | [Incantation] Bayle's Tyranny | 1500 | 46 |
| 2007010 | [Incantation] Bayle's Flame Lightning | 1200 | 43 |
| 2007020 | [Incantation] Ghostflame Breath | 100 | 36 |
| 2007200 | [Incantation] Rotten Butterflies | 1500 | 48 |
| 2007300 | [Incantation] Midra's Flame of Frenzy | 1400 | 22 |
| 2007410 | [Sorcery] Fleeting Microcosm | 850 | 26 |
| 2007420 | [Sorcery] Cherishing Fingers | 500 | 20 |
| 2007700 | [Sorcery] Golden Arcs | 300 | 12 |
| 2007710 | [Sorcery] Giant Golden Arc | 400 | 24 |
| 2007730 | [Incantation] Divine Beast Tornado | 700 | 24 |
| 2007800 | [Incantation] Fire Serpent | 450 | 11 |
| 2007820 | [Incantation] Messmer's Orb | 1000 | 31 |

## 附录 B：全部 237 条战技 L2 FP 差异

| ID | 名称 | Ascended FP | 新版原版 FP |
|---:|---|---:|---:|
| 100 | Lion's Claw | 80 | 20 |
| 101 | Impaling Thrust | 80 | 9 |
| 102 | Piercing Fang | 80 | 16 |
| 103 | Spinning Slash | 80 | 6 |
| 105 | Charge Forth | 80 | 16 |
| 106 | Stamp (Upward Cut) | 80 | 5 |
| 107 | Stamp (Sweep) | 80 | 5 |
| 109 | Repeating Thrust | 80 | 7 |
| 110 | Wild Strikes | 80 | 2 |
| 111 | Spinning Strikes | 80 | 2 |
| 112 | Double Slash | 80 | 6 |
| 113 | Prelate's Charge | 80 | 7 |
| 116 | Giant Hunt | 80 | 16 |
| 117 | Torch Attack | 80 | 0 |
| 118 | Loretta's Slash | 80 | 14 |
| 119 | Poison Moth Flight | 80 | 7 |
| 120 | Spinning Weapon | 80 | 12 |
| 122 | Storm Assault | 80 | 22 |
| 123 | Stormcaller | 80 | 9 |
| 124 | Sword Dance | 80 | 6 |
| 125 | Spinning Chain | 80 | 8 |
| 200 | Glintblade Phalanx | 80 | 10 |
| 201 | Sacred Blade | 80 | 19 |
| 202 | Ice Spear | 80 | 15 |
| 203 | Glintstone Pebble | 250 | 8 |
| 204 | Bloody Slash | 80 | 6 |
| 205 | Lifesteal Fist | 80 | 14 |
| 207 | Eruption | 80 | 14 |
| 208 | Prayerful Strike | 80 | 20 |
| 209 | Gravitas | 80 | 13 |
| 210 | Storm Blade | 160 | 10 |
| 212 | Earthshaker | 80 | 10 |
| 213 | Golden Land | 80 | 16 |
| 214 | Flaming Strike | 80 | 4 |
| 216 | Thunderbolt | 80 | 10 |
| 217 | Lightning Slash | 80 | 10 |
| 218 | Carian Grandeur | 80 | 26 |
| 219 | Carian Greatsword | 80 | 16 |
| 220 | Vacuum Slice | 600 | 14 |
| 221 | Black Flame Tornado | 80 | 30 |
| 222 | Sacred Ring of Light | 80 | 9 |
| 223 | Firebreather | 80 | 8 |
| 224 | Blood Blade | 80 | 3 |
| 225 | Phantom Slash | 80 | 8 |
| 226 | Spectral Lance | 80 | 9 |
| 227 | Chilling Mist | 80 | 14 |
| 228 | Poisonous Mist | 80 | 14 |
| 300 | Shield Bash | 80 | 10 |
| 301 | Barricade Shield | 80 | 12 |
| 305 | Carian Retaliation | 80 | 8 |
| 306 | Storm Wall | 80 | 0 |
| 307 | Golden Parry | 80 | 4 |
| 308 | Shield Crash | 80 | 12 |
| 501 | Hoarfrost Stomp | 80 | 10 |
| 502 | Storm Stomp | 80 | 6 |
| 504 | Lightning Ram | 80 | 5 |
| 505 | Flame of the Redmanes | 80 | 14 |
| 506 | Ground Slam | 80 | 14 |
| 507 | Golden Slam | 80 | 22 |
| 508 | Waves of Darkness | 80 | 16 |
| 509 | Hoarah Loux's Earthshaker | 80 | 16 |
| 600 | Determination | 80 | 10 |
| 601 | Royal Knight's Resolve | 80 | 15 |
| 602 | Assassin's Gambit | 80 | 5 |
| 603 | Golden Vow | 80 | 40 |
| 604 | Sacred Order | 80 | 18 |
| 605 | Shared Order | 80 | 20 |
| 606 | Seppuku | 80 | 4 |
| 607 | Cragblade | 80 | 16 |
| 651 | War Cry | 9999 | 16 |
| 652 | Beast's Roar | 80 | 10 |
| 653 | Troll's Roar | 80 | 22 |
| 654 | Braggart's Roar | 80 | 16 |
| 700 | Endure | 80 | 9 |
| 701 | Vow of the Indomitable | 80 | 20 |
| 702 | Holy Ground | 80 | 30 |
| 800 | Quickstep | 60 | 3 |
| 801 | Bloodhound's Step | 60 | 5 |
| 802 | Raptor of the Mists | 80 | 6 |
| 850 | White Shadow's Lure | 80 | 15 |
| 1000 | Surge of Faith | 80 | 15 |
| 1001 | Flame Spit | 80 | 28 |
| 1002 | Tongues of Fire | 80 | 5 |
| 1003 | Oracular Bubble | 80 | 6 |
| 1004 | Bubble Shower | 80 | 16 |
| 1005 | Great Oracular Bubble | 80 | 16 |
| 1006 | Sea of Magma | 80 | 5 |
| 1007 | Viper Bite | 80 | 8 |
| 1008 | Moonlight Greatsword | 80 | 32 |
| 1009 | Siluria's Woe | 80 | 25 |
| 1010 | Rallying Standard | 80 | 30 |
| 1011 | Bear Witness! | 80 | 20 |
| 1012 | Eochaid's Dancing Blade | 80 | 15 |
| 1013 | Soul Stifler | 80 | 12 |
| 1014 | Taker's Flames | 80 | 30 |
| 1015 | Shriek of Milos | 80 | 30 |
| 1016 | Reduvia Blood Blade | 80 | 6 |
| 1017 | Glintstone Dart | 80 | 10 |
| 1018 | Flowing Form | 80 | 9 |
| 1020 | Wave of Gold | 80 | 42 |
| 1021 | Ruinous Ghostflame | 200 | 20 |
| 1022 | Establish Order | 80 | 20 |
| 1023 | Mists of Slumber | 80 | 20 |
| 1024 | Spearcall Ritual | 80 | 20 |
| 1025 | Wolf's Assault | 80 | 20 |
| 1026 | Thundercloud Form | 80 | 28 |
| 1027 | Cursed-Blood Slice | 80 | 20 |
| 1028 | Waterfowl Dance | 80 | 12 |
| 1029 | Gold Breaker | 80 | 26 |
| 1030 | I Command Thee Kneel! | 80 | 15 |
| 1031 | Regal Roar | 80 | 25 |
| 1032 | Starcaller Cry | 80 | 20 |
| 1033 | Wave of Destruction | 80 | 25 |
| 1034 | Bloodboon Ritual | 80 | 20 |
| 1035 | Flowing Form | 80 | 16 |
| 1036 | Blade of Death | 80 | 25 |
| 1037 | Blade of Gold | 80 | 17 |
| 1038 | Destined Death | 80 | 40 |
| 1039 | Spinning Wheel | 80 | 3 |
| 1040 | Alabaster Lords' Pull | 80 | 15 |
| 1041 | Onyx Lords' Repulsion | 80 | 27 |
| 1042 | Oath of Vengeance | 80 | 20 |
| 1043 | Ice Lightning Sword | 80 | 25 |
| 1044 | Regal Beastclaw | 80 | 20 |
| 1045 | Flame Dance | 80 | 25 |
| 1046 | Claw Flick | 80 | 14 |
| 1047 | Nebula | 80 | 25 |
| 1048 | Ghostflame Ignition | 450 | 15 |
| 1049 | Ancient Lightning Spear | 80 | 24 |
| 1050 | Frenzyflame Thrust | 80 | 14 |
| 1051 | Miquella's Ring of Light | 80 | 11 |
| 1052 | Golden Tempering | 300 | 24 |
| 1053 | Last Rites | 80 | 25 |
| 1054 | Unblockable Blade | 80 | 18 |
| 1055 | Eochaid's Dancing Blade | 80 | 15 |
| 1167 | Corpse Wax Cutter | 80 | 16 |
| 1168 | Zamor Ice Storm | 80 | 15 |
| 1169 | Radahn's Rain | 9999 | -1 |
| 1170 | The Queen's Black Flame | 80 | 15 |
| 1171 | Dynast's Finesse | 80 | 5 |
| 1172 | Magma Shower | 80 | 12 |
| 1173 | Nebula | 80 | 20 |
| 1174 | Death Flare | 80 | 16 |
| 1175 | Bloodhound's Finesse | 80 | 8 |
| 1176 | Magma Guillotine | 80 | 20 |
| 1177 | Corpse Piler | 80 | 17 |
| 1179 | Bloodblade Dance | 80 | 11 |
| 1182 | Knowledge Above All | 80 | 35 |
| 1183 | Devourer of Worlds | 80 | 35 |
| 1184 | Familal Rancor | 80 | 25 |
| 1185 | Rosus's Summons | 80 | 15 |
| 1186 | Thunderstorm | 80 | 19 |
| 1187 | Sacred Phalanx | 80 | 12 |
| 1188 | Great-Serpent Hunt | 80 | 10 |
| 1189 | Angel's Wings | 80 | 17 |
| 1190 | Storm Kick | 80 | 10 |
| 1191 | Unblockable Blade | 80 | 17 |
| 1192 | Sorcery of the Crozier | 450 | 15 |
| 1193 | Erdtree Slam | 80 | 19 |
| 1194 | Gravity Bolt | 80 | 13 |
| 1195 | Fires of Slumber | 80 | 15 |
| 1196 | Golden Retaliation | 80 | 4 |
| 1197 | Contagious Fury | 80 | 9 |
| 1198 | Ordovis's Vortex | 80 | 15 |
| 1199 | Spinning Weapon | 80 | 20 |
| 2000 | Dryleaf Whirlwind | 80 | 9 |
| 2001 | Aspects of the Crucible: Wings | 80 | 22 |
| 4000 | Spinning Gravity Thrust | 80 | 26 |
| 4010 | Palm Blast | 80 | 14 |
| 4020 | Piercing Throw | 80 | 8 |
| 4030 | Scattershot Throw | 80 | 11 |
| 4040 | Wall of Sparks | 80 | 16 |
| 4050 | Rolling Sparks | 800 | 14 |
| 4060 | Raging Beast | 40 | 7 |
| 4070 | Savage Claws | 40 | 13 |
| 4080 | Red Bear Hunt | 40 | 8 |
| 4090 | Blind Spot | 40 | 9 |
| 4100 | Swift Slash | 40 | 16 |
| 4130 | Blinkbolt | 40 | 8 |
| 4140 | Flame Skewer | 40 | 18 |
| 4150 | Savage Lion's Claw | 80 | 20 |
| 4160 | Divine Beast Frost Stomp | 80 | 18 |
| 4170 | Flame Spear | 80 | 19 |
| 4180 | Carian Sovereignty | 80 | 30 |
| 4190 | Shriek of Sorrow | 80 | 19 |
| 4220 | Ghostflame Call | 450 | 15 |
| 5000 | Dragonwound Slash | 80 | 18 |
| 5010 | Needle Piercer | 80 | 19 |
| 5020 | Light | 80 | 30 |
| 5030 | Darkness | 80 | 30 |
| 5040 | Onze's Line of Stars | 40 | 10 |
| 5050 | The Poison Flower Blooms Twice | 80 | 14 |
| 5080 | Spinning Guillotine | 40 | 12 |
| 5090 | Unending Dance | 40 | 2 |
| 5100 | Revenger's Blade | 80 | 15 |
| 5110 | Mists of Eternal Sleep | 80 | 23 |
| 5120 | Dynastic Sickleplay | 40 | 7 |
| 5130 | Blinkbolt: Twinaxe | 40 | 8 |
| 5140 | Blinkbolt: Long-hafted Axe | 40 | 8 |
| 5150 | Promised Consort | 450 | 20 |
| 5160 | Shadow Sunflower Headbutts | 80 | 16 |
| 5180 | Devonia's Vortex | 80 | 16 |
| 5190 | Messmer's Assault | 80 | 15 |
| 5210 | Sleep Evermore | 80 | 16 |
| 5220 | Golden Crux | 80 | 21 |
| 5230 | Moore's Charge | 80 | 16 |
| 5240 | White Light Charge | 40 | 10 |
| 5250 | Rancor Slash | 40 | 12 |
| 5260 | Witching Hour Slash | 80 | 21 |
| 5270 | Euporia Vortex | 80 | 28 |
| 5280 | Smithing Art Spears | 80 | 18 |
| 5290 | Rancor Slash | 40 | 12 |
| 5300 | Romina's Purification | 80 | 24 |
| 5310 | Poison Spear-Hand Strike | 40 | 13 |
| 5320 | Madding Spear-Hand Strike | 40 | 13 |
| 5330 | Feeble Lord's Frenzied Flame | 40 | 3 |
| 5350 | Deadly Dance | 80 | 15 |
| 5370 | Discus Hurl | 40 | 3 |
| 5380 | Flower Dragonbolt | 80 | 18 |
| 5390 | Kowtower's Resentment | 80 | 31 |
| 5420 | Painful Strike | 80 | 16 |
| 5430 | Solitary Moon Slash | 40 | 12 |
| 5440 | Revenge of the Night | 40 | 5 |
| 5450 | Weed Cutter | 40 | 8 |
| 5460 | Blindfold of Happiness | 40 | 10 |
| 5470 | Jori's Inquisition | 40 | 6 |
| 5480 | Roaring Bash | 40 | 12 |
| 5490 | Deadly Poison Spray | 80 | 21 |
| 5500 | Flare- O Serpent | 40 | 8 |
| 5510 | Scattershot (Claws) | 40 | 11 |
| 5520 | Hone Blade | 80 | 16 |
| 5530 | Horn Calling | 80 | 17 |
| 5540 | Horn Calling: Storm | 80 | 22 |
| 5550 | Tremendous Phalanx | 80 | 16 |
| 5560 | Bloodfiends' Bloodboon | 80 | 20 |
| 5570 | Dragonform Flame | 80 | 14 |
| 5580 | Lightspeed Slash | 80 | 32 |

**解读重点**：`pad*`、`dummy*`、装备的某些可见性标志以及字段定义不确定的项需要复核，不能据其出现次数推论玩法效果。`residentSpEffectId*` 变化说明挂载的特效 ID 改了，具体效果要继续追查 `SpEffectParam` 对应行和条件；不能只看一个 ID 就断定武器被加强。

## 目前无法准确归因的部分

- 这份原版来自 1.17.1，Ascended 包来自 1.16。1.16 到 1.17.1 官方更新增加/删除/调整了部分参数行，特别是 10 张表的行长度不同。因此“仅 Ascended 有”并不必然表示作者新增，“仅新版原版有”也不等于作者删除。
- 对于同一 ID 的血量、伤害和掉落，上面可证明两份文件不同；要正式形成**作者更改清单**，还需要内部版本 `11601000` 的未修改原版 `regulation.bin` 做同版本差异。现有的 1.17.1 文件应保留，下一阶段可作为移植到新版游戏的目标基准。
- 本清单只覆盖 `regulation.bin`。压缩包中的地图、事件、角色动画、脚本、文本没有提供同版本原版文件，无法逐文件证明作者做了什么。

## 对第一阶段平衡优化的直接意义

优先核对 FP 成本、NPC 基础 HP/失衡阈值、攻击伤害和武器附加特效的联动。尤其法术与战技的高 FP 成本可能让依赖它们的 Build 过早被资源耗尽；敌人血量和失衡能力的提高会进一步放大该问题。等取得 `11601000` 原版后，先做同版本精确差异，再决定哪些值回调及改多少。

**数据来源与可复核性**：两份用户提供的 `regulation.bin`；解密与容器格式按 [SoulsFormats 代码](https://github.com/soulsmods/DSMapStudio/blob/master/src/Andre/SoulsFormats/SoulsFormats/Util/SFUtil.cs)；字段和行名按 [Paramdex](https://github.com/soulsmods/Paramdex)。官方 [1.16 更新公告](https://en.bandainamcoent.eu/elden-ring/news/elden-ring-patch-notes-version-116) 和 [1.17.1 更新公告](https://www.eldenring.jp/newsdetail/news_detail_260908_1.html)说明这确实是两个游戏版本。
