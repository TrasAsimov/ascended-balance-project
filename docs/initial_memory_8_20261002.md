# 初始基础记忆槽8个（06，待05整合）

用户要求初始人物自带8个魔法／祷告槽位，按所有职业的基础记忆槽处理。最新v0.10.9的PlayerCommonParam行0.baseMagicSlotSize仍为2，现仅改为8。魔法和祷告共用同一记忆容量，不是各8个，也不是随附8个法术。

基础值为共享玩家参数；新角色无需先拿记忆石或戴加槽护符。已有角色预期也采用新的基础值，已有记忆石／装备加槽继续按引擎规则作用，实际总数可能高于8，需实机确认。本轮没有修改记忆石、道具旗标、护符、职业出生装备、法术slotLength、菜单／存档容量上限或存档文件。占用多槽的法术仍按现有槽数扣除。保留4护符栏baseAccSlotNum=4。

输入是已发布v0.10.9整合包内唯一regulation.bin，SHA256 `ccf28375c2eda8d6ea4d8521f186c23a5c579d99da4e92ce8c6f23299d1ba99a`。继承最新看门犬战灰、大盾80%、原生武器异常恢复、床帘恩泽120秒、蓝露滴10FP/s和其它审计回蓝5FP/s、核心、心脏、护甲套装及法术异常50%。不使用前轮床帘30分钟独立候选。

输出06_Initial_Memory_8_20261002_regulation.bin，2284528字节；SHA256 `968adbda6c2b2cbace361af0e679d2fc308b1640d7c320c9a2dc46552fdfab4d`。PlayerCommonParam整体只变1字节，行内偏移12的2→8；其余193张表完全保持。匹配定义行尺寸256，单行PARAM推断会包含8字节填充而显示264，本脚本用真实定义尺寸及独立目录检查，保留所有不透明尾部。参数目录、名字、字段、加密回读、幂等、编译、diff及源码补丁apply检查通过；游戏未运行。

源码scripts/set_initial_memory_slots.py，需要匹配的ARMOR_PARAMDEFS及ARMOR_REGULATION_KEY_HEX环境变量，无新嵌入式密钥：

```bash
python scripts/set_initial_memory_slots.py --input <最新regulation.bin> --output <输出regulation.bin> --audit <审计.json>
```

独立bin只替换实际加载的ModEngine/mod/regulation.bin，不更换common或文本。05在最终最新参数上执行幂等脚本，不用整文件覆盖未来更新；本轮无ZIP、GitHub写入、tag或Release，v0.10.9已发布附件未更新。

测试新建任一职业，到赐福记忆法术菜单确认未持记忆石／未戴加槽装备时为8槽，装备魔法与祷告共同消耗容量，跨过原2槽的位置能够记忆／轮换／施放；测试多槽法术、记忆石、加槽护符和旧角色，保存退出重载后保持。静态验证不等于上述实机验收。
