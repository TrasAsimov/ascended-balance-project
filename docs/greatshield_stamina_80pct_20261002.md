# 大盾护符：格挡精力消耗减少80%

用户09:49反馈原50%减耗仍不扣精力，09:50要求至少减少80%。以v0.10.8实际安装参数为基准实现80%减耗，而非免耗。

## 定位与改动

EquipParamAccessory 4100实际引用SpEffect 341000，不能把护符物品ID4100当效果ID。v0.10.8该效果guardStaminaCutRate=0.5；但真正的guardStaminaMult位于912字节行的0x388（904），值为0。官方1.17.1同字段为0.8。旧参数定义错误地把这一字段连同最后4字节归为pad3[8]，逐字段差分此前忽略了它。这是零消耗的明确参数原因，游戏执行仍需验证。

libER当前ELDEN RING结构和Smithbox ER注释识别此字段为格挡精力倍率：
https://dasaav-dsv.github.io/libER/d9/d22/SP__EFFECT__PARAM__ST_8hpp_source.html
https://github.com/vawser/Smithbox/blob/main/src/Smithbox.Data/Assets/PARAM/ER/Param%20Annotations/English/SP_EFFECT_PARAM_ST.json

仅修改341000两项：guardStaminaCutRate 0.5→1，guardStaminaMult 0→0.2。保留stateInfo158、适用对象、效果引用、其它字段及最后4字节。消耗按同盾同攻击不戴护符的正常格挡剩余成本再乘0.2，不提高盾牌防御强度，不改变攻击/翻滚/奔跑精力成本。

例：同一攻击原格挡消耗50/20/5，佩戴后模型为10/4/1。理论正值小于1时可能因引擎取整或显示分辨率看不出扣条；也不能保证原本零消耗的攻击、100防御强度或其它免耗效果变成非零。

发现其它stateInfo158旧效果亦有尾部0值，含801等盾牌附魔/其它效果。本轮仅修大盾护符，未批量恢复所有旧效果或改动套装字段；测试须先不叠加其它盾牌附魔/战技与格挡奖励。若仍零耗，要单独定位这些额外生效效果，不继续盲调护符百分比。

## 验证与交接

193非目标表体、全部其它SpEffect行和所有行名逐字节不变；仅允许目标两段4字节改变。加密回读、幂等、400个防御强度/攻击精力模型、编译和diff检查通过。英文输入采用02最新护甲/盾牌Effect排版交接version1（libfile_535bd53698e8819180319b5f97ab16ae、libfile_697d5ebcf24c8191aee649686c733e0c），两份英文只改AccessoryCaption.fmg护符4100正文为80%；中文合并源同步。游戏未运行，不能宣布实机已修好。

脚本scripts/fix_greatshield_stamina.py支持旧定义pad3或新定义guardStaminaMult，并验证0x388及912行长；不把格式密钥写入源码。需要ARMOR_REGULATION_KEY_HEX。scripts/update_greatshield_stamina_text.py独立改英文正文。

05统一集成时，在最终v0.10.8之后参数或更晚BUG修复输入上执行一次本修正，不用独立bin覆盖较晚武器异常等模块；英文文本同样在最新输入上改正文。保持已有心脏、异常50%、核心×4/×3.2、护甲等。不生成ZIP/tag/Release，本模块源码留独立patch统一提交。

复测：v0.10.8玩家只替换候选bin即可测试数值；common不变。关闭其它盾牌附魔/格挡套装增益，以同盾同攻击比较摘下→佩戴→摘下的实际精力数值，测试小盾/中盾/大盾，确认正常格挡仍耗精力，攻击和翻滚消耗不变；再单独加入其它增益检查叠加。实际80%比例、启动/读档/保存尚待玩家测试。
