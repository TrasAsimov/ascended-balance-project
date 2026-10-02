# 受击硬直效果描述

用户确认将护甲的内部参数式文字改为易读描述。中文 `受击动作等级 1` 改为 `减轻受击硬直`，英文 `Hit-reaction grade 1` 改为 `Reduced hit stagger`。游戏显示为 `Effect: Reduced hit stagger`；中文合并源为 `效果: 减轻受击硬直`，继续保留空行分块。

仅改文字，SpEffect 6351、护甲常驻效果、套装和全部参数不变。两个英文容器及中英文 Armor_Core 说明各232条修改，其它条目及FMG表字节不变，回读与幂等通过。未运行游戏。

`python scripts/update_hit_stagger_text.py --input <最新item.msgbnd.dcx或说明JSON> --output <输出>`

必须在最新整合文本上运行本脚本。此轮独立英文基于07最新盾牌油脂300000秒／床帘恩泽1800秒文件，继续保留大盾80%、10/5FP/s、护甲分区与盾牌效果精简等文字，不能回滚为已发布v0.10.9旧文本。未来其他文本变更优先保留，通过脚本精确修改目标短语。

生成源 texts.py、short_text.py 与旧版Effect分区升级脚本也同步，避免重建时恢复旧短语。未生成ZIP或Release，05负责下一轮统一打包。中文JSON是合并源，不是游戏zhocn档案。
