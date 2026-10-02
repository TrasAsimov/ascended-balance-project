# 褪色者包护甲单件增益补齐

覆盖 4 套、18 个条目（含改造版），目标为每件至少两条正向单件增益。按现有 Ascended 档位使用属性 +30、资源／负重 +30%、对应承伤 -30%，回蓝 5 FP/s。保留原版单件效果及代价、套装增益及分区排版。

| 套装 | 装备 | 本次新增单件增益 |
|---|---|---|
| 破损金面具套装（暂译） | Broken Gold Mask | 信仰 +30 |
| 破损金面具套装（暂译） | Gold Tattoo (Chest) | 最大生命值 +30% |
| 破损金面具套装（暂译） | Gold Tattoo (Arm) | 最大 FP +30% |
| 破损金面具套装（暂译） | Gold Tattoo (Leg) | 最大精力 +30% |
| 银沟套装（暂译） | Silver Grooved Helm | 生命力 +30；圣属性承伤 -30% |
| 银沟套装（暂译） | Silver Grooved Armor | 最大生命值 +30%；雷电承伤 -30% |
| 银沟套装（暂译） | Silver Grooved Gauntlets | 力量 +30；突刺承伤 -30% |
| 银沟套装（暂译） | Silver Grooved Greaves | 最大精力 +30%；斩击承伤 -30% |
| 银沟套装（暂译） | Silver Grooved Armor (Altered) | 最大生命值 +30%；雷电承伤 -30% |
| 莱昂提尔套装（暂译） | Leontiel's Hat | 智力 +30；最大 FP +30% |
| 莱昂提尔套装（暂译） | Leontiel's Armor | 最大生命值 +30%；魔力承伤 -30% |
| 莱昂提尔套装（暂译） | Leontiel's Leather Gloves | 集中力 +30；每秒恢复 5 FP |
| 莱昂提尔套装（暂译） | Leontiel's Boots | 最大精力 +30%；负重上限 +30% |
| 莱昂提尔套装（暂译） | Leontiel's Hat (Altered) | 智力 +30；最大 FP +30% |
| 钢铁套装（暂译） | Steel Helm | 耐力 +30；打击承伤 -30% |
| 钢铁套装（暂译） | Steel Armor | 最大生命值 +30%；标准物理承伤 -30% |
| 钢铁套装（暂译） | Steel Gauntlets | 力量 +30；火焰承伤 -30% |
| 钢铁套装（暂译） | Steel Greaves | 负重上限 +30%；突刺承伤 -30% |

破损金面具／纹身各保留原有祷告加成或信仰 +2/+1 及睡眠、发狂抗性和魔力防御代价，每件新增一条正向效果。其它14条配置各新增两条。银沟改造胸甲、莱昂提尔改造帽与原件新增效果相同，不算额外套装部位。

## 在最新整合输入上应用

参数：`python scripts/add_tarnished_armor_bonuses.py --input <最新regulation.bin> --output <输出.bin> --protector-def <EquipParamProtector.xml> --effect-def <SpEffect.xml> --audit <审计.json>`，密钥使用 ARMOR_REGULATION_KEY_HEX 环境变量。

英文／中文说明：`python scripts/update_tarnished_armor_text.py --input <最新item.msgbnd.dcx或护甲说明JSON> --output <输出> --language <en或zh>`。两份英文和中英文JSON需一起更新；保留现有套装名字、总件数、单件及套装Effect分区。

本次最终独立参数直接基于01最新近战强化候选（f7fe406e...），继续保留武器强化收益与06新职业出生配置候选，继承8记忆槽、油脂300000秒、床帘恩泽1800秒及v0.10.9全部修复。两份英文基于02最新受击硬直描述，继承07时长、01回蓝、大盾80%和护甲盾牌分区。若06斗牛剑等后续职业配置或其它模块已更新，必须对最新输入运行脚本，不得用本轮整文件回滚。

只改18行护甲的常驻效果槽，193其它表体、全部特效参数和非目标护甲行保持。已有单件ID保留，未占用槽不足时拒绝覆盖。复用现有效果而非复制；同ID叠加规则不改，不能按装备数承诺同类回蓝倍增。回读、幂等、加密回读、文字非目标条目保持检查通过。游戏未实测，中文JSON不是游戏zhocn档案。

关闭游戏后由05统一集成参数和文字，实测穿上一件即可得到对应单件增益、改造版一致、脱装恢复，再核对两件／四件套装与保存重载。未生成ZIP、tag或Release。
