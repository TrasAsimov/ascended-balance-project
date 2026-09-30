# 艾尔登法环 Ascended 平衡优化项目

[English](README.md) · [版本改动记录](CHANGELOG.md) · [最新测试包](https://github.com/TrasAsimov/ascended-balance-project/releases/tag/v0.10.4-jump-integrated)

这是在 **Ascended: Age of the Endless** MOD 基础上进行的独立平衡与新版兼容项目。第一阶段希望保留 Ascended 的敌人强度与特色战斗，同时让法术、祷告、战技、弓箭和其他武器玩法有更多选择。敌人、Boss 与掉落随机化属于第二阶段，**目前尚未制作**。

当前完整测试版为 **v0.10.4**，参数容器使用官方 1.17.1 格式，以兼容玩家当前游戏的新内容和初始职业；这不代表 Ascended 的每一项旧机制都已经迁移到新版。游戏本体与 DLC 需自行拥有。

## 主要改动

| 方向 | 当前实现 |
|---|---|
| 多流派平衡 | 调整 FP 经济，逐条审查 217 条玩家可用魔法与祷告，并修订大量攻击判定、伤害和相关效果，让施法不再明显落后于特大武器蓄力。 |
| 难度与生存 | 敌人基础生命及区域生命倍率恢复 Ascended 原有强度；玩家基础生命按原版生命成长曲线 ×2。移除“拿起普通武器就增加生命与固定属性攻击”的异常常驻效果。 |
| 武器和护符 | 恢复受影响武器的原战技，审查 2,550 条武器行；调整短剑、曲剑、双头剑、斧、爪、大盾和硬箭等护符，英文游戏内说明随参数修订。 |
| 失衡与处决 | 恢复官方处决配对，审查全部 7,187 条 NPC 参数，并修复可处决模型及 Ascended 新变体的接触范围；部分自定义动画仍需游戏内验证。 |
| 开局与状态条 | 开局四护符槽，调整血、蓝、精力显示与成长；修订 Bandit、Vagabond 初始装备、托雷特道具参数，并加入开局 Empowered Soul。 |
| 追忆 | 21 种普通追忆目标为每层最大生命 +5%、攻击力 +2.5%，并接入法术增益；统一心脏刷新与互斥仍需进一步实测。四种特殊追忆保留其特殊效果。 |
| 永夜与跳跃 | 公共事件尝试在时间变化后将世界拉回 23:45。基于当前版本的玩家 HKS 恢复 Ascended 的 1.4 倍跳跃移动缩放，同时保留新版武器战技映射；玩家已实测高跳与斗牛剑战技正常。 |

上表说明当前目标和已集成内容，不代表每只 Boss、每把武器和全部事件都完成实测。**弹反加速和宽松判定、完整游戏内简体中文、统一心脏动作、随机化**仍是独立待办事项。

## 安装与测试

1. 从 [v0.10.4 Release](https://github.com/TrasAsimov/ascended-balance-project/releases/tag/v0.10.4-jump-integrated) 下载完整安装 ZIP。GitHub 自动生成的“Source code”压缩包不是 MOD 安装包。
2. 解压到**新的** MOD 文件夹，按包内 ModEngine 方式启动。直接混合覆盖旧文件夹可能残留旧版 `c0000.hks`、`c0000.anibnd.dcx` 或文本文件。
3. 备份存档，离线测试并禁用 EAC。新角色初始物品不会自动补发到旧存档。
4. 如需单独撤销高跳脚本，删除 MOD 路径下的 `ModEngine/mod/action/script/c0000.hks`。

v0.10.4 完整包 SHA-256：`007b4f0b8dff4d6bab6ad7bcec25ba28386df839c9f589849df23efcfad70136`。

## 仓库内容

- [`CHANGELOG.md`](CHANGELOG.md)：唯一持续维护的版本说明，含已知限制与验证状态。
- [`docs/vanilla_to_v0104_summary.md`](docs/vanilla_to_v0104_summary.md)：与官方 1.17.1 同版本参数的逐表对照。
- [`changes/vanilla_to_v0104_fields.csv.gz`](changes/vanilla_to_v0104_fields.csv.gz)：可解析字段的完整差异，包含表、行 ID、原版值和当前值；解压后为 CSV。差异同时包含 Ascended 原有修改和本项目修改。
- [`changes/`](changes/)：保留每版必要的参数审查 CSV 和 manifest。历史文件名含 `pending_` 不代表当前版本仍未集成。
- [`scripts/`](scripts/)：构建与审查脚本，需要你自己拥有的游戏和 MOD 原始资源，尚非一键从零构建。
- [`docs/zhocn_patch.md`](docs/zhocn_patch.md)：同版本简中物品文本补丁的双语说明与生成方法；可直接安装的简中二进制包仍需同版本原版简中输入文件。

完整测试包中的游戏资源放在 Releases，不直接加入源码目录。参数字段定义参考 [Paramdex](https://github.com/soulsmods/Paramdex)，本仓库没有复制其数据。

## 致谢

Ascended: Age of the Endless 与《艾尔登法环》分别归其原作者所有。本项目是独立的平衡与兼容性工作，不是原 Ascended 或游戏官方更新。
