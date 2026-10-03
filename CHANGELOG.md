## v0.10.15 — 最近改动整合测试版（2026-10-03）

- 碎星追忆三条回血80/120/50→40/60/25 HP/s，5FP/s与触发/时长保持；核心和Caligo优先加载参数同时应用，两部核心英文说明与扩展英文说明同步。
- 私人Caligo扩展累计T1/T2/T3/HF04，删除旧启动入口和开发附件，只保留单入口、运行资源、说明与校验。75万静态HP、60%阶段、非火抗性与三只道路魔像候选保留；HP模块全局作用，需运行日志确认。
- 删除17个逐字节重复的历史归档文件（101739字节），保留唯一记录与构建依赖。玩家核心984文件、979既有文件不变；扩展53文件，不带重复核心。
- 核心Pre-release上传GitHub；Caligo原资源许可未确认，仅私人交付。CRC、逐文件SHA、参数白名单、幂等与英文非目标文字校验通过，未运行Windows游戏。

## v0.10.14 — 六护符测试版 / Six Talismans Test

- 集成用户提供并已获作者同意的imCioco Expanded Talisman Slots 1.1.6，原DLL不修改。
- 原生四槽＋额外两槽＝总六槽，INI启用且slots=2；额外槽由赐福菜单管理，普通装备界面仍为四槽。
- 包内ME2配置加载DLL；原生ME3须在实际profile登记DLL路径，单设mod目录不足。
- 保留v0.10.13全部游戏数据。984文件，979个既有文件逐字节保持，配置／安装说明／校验表更新，新增DLL与INI；CRC、全包读回和内部SHA256通过，游戏实测待完成。

## v0.10.13 — 新职业护符与心脏奖励修复 / Starter and heart fix

- 两个新职业出生及男女预览固定护符1231→1230小战士壶碎片，沿用战技+40%；其它配装与库存保持v0.10.12，仅新建角色。
- Empowered Soul计数器迁移到已分配旗标，替换旧扩展尾部；181场小首领奖励恢复计数路径，三资源上限各+0.2%／攻击与施法各+0.1%按场加算。移除小首领误继承的固定5%物理层；追忆／贝勒保持。
- 两部英文心脏说明写明范围、数值、重复刷新和不消耗；已有本周目击败可计入。中文源同步。
- 全部计数及重复／重置模拟、其它事件与非目标参数／文本、幂等和读回通过。静态实现完成，未游戏实测。保留v0.10.12十护符礼物、无返回赐福、HP×2.5及其它既有内容。

## v0.10.12 — Starting items and keepsakes

- Remove grace return goods from all 12 origins, 24 previews and four common player templates.
- Ten selectable build talismans, including unchanged Magic Scorpion and Greatshield. None is empty. English names/help updated in all three menu archives.
- All v0.10.11 balance and class builds retained; new characters only. Static validation passed, game test pending.

## v0.10.11 — Jar shard target correction

- Warrior Jar Shard (1230 / 312300): skill damage 20% → 40%.
- Shard of Alexander (1231): restore v0.10.9 effects and descriptions; remove mistaken private effect 78212310.
- Keep player HP ×2.5 and all other v0.10.10 changes. English DLC01/02 descriptions updated.
- Previous 13 old Releases and 15 uploaded assets removed; Git tags preserved.

# 版本摘要 / Changelog

## v0.10.10 — 发布后改动整合（2026-10-02）

- 近战物理强化按等级提高，+0不变；满力敏模型看门犬杖约5000、吉萨刺轮约2800。大蛇矛进攻属性从+0到+10保持，强化材料仍可消耗；法杖／圣印记与法术、祷告不变。
- 基础记忆槽8个；双轻大剑出生自带单翼架势及亚历山大碎片／翼剑徽章；斗牛剑职业使用平民服装与亚历山大碎片。两个新职业无初始骨灰，七药各20、心脏／赐福记忆各1；仅影响新建角色。
- 18条褪色者护甲补单件增益；莱昂提尔2～3件全战技伤害+10%、4件+20%，满套替换低档；原生单件特色保留。受击文字改为“减轻受击硬直”。
- 亚历山大碎片新增独立战技+40%，保留原主效果防御／异常增益；玩家基础HP曲线从原版×2升至×2.5。
- 最新道具定案：普通床帘恩泽1800秒／30分钟，盾牌油脂300000秒，覆盖v0.10.9的120秒／60秒。死亡、换装、休息和重载处理尚需实测。
- 保留v0.10.9大盾80%、原生武器异常、看门犬战灰、10／5 FP/s、心脏、法术异常50%和高跳；不重复减半。

静态、目录、幂等、加密／文字读回、ZIP CRC和内部校验通过；新增改动未实机验证。

## v0.10.9 — 最终整合（2026-10-02）

- 盗贼面罩归属、741件护甲/盾牌Effect分区。
- 大盾护符修正零消耗字段，目标剩余格挡消耗减少80%。
- 武器固有异常恢复官方，去掉额外常驻异常；看门犬杖恢复安装战灰。
- 普通床帘恩泽120秒；蓝露滴10FP/s，其余已审计回蓝来源5FP/s。
- 继承v0.10.8核心、心脏、异常50%、减益清理、护甲及高跳，不重复减半。
- ZIP仅运行资源、简短说明、校验和；开发资料集中仓库。静态核验通过，实机未测。

## v0.10.8 — 统一整合（2026-10-02）

- 套装234条武器筛选、12条额外减益清理、保留攻击异常。
- 心脏181场小首领成长和贝勒独立奖励；法术异常50%。
- 蓄力额外+300%，魔法/祷告攻击力额外+220%。

## v0.10.7 / v0.10.6 — 护甲描述与激活修复

- 百分比分行及套装件数；紧凑容器、奖励目标标记和初始化修复。

## 更早版本

- v0.10.5：护甲套装与核心整合，曾出现存档损坏误报。
- v0.10.4～v0.10：高跳、战技、永夜、处决与心脏。
- v0.9～v0.1：护符、状态条、法术/FP、武器、职业和参数格式迁移。

详见[开发索引](docs/INDEX.md)、[完整旧记录](docs/archive/CHANGELOG_through_v0.10.8.md)、[机器差分](changes/INDEX.md)。静态检查、已集成、玩家实测分别记录。
