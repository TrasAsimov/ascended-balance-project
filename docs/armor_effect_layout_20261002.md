# Bandit Mask 套装归属与 Effect 描述分区

Bandit Mask（1401000）原先被误分配到皮革套装，而 Bandit Garb、Bandit Manchettes、Bandit Boots 归在猛禽套装。现在将面罩作为猛禽／盗贼套装头部槽的另一选项；骨骸面具与面罩不重复计算，套装总件数仍为 4。皮革套装保留 Black Hood 作为头部。

单件睡眠抗性 +400 不变；两件奖励为跳跃攻击削韧 +10%，四件额外奖励为跳跃攻击伤害 +10%。只修改所属套装的判定与文字，不改变奖励参数。

## 描述格式

全部 741 件护甲移除物品背景描述，保留套装名字和总件数。单件效果使用 `Effect:`，套装效果使用 `2-Piece Effect:` / `4-Piece Effect:`，每项效果之间空一行，倍率用百分比。中文对应 `效果:` / `2件效果:` / `4件效果:`。

```text
Raptor / Bandit Set (4 pieces)

Effect: Sleep resistance +400 points

2-Piece Effect: Jump attack stance damage +10%

4-Piece Effect: Jump attack damage +10%
```

## 在 v0.10.8 上集成

```sh
python scripts/update_armor_effect_layout.py --input /path/to/extracted/game-root --output /path/to/handoff
```

输入目录应包含 `ModEngine` 和 `Armor_Core`，输入哈希必须匹配 v0.10.8。用输出的 common.emevd.dcx、两个 engus item_dlc*.msgbnd.dcx 替换统一集成树的对应文件；description_zh.json、description_en.json、shield_description_en.json 放入 Armor_Core 交接目录。regulation.bin 不改动，核心伤害、心脏效果、法术异常积累与其他整合改动继续保留。

中文 JSON 是合并源，不能作为中文游戏容器使用；合并真正的 zhocn msgbnd 仍需相应语言源文件。不要将英文容器混入中文后冒充中文版。

## 验证与发布范围

已回读 1482 条英文护甲描述，检查 741 条中文源；效果内容保持不变，仅面罩改用正确套装奖励。实际装备条件指令穷举 450 个穿戴组合，含不足两件、两件、满套及卸装组合。只修改四个套装事件（9000157、9000158、9000187、9000188）；其余 560 个事件及心脏事件 20007902 不变。除目标护甲和盾牌描述表以外的 FMG 字节不变；其他装备文本与中文核心／心脏条目不变。

完整校验和见同目录 JSON。尚未启动游戏验证视觉、读档和效果触发。未生成 ZIP、Release 或统一下载包；由统一集成工作聊天纳入下一版并实测。

## 盾牌补充要求

所有盾牌的背景／物品描述移除，仅保留原 Ascended 的数值效果，以 `Effect:` 开头并空行分隔。两份容器各覆盖 933 个描述条目（包括质变版本）。v0.10.8 的 DLC01 保留了原生盾牌故事，DLC02 才有 Ascended 效果，因而将 DLC02 已有效果同步到两份容器，避免不同 DLC 容器选取导致显示不一致。少数盾牌原来没有数值效果文本，清除故事后不编造奖励；共 100 个条目为空，含质变版本。

原文中荆棘盾的 `200 madness resist` 没有 Effect 前缀，已保留并独立成块。被误放在空白 `Effect:` 后的物品故事不当作效果保留。盾牌参数与实际增益不改动，数值沿用现有 Ascended 文本。
