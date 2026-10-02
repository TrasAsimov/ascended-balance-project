# 官方原版 1.17.1 → 当前 v0.10 集成测试参数

基线及当前均是内部版本 `11711000` 的 194 张参数表。仅比较 `regulation.bin` 参数行；事件、文本、地图及角色动画另行记录。相同共有行不会列入 CSV。

逐字段全量明细（gzip 压缩的 CSV，下载后解压）：[`../changes/vanilla_to_current_fields.csv.gz`](../changes/vanilla_to_current_fields.csv.gz)。独有行只有行级数量，不在字段 CSV 中假定原值。

| 指标 | 数量 |
|---|---:|
| 基线行 | 179,332 |
| 当前行 | 190,247 |
| 新增行 | 10,915 |
| 缺失行 | 0 |
| 改动共有行 | 45,348 |
| 字段改动 | 159,487 |
| 相同行 | 133,984 |

| 参数表 | 中文类别 | 基线行 | 当前行 | 新增 | 缺失 | 改动共有行 | 逐字段变化 |
|---|---|---:|---:|---:|---:|---:|---:|
| `NpcParam` | 敌人与 NPC | 7045 | 7187 | 142 | 0 | 4816 | 38109 |
| `AtkParam_Npc` | 敌人攻击判定 | 12855 | 23093 | 10238 | 0 | 10380 | 36882 |
| `EquipParamWeapon` | 武器／盾牌 | 3636 | 3638 | 2 | 0 | 3521 | 19945 |
| `Bullet` |  | 15475 | 15475 | 0 | 0 | 5783 | 16212 |
| `SpEffectParam` | 特殊效果 | 11354 | 11834 | 480 | 0 | 8639 | 14270 |
| `ItemLotParam_enemy` |  | 5135 | 5154 | 19 | 0 | 2628 | 5466 |
| `NpcThinkParam` |  | 2215 | 2215 | 0 | 0 | 1031 | 5320 |
| `CharaInitParam` |  | 3273 | 3273 | 0 | 0 | 397 | 3920 |
| `ItemLotParam_map` | 地图奖励 | 5592 | 5612 | 20 | 0 | 2898 | 3905 |
| `EquipParamProtector` |  | 838 | 838 | 0 | 0 | 753 | 3775 |
| `AtkParam_Pc` | 玩家攻击判定 | 11017 | 11017 | 0 | 0 | 1754 | 3331 |
| `EquipParamGoods` | 道具 | 2329 | 2340 | 11 | 0 | 1491 | 2947 |
| `FaceParam` |  | 573 | 573 | 0 | 0 | 15 | 2283 |
| `EquipParamAccessory` | 护符 | 157 | 158 | 1 | 0 | 156 | 969 |
| `PhantomParam` |  | 65 | 65 | 0 | 0 | 48 | 593 |
| `Magic` | 魔法和祷告 | 317 | 317 | 0 | 0 | 220 | 537 |
| `BuddyStoneParam` |  | 304 | 304 | 0 | 0 | 303 | 339 |
| `ShopLineupParam` |  | 1296 | 1296 | 0 | 0 | 191 | 266 |
| `CalcCorrectGraph` | 属性成长曲线 | 77 | 77 | 0 | 0 | 27 | 160 |
| `ReinforceParamWeapon` |  | 939 | 939 | 0 | 0 | 22 | 110 |
| `HitMtrlParam` |  | 51 | 51 | 0 | 0 | 51 | 65 |
| `WorldMapPieceParam` |  | 34 | 34 | 0 | 0 | 34 | 34 |
| `BehaviorParam_PC` |  | 13865 | 13865 | 0 | 0 | 33 | 33 |
| `WeatherParam` |  | 162 | 162 | 0 | 0 | 14 | 14 |
| `EquipParamCustomWeapon` |  | 1663 | 1663 | 0 | 0 | 2 | 2 |
| `BuddyParam` |  | 170 | 171 | 1 | 0 | 139 | 0 |
| `MenuCommonParam` |  | 1 | 1 | 0 | 0 | 1 | 0 |
| `PlayerCommonParam` |  | 1 | 1 | 0 | 0 | 1 | 0 |
| `SwordArtsParam` |  | 278 | 279 | 1 | 0 | 0 | 0 |

## 差异最多的字段

| 参数表 | 字段 | 变化行数 |
|---|---|---:|
| `AtkParam_Npc` | `pad4` | 8268 |
| `AtkParam_Npc` | `spEffectId1` | 5552 |
| `AtkParam_Npc` | `spEffectId2` | 4527 |
| `AtkParam_Npc` | `spEffectId0` | 4261 |
| `AtkParam_Npc` | `atkFire` | 3123 |
| `AtkParam_Npc` | `atkMag` | 2347 |
| `AtkParam_Npc` | `spEffectId3` | 2293 |
| `AtkParam_Npc` | `atkThun` | 1946 |
| `AtkParam_Pc` | `pad4` | 845 |
| `AtkParam_Pc` | `atkPhysCorrection` | 285 |
| `AtkParam_Pc` | `atkMagCorrection` | 266 |
| `AtkParam_Pc` | `atkThunCorrection` | 261 |
| `AtkParam_Pc` | `atkDarkCorrection` | 261 |
| `AtkParam_Pc` | `atkFireCorrection` | 255 |
| `AtkParam_Pc` | `atkMag` | 216 |
| `AtkParam_Pc` | `atkFire` | 114 |
| `BehaviorParam_PC` | `stamina` | 33 |
| `BuddyStoneParam` | `overwriteActivateRegionEntityId` | 266 |
| `BuddyStoneParam` | `activateRange` | 37 |
| `BuddyStoneParam` | `overwriteReturnRange` | 20 |
| `BuddyStoneParam` | `warnRegionEntityId` | 16 |
| `Bullet` | `spEffectId0` | 3164 |
| `Bullet` | `homingBeginDist` | 2272 |
| `Bullet` | `spEffectId1` | 1506 |
| `Bullet` | `initVellocity` | 1295 |
| `Bullet` | `maxVellocity` | 1144 |
| `Bullet` | `homingAngle` | 1090 |
| `Bullet` | `spEffectId2` | 999 |
| `Bullet` | `numShoot` | 908 |
| `CalcCorrectGraph` | `stageMaxGrowVal1` | 23 |
| `CalcCorrectGraph` | `stageMaxGrowVal3` | 23 |
| `CalcCorrectGraph` | `stageMaxGrowVal4` | 23 |
| `CalcCorrectGraph` | `stageMaxGrowVal2` | 22 |
| `CalcCorrectGraph` | `stageMaxVal3` | 17 |
| `CalcCorrectGraph` | `stageMaxVal2` | 16 |
| `CalcCorrectGraph` | `stageMaxVal1` | 15 |
| `CalcCorrectGraph` | `stageMaxVal4` | 7 |
| `CharaInitParam` | `soulLv` | 350 |
| `CharaInitParam` | `baseFai` | 290 |
| `CharaInitParam` | `baseMag` | 254 |
| `CharaInitParam` | `baseVit` | 189 |
| `CharaInitParam` | `equip_Wep_Right` | 188 |
| `CharaInitParam` | `baseEnd` | 184 |
| `CharaInitParam` | `equip_Wep_Left` | 182 |
| `CharaInitParam` | `equip_Helm` | 182 |
| `EquipParamAccessory` | `rarity` | 146 |
| `EquipParamAccessory` | `sfxVariationId` | 117 |
| `EquipParamAccessory` | `shopLv` | 117 |
| `EquipParamAccessory` | `trophySGradeId` | 117 |
| `EquipParamAccessory` | `trophySeqId` | 117 |
| `EquipParamAccessory` | `vagrantItemLotId` | 117 |
| `EquipParamAccessory` | `vagrantBonusEneDropItemLotId` | 117 |
| `EquipParamAccessory` | `vagrantItemEneDropItemLotId` | 117 |
| `EquipParamCustomWeapon` | `gemId` | 2 |
| `EquipParamGoods` | `goodsUseAnim` | 1035 |
| `EquipParamGoods` | `consumeHP` | 924 |
| `EquipParamGoods` | `rarity` | 310 |
| `EquipParamGoods` | `maxNum` | 121 |
| `EquipParamGoods` | `maxRepositoryNum` | 96 |
| `EquipParamGoods` | `pad1` | 80 |
| `EquipParamGoods` | `pad3` | 70 |
| `EquipParamGoods` | `refId_default` | 45 |
| `EquipParamProtector` | `residentSpEffectId` | 701 |
| `EquipParamProtector` | `rarity` | 639 |
| `EquipParamProtector` | `toughnessCorrectRate` | 598 |
| `EquipParamProtector` | `residentSpEffectId2` | 450 |
| `EquipParamProtector` | `invisibleFlag_SexVer18` | 399 |
| `EquipParamProtector` | `pad404` | 324 |
| `EquipParamProtector` | `residentSpEffectId3` | 291 |
| `EquipParamProtector` | `invisibleFlag_SexVer77` | 186 |
| `EquipParamWeapon` | `wepRegainHp` | 2786 |
| `EquipParamWeapon` | `residentSpEffectId2` | 2348 |
| `EquipParamWeapon` | `staminaGuardDef` | 1734 |
| `EquipParamWeapon` | `isEnhance` | 1591 |
| `EquipParamWeapon` | `residentSpEffectId1` | 1366 |
| `EquipParamWeapon` | `residentSpEffectId` | 1207 |
| `EquipParamWeapon` | `physGuardCutRate` | 1186 |
| `EquipParamWeapon` | `toughnessCorrectRate` | 856 |
| `FaceParam` | `face_partsId` | 15 |
| `FaceParam` | `skin_color_R` | 15 |
| `FaceParam` | `skin_color_G` | 15 |
| `FaceParam` | `skin_color_B` | 15 |
| `FaceParam` | `skin_gloss` | 15 |
| `FaceParam` | `face_aroundEye` | 15 |
| `FaceParam` | `face_aroundEyeColor_R` | 15 |
| `FaceParam` | `face_aroundEyeColor_G` | 15 |
| `HitMtrlParam` | `spEffectIdOnHit0` | 50 |
| `HitMtrlParam` | `spEffectId_forWet00` | 7 |
| `HitMtrlParam` | `spEffectId_forWet03` | 4 |
| `HitMtrlParam` | `aiVolumeRate` | 3 |
| `HitMtrlParam` | `spEffectId_forWet02` | 1 |
| `ItemLotParam_enemy` | `lotItemNum01` | 2152 |
| `ItemLotParam_enemy` | `lotItemBasePoint02` | 1624 |
| `ItemLotParam_enemy` | `lotItemBasePoint01` | 1522 |
| `ItemLotParam_enemy` | `lotItemNum02` | 57 |
| `ItemLotParam_enemy` | `lotItemId01` | 19 |
| `ItemLotParam_enemy` | `lotItemCategory01` | 18 |
| `ItemLotParam_enemy` | `enableLuck02` | 14 |
| `ItemLotParam_enemy` | `lotItemId02` | 14 |
| `ItemLotParam_map` | `lotItemNum01` | 2727 |
| `ItemLotParam_map` | `lotItemId01` | 903 |
| `ItemLotParam_map` | `lotItemCategory01` | 212 |
| `ItemLotParam_map` | `lotItemNum02` | 24 |
| `ItemLotParam_map` | `lotItemNum03` | 22 |
| `ItemLotParam_map` | `getItemFlagId` | 6 |
| `ItemLotParam_map` | `lotItemNum04` | 4 |
| `ItemLotParam_map` | `lotItemCategory02` | 2 |
| `Magic` | `mp` | 217 |
| `Magic` | `mp_charge` | 103 |
| `Magic` | `stamina` | 51 |
| `Magic` | `refType` | 41 |
| `Magic` | `stamina_charge` | 29 |
| `Magic` | `aiUseJudgeId` | 20 |
| `Magic` | `slotLength` | 13 |
| `Magic` | `subCategory2` | 10 |
| `NpcParam` | `pad12` | 4539 |
| `NpcParam` | `pad1` | 4536 |
| `NpcParam` | `turnVellocity` | 3503 |
| `NpcParam` | `hp` | 2680 |
| `NpcParam` | `weakPartsDamageRate` | 1179 |
| `NpcParam` | `hitHeight` | 912 |
| `NpcParam` | `getSoul` | 907 |
| `NpcParam` | `defFlickPower` | 875 |
| `NpcThinkParam` | `TeamAttackEffectivity` | 697 |
| `NpcThinkParam` | `backhomeBattleDist` | 662 |
| `NpcThinkParam` | `backhomeDist` | 660 |
| `NpcThinkParam` | `maxBackhomeDist` | 659 |
| `NpcThinkParam` | `isGuard_Act` | 630 |
| `NpcThinkParam` | `nose_dist` | 437 |
| `NpcThinkParam` | `goalAction_ToCaution` | 216 |
| `NpcThinkParam` | `goalAction_ToCautionImportant` | 183 |
| `PhantomParam` | `edgeColorB` | 47 |
| `PhantomParam` | `edgeColorG` | 46 |
| `PhantomParam` | `edgeColorR` | 45 |
| `PhantomParam` | `edgeColorA` | 44 |
| `PhantomParam` | `glowScale` | 40 |
| `PhantomParam` | `frontColorA` | 36 |
| `PhantomParam` | `frontColorG` | 35 |
| `PhantomParam` | `frontColorB` | 35 |
| `ReinforceParamWeapon` | `correctStrengthRate` | 22 |
| `ReinforceParamWeapon` | `correctAgilityRate` | 22 |
| `ReinforceParamWeapon` | `correctMagicRate` | 22 |
| `ReinforceParamWeapon` | `correctFaithRate` | 22 |
| `ReinforceParamWeapon` | `correctLuckRate` | 22 |
| `ShopLineupParam` | `eventFlag_forRelease` | 91 |
| `ShopLineupParam` | `sellQuantity` | 73 |
| `ShopLineupParam` | `eventFlag_forStock` | 32 |
| `ShopLineupParam` | `value` | 30 |
| `ShopLineupParam` | `setNum` | 19 |
| `ShopLineupParam` | `equipId` | 15 |
| `ShopLineupParam` | `nameMsgId` | 4 |
| `ShopLineupParam` | `equipType` | 1 |
| `SpEffectParam` | `pad3` | 8320 |
| `SpEffectParam` | `effectEndurance` | 382 |
| `SpEffectParam` | `cycleOccurrenceSpEffectId` | 343 |
| `SpEffectParam` | `changeHpRate` | 342 |
| `SpEffectParam` | `changeHpPoint` | 340 |
| `SpEffectParam` | `spCategory` | 144 |
| `SpEffectParam` | `bCurrHPIndependeMaxHP` | 143 |
| `SpEffectParam` | `atkEnemyDmgCorrectRate_Magic` | 102 |
| `WeatherParam` | `GparamId` | 14 |
| `WorldMapPieceParam` | `openEventFlagId` | 34 |

## 无法逐字段解析的表

- `BuddyParam`: 行字节数 160 → 160；定义 96。
- `ChrModelParam`: 行字节数 16 → 16；定义 12。
- `EnemyCommonParam`: 行字节数 264 → 264；定义 256。
- `GameSystemCommonParam`: 行字节数 1032 → 1032；定义 800。
- `GraphicsCommonParam`: 行字节数 264 → 264；定义 256。
- `LoadBalancerNewDrawDistScaleParam_ps5`: 行字节数 56 → 56；定义 48。
- `LoadBalancerNewDrawDistScaleParam_xss`: 行字节数 56 → 56；定义 48。
- `LoadBalancerNewDrawDistScaleParam_xsx`: 行字节数 56 → 56；定义 48。
- `MenuCommonParam`: 行字节数 264 → 264；定义 256。
- `MimicryEstablishmentTexParam`: 行字节数 24 → 24；定义 16。
- `PlayerCommonParam`: 行字节数 264 → 264；定义 256。
- `PostureControlParam_WepRight`: 行字节数 144 → 144；定义 112。
- `SfxBlockResShareParam`: 行字节数 8 → 8；定义 4。
- `SignPuddleParam`: 行字节数 48 → 48；定义 32。
- `SoundCutsceneParam`: 行字节数 36 → 36；定义 32。
