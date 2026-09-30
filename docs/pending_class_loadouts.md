# 待合并：Bandit 和 Vagabond 初始装备

基于 v0.9.1 的本地修改，等待下一个大版本统一发布。职业选择表 `BaseChrSelectMenuParam` 指向职业起源行与外观模板行，因此同时核对了两组开局装备。

| 职业 | 初始装备修改 | 护符修改 |
|---|---|---|
| Bandit | 左手改为小圆盾 Buckler；移除备用短弓和不再使用的箭矢；小圆盾保持原有战技 `Buckler Parry`（小圆盾弹反） | 保留连击护符 Winged Sword Insignia，增加短剑护符 Dagger Talisman |
| Vagabond | 其余武器保持原样 | 原曲剑护符换成大盾护符 Greatshield Talisman |

本地只检查了参数行、战技关联和其他行不变；尚未进行游戏内新建角色验证。已有存档的装备不会因初始职业参数变动而自动替换。
