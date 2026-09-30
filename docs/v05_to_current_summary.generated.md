# v0.5 → 当前 v0.10 集成测试参数

基线及当前均是内部版本 `11711000` 的 194 张参数表。仅比较 `regulation.bin` 参数行；事件、文本、地图及角色动画另行记录。相同共有行不会列入 CSV。

逐字段全量明细（gzip 压缩的 CSV，下载后解压）：[`../changes/v05_to_current_fields.csv.gz`](../changes/v05_to_current_fields.csv.gz)。独有行只有行级数量，不在字段 CSV 中假定原值。

| 指标 | 数量 |
|---|---:|
| 基线行 | 190,226 |
| 当前行 | 190,247 |
| 新增行 | 21 |
| 缺失行 | 0 |
| 改动共有行 | 3,516 |
| 字段改动 | 7,546 |
| 相同行 | 186,710 |

| 参数表 | 中文类别 | 基线行 | 当前行 | 新增 | 缺失 | 改动共有行 | 逐字段变化 |
|---|---|---:|---:|---:|---:|---:|---:|
| `EquipParamWeapon` | 武器／盾牌 | 3638 | 3638 | 0 | 0 | 2550 | 5865 |
| `ThrowParam` | 处决动作 | 1794 | 1794 | 0 | 0 | 191 | 408 |
| `AtkParam_Pc` | 玩家攻击判定 | 11017 | 11017 | 0 | 0 | 390 | 403 |
| `SpEffectParam` | 特殊效果 | 11813 | 11834 | 21 | 0 | 52 | 383 |
| `Magic` | 魔法和祷告 | 317 | 317 | 0 | 0 | 216 | 312 |
| `NpcParam` | 敌人与 NPC | 7187 | 7187 | 0 | 0 | 68 | 84 |
| `EquipParamGoods` | 道具 | 2340 | 2340 | 0 | 0 | 12 | 23 |
| `ItemLotParam_map` | 地图奖励 | 5612 | 5612 | 0 | 0 | 10 | 20 |
| `CalcCorrectGraph` | 属性成长曲线 | 77 | 77 | 0 | 0 | 3 | 17 |
| `WeatherParam` |  | 162 | 162 | 0 | 0 | 15 | 15 |
| `CharaInitParam` |  | 3273 | 3273 | 0 | 0 | 6 | 14 |
| `EquipParamCustomWeapon` |  | 1663 | 1663 | 0 | 0 | 2 | 2 |
| `MenuCommonParam` |  | 1 | 1 | 0 | 0 | 1 | 0 |

## 差异最多的字段

| 参数表 | 字段 | 变化行数 |
|---|---|---:|
| `AtkParam_Pc` | `atkMag` | 183 |
| `AtkParam_Pc` | `atkFire` | 86 |
| `AtkParam_Pc` | `atkPhys` | 50 |
| `AtkParam_Pc` | `atkDark` | 40 |
| `AtkParam_Pc` | `atkThun` | 39 |
| `AtkParam_Pc` | `atkMagCorrection` | 5 |
| `CalcCorrectGraph` | `stageMaxGrowVal2` | 3 |
| `CalcCorrectGraph` | `stageMaxGrowVal3` | 3 |
| `CalcCorrectGraph` | `stageMaxGrowVal4` | 3 |
| `CalcCorrectGraph` | `stageMaxGrowVal1` | 2 |
| `CalcCorrectGraph` | `stageMaxVal1` | 1 |
| `CalcCorrectGraph` | `stageMaxVal2` | 1 |
| `CalcCorrectGraph` | `stageMaxVal3` | 1 |
| `CalcCorrectGraph` | `stageMaxGrowVal0` | 1 |
| `CharaInitParam` | `equip_Accessory01` | 5 |
| `CharaInitParam` | `equip_Arrow` | 3 |
| `CharaInitParam` | `equip_Accessory02` | 3 |
| `CharaInitParam` | `equip_Subwep_Left` | 2 |
| `CharaInitParam` | `equip_Wep_Left` | 1 |
| `EquipParamCustomWeapon` | `gemId` | 2 |
| `EquipParamGoods` | `refId_default` | 11 |
| `EquipParamGoods` | `isConsume` | 9 |
| `EquipParamGoods` | `yesNoDialogMessageId` | 1 |
| `EquipParamGoods` | `pad3` | 1 |
| `EquipParamGoods` | `opmeMenuType` | 1 |
| `EquipParamWeapon` | `residentSpEffectId` | 1900 |
| `EquipParamWeapon` | `residentSpEffectId1` | 1414 |
| `EquipParamWeapon` | `spEffectBehaviorId1` | 1124 |
| `EquipParamWeapon` | `spEffectBehaviorId0` | 764 |
| `EquipParamWeapon` | `spEffectBehaviorId2` | 428 |
| `EquipParamWeapon` | `correctStrength` | 94 |
| `EquipParamWeapon` | `residentSpEffectId2` | 82 |
| `EquipParamWeapon` | `correctAgility` | 26 |
| `ItemLotParam_map` | `lotItemId01` | 10 |
| `ItemLotParam_map` | `lotItemCategory01` | 10 |
| `Magic` | `mp` | 216 |
| `Magic` | `mp_charge` | 96 |
| `NpcParam` | `hitHeight` | 68 |
| `NpcParam` | `hitRadius` | 16 |
| `SpEffectParam` | `effectEndurance` | 23 |
| `SpEffectParam` | `motionInterval` | 21 |
| `SpEffectParam` | `physicsAttackPowerRate` | 21 |
| `SpEffectParam` | `magicAttackPowerRate` | 21 |
| `SpEffectParam` | `fireAttackPowerRate` | 21 |
| `SpEffectParam` | `thunderAttackPowerRate` | 21 |
| `SpEffectParam` | `cycleOccurrenceSpEffectId` | 21 |
| `SpEffectParam` | `darkAttackPowerRate` | 21 |
| `ThrowParam` | `throwFollowingEndEasingTime` | 180 |
| `ThrowParam` | `diffAngMyToDef` | 17 |
| `ThrowParam` | `Dist` | 15 |
| `ThrowParam` | `DiffAngMin` | 13 |
| `ThrowParam` | `DiffAngMax` | 13 |
| `ThrowParam` | `atkAnimId` | 13 |
| `ThrowParam` | `upperYRange` | 12 |
| `ThrowParam` | `lowerYRange` | 12 |
| `WeatherParam` | `GparamId` | 15 |

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
