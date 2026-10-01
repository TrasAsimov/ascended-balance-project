# 护甲套装与核心伤害平衡（2026-10-01）

用户回传 Excel 的 26 类奖励、12 件单件意见，以及另一 Work 聊天的核心护符定案，已合并到同一个构建流程。具体目标和例外见 `config/approved_edits.json`，分类及全部 187 个家族见 `config/families.json`。

设计曾随 v0.10.5 发布，但用户实测其 regulation.bin 触发存档损坏误报；保留 v0.10.5 其余文件、只换 v0.10.4 regulation.bin 后正常。当前构建输出是 06-BUG-001 修复候选，尚未实机验证，没有新的下载包或 Release。问题范围确认到参数包，整表重排只是待实测的原因假设。记录见仓库 `docs/bug_06_001_regulation_20261001.md`。完整包仍由发布专用聊天处理。

## 构建

需要 Python 3.10+、`cryptography`、`zstandard`。使用项目已有的 `scripts/analyze_regulation.py`、`scripts/build_zhocn_patch.py`。参数定义由拥有者另行提供，不复制 Paramdex 到本仓库。

将下列自有输入放在本目录的 `inputs/` 中；`config/input_hashes.json` 校验对应版本，不接受未经核对的新输入：

- `work/vanilla.bnd`：官方 1.17.1 参数。
- `pending_v0105/adjusted.bnd`：v0.10.4 加既有待集成改动的参数，包括敌人韧性 +25%、大盾护符精力消耗减少 50%、原魔法护符 ×3.8。
- `pending_v0105/ModEngine/mod/regulation.bin`：与 adjusted.bnd 对应的加密容器。
- `pending_v0105/ModEngine/mod/msg/engus/item_dlc01.msgbnd.dcx` 和 `item_dlc02.msgbnd.dcx`。
- `reference/common.emevd`：现有集成版原始公共事件。
- `reference/er-common.emedf.json`：匹配的事件指令格式定义。
- `work/Paramdex/ER/Defs/*.xml`：匹配字段定义；也可通过 `ARMOR_PARAMDEFS` 指定目录。

从仓库根目录依次执行：

```bash
python systems/armor/scripts/build.py
python systems/armor/scripts/texts.py
python systems/armor/scripts/verify.py
python systems/armor/scripts/verify_layout.py
```

输出为本目录 `ModEngine/mod/regulation.bin`、`ModEngine/mod/event/common.emevd.dcx` 和两份 `ModEngine/mod/msg/engus/` 文本档案。`data/` 存放中间参数、逐项描述和审查记录，`docs/ARMOR_SYSTEM.md` 为完整目录。这些本地输出不进入 Git。

## 规则

原版单件效果及代价优先恢复；与原版冲突的旧 Mod 单件效果移除，兼容效果保留。用户本次明确改动的例外：蘑菇王冠和黑头罩的原版增伤持续 600 秒；神兽头部力量、灵巧各 +20。通过独立副本调整，不改共享原版效果行。六种小恶魔头罩新增指定效果，同时保留各自原版属性；小恶魔狮子头罩保留原版生命力 +2，再加力量 +30、信仰 +30。

同一类型奖励从两件提升到满套时，满套值替换低档值，总加成为所列满套百分比。处决、魔法剑士、熔炉、工艺、舞蹈、荆棘魔法、重力、鲜血战技适用此规则；血瓶延续原有替换规则。不同效果并存。每个穿戴部位最多计一件，同一套装的改造版兼容；不足两部位的家族只按明确单件规则处理。

满套需占齐该家族实际存在的部位。两部位家族延续既定“两件奖励即最高档”行为，不额外领取四件家族的满套奖励。换装或死亡后最多 6 个游戏帧内清除套装奖励及其触发子效果。

核心护符只改原有作用字段，保留筛选：魔法／祷告的五属性 `AttackPowerRate` 从 ×3.8 到 ×2.2，其余三项的五属性 `AttackRate` 分别为蓄力 ×3、跳跃 ×2、普通连段末击 ×3.5。攻击力倍率不等于敌人扣血倍率。防反 ×4、处决 ×5、箭矢／弩箭 ×2 保持不变。Boss 成长、敌人参数、技能范围、装备防御与强韧等保持输入版本。

## 简中说明

匹配版本的自有简中档案未提供，故未生成简中游戏档案。可先用仓库 `scripts/build_zhocn_patch.py` 更新核心护符／既有成长说明，再用本目录 `scripts/merge_zhocn.py` 添加护甲说明，两步使用不同输入、输出目录。后者默认读取生成后的 `data/description_zh.json`，支持已解压 BND4 或 DFLT；Kraken 需拥有者的解包工具或匹配 Oodle DLL。不得用英文文本文件冒充简中。

`param_patch()` 对已有行原位修改；新增行扩展目录并追加数据，保留原字符串区、原行相对布局、空指针、padding 和旧版尾部数据。新增行导致已有绝对偏移整体移动，这是必须的目录扩展，不能表述为所有偏移完全不动。`verify_layout.py` 用参数定义给定的行长检查，不使用回读器的众数行长推断；可加 `--previous-bnd <旧v0.10.5解密BND>` 核对全部行内容不变，加 `--excel <用户回传xlsx>` 核对原始意见。

参数回读、差分与事件分支模拟通过，只能作为静态验证。启动、读档、保存重载、单件和套装实际触发须各自记为通过后才可称为实机验证通过；没有这些结果时保留 not run。历史验证记录见仓库 `docs/armor_core_integration_20261001.md`。
