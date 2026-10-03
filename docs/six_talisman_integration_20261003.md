# 六护符集成（待05发布与实机验证）

用户确认已取得作者同意，2026-10-03提供Expanded Talisman Slots 1.1.6原始压缩包。作者imCioco，来源https://www.nexusmods.com/eldenring/mods/10481，主页https://www.nexusmods.com/profile/imCioco/mods。发布时保留该署名和链接。当前公开v0.10.13仍未包含本模块。

核对原包仅包含ExpandedTalismanSlots.dll（312320字节，PE x64 DLL）与ExpandedTalismanSlots.ini（182字节）。原包SHA256 `bc917f070f41b1f0387d2c4ad465398ad6fa76292c1533d8323dab3bc364ea85`；DLL SHA256 `9b6a4190c02b6be9ed23301e692e832464c72046da0be1a4a66d697f4333a1ea`。DLL原样保留。

INI启用enabled=1，slots由默认3改2。slots表示额外槽数：本项目原生4＋额外2＝总6，不设slots=6，不改baseAccSlotNum。INI文件名已核对为ExpandedTalismanSlots.ini，修改后SHA256 `94c108172ec844b25bc164cbf2eb3f37e70cf1494e5612e168de7dc9c190c8b3`；原注释保持。

## 已完成静态集成

scripts/integrate_six_talismans.py从作者原包和最新已发布ZIP生成三份运行替换／新增文件及审计，不生成ZIP：

- ModEngine/config_eldenring.toml：在[modengine]登记external_dlls中的ExpandedTalismanSlots.dll，其它设置保持。
- ModEngine/ExpandedTalismanSlots.dll：原作者文件。
- ModEngine/ExpandedTalismanSlots.ini：enabled=1、slots=2。

基准v0.10.13 ZIP SHA256 `826a740219061fd853f9ff35b0caa7944cec97dbb536cb2239cf3de86f79775e`。实际运行参数SHA256 `2e0cef01d8261610abbfdf0f1f6fb48d908535e1acdf09e1d557c7843ddbffc2`完全保持；981个非目标既有文件保持。配置原生DLL列表支持保留其他DLL；路径重复或冲突时拒绝盲目覆盖。对当前文件集重复执行相同结果。

调用：python scripts/integrate_six_talismans.py --base-zip <最新完整ZIP> --upstream-zip <用户提供原作者1.1.6ZIP> --output <工作目录>。

源码修订历史package_v0109.keep白名单，明确保留新增DLL／INI。较新的package_v0110～0113从完整基准读所有成员，但不会自动把独立输出目录的三份文件合进ZIP；05仍必须显式合入本模块三文件，再刷新README、SHA256_FILES.txt和新版本审计。最终包须读回核对DLL／INI／登记及总六槽设置，不能只提交源码。不要在旧发布脚本固定版本／固定文件数上强行复用假定。

## 游戏操作与ME3

按作者设计在赐福的Expanded Talisman Slots菜单装备额外护符；原生四槽与普通装备菜单同步。不是在原生装备画面追加两个可见格子。必须拥有实际护符。

包内BAT使用ME2配置即可；原生ME3启动必须在用户真实profile的[[natives]]注册该DLL，并保留Ascended文件mod路径，DLL／INI放一起。作者示例path = "eldenring-mods\\\\ExpandedTalismanSlots.dll"，该示例对应DLL直接放在该目录；实际将DLL放在Ascended/ModEngine时须把path改为该位置。仅设置ME3的mod目录不会加载DLL。没有读取用户本地ME3 profile，不能宣称已修改其启动配置；一次启动不要重复注册同一DLL。

## 检查与边界

通过：作者ZIP CRC、精确两文件、x64 PE DLL、INI真实名称／只改slots、加载TOML解析与既有设置保持、加两槽配置、981既有文件保持、无参数／事件／动作变化、幂等、10种INI／加载列表换行组合、打包白名单、源码编译／diff。

未运行Windows游戏。没有宣称赐福菜单、额外效果、重量、互斥及存档持久性已实机通过。实测：菜单总6槽、不能装第7个；第5／6护符效果生效及卸装解除；同族互斥／背包／重量；赐福、传送、死亡、退出重载和换角色；现有核心、小壶40%、莱昂提尔、心脏与高跳；分别测BAT和原生ME3入口。未生成新下载包、tag或Release，统一由05完成发布。
