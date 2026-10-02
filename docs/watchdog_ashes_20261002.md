# 看门犬杖恢复战灰安装（06，待05统一整合）

用户实测看门犬杖不能像其它武器安装战灰。当前 EquipParamWeapon 23010000 的 gemMountType=0；旧 pending_watchdog_no_skill.csv 记录去掉默认战技时将这个字段由2改为0，是直接的安装禁用。最近武器异常恢复只处理命中特效、常驻异常、显示与异常补正，不改此字段。

只把 gemMountType 0→2，与当前可安装战灰的特大武器一致。保留默认无战技 swordArtsParamId=10、出生武器309/329使用的30900无战技预设，不重新加入原来的1192。武器类型仍为41（特大武器），按战灰自身 canMountWep_AxhammerLarge 筛选，不能把名称中的杖误作魔法杖类别。

保留 disableGemAttr=1、reinforceTypeId=2200、materialSetId=2200：标准属性、失色强化。当前只有23010000，没有其它质变行；本次修复战灰安装，不补造质变、血／毒／冻伤数据或修改共享战灰适用范围。卸下战灰仍回到无战技基线。

最终输入为07床帘恩泽30分钟候选，SHA256 `79df4acf44b31e2f298b0f3f71a3f81c905435fb298d4109b758f9b956cc1c8b`。输出06_Watchdog_Ashes_20261002_regulation.bin，2284528字节，SHA256 `275597089717ec4945df97758efd4874d99478643a1970a6a41da21bcde9d07a`。保留06武器固有异常恢复、01大盾80%、07床帘恩泽30分钟、法术异常50%、心脏／核心与套装。

整个武器PARAM只有1字节改变；其它3637行、193张表、目录、行名、偏移、全部其它武器字段均保持。独立已知行尺寸目录和不重叠检查、紧凑BND、加密回读、幂等、编译与源码补丁apply检查通过。游戏未运行。

后处理脚本：scripts/fix_watchdog_ashes.py。设置匹配的 ARMOR_PARAMDEFS 与 ARMOR_REGULATION_KEY_HEX 后执行：

```bash
python scripts/fix_watchdog_ashes.py --input <最新regulation.bin> --output <输出regulation.bin> --audit <审计.json>
```

旧 build_pending_watchdog_no_skill.py 同步保持安装开关为2，跳过已达到目标的字段，防止今后重建再次禁用战灰。旧CSV保留历史变更事实；本轮实际结果见changes/watchdog_ashes_20261002.json。

只需替换实际加载的ModEngine/mod/regulation.bin；若使用包根目录副本，也同步它。无需替换事件或文本，应保留02最新面罩归属common与07最新文字。05在最终最新参数上运行脚本，不能用独立文件覆盖未来修改。无ZIP、远程写入、tag或Release。

游戏验收：用现有看门犬杖在赐福或铁匠处安装已拥有且适用特大武器的战灰（例如Stamp／箭步上砍）；确认只能标准属性，战技可发动，卸下回无战技，保存退出重载后仍正确；出生预设309/329也需核对。检查失色强化、武器固有异常恢复、法术50%、套装、大盾80%和床帘恩泽30分钟未回退。不能宣称静态候选已通过实机安装或存档验收。
