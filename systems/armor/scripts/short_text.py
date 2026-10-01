"""Compact player text: retain values and essential scope, remove provenance/lore."""
import re

def compact(text, language, independent=False):
    if language=='zh':
        replacements={
            '普通连段最后一击':'连击末段','精力恢复速度':'精力恢复',' 点/秒':'/秒','蓄力普通重击':'蓄力重击','背刺与处决':'背刺/处决','削韧系数':'削韧',
            '附近发生出血时，所有伤害':'附近出血时，伤害',
            '附近发生中毒或腐败时，所有伤害':'附近中毒/腐败时，伤害',
            '；再次触发刷新时间':'，可刷新','持续 600 秒':'600秒',
            '（魔法剑士对应的战技类别）':'（魔法剑士适用战技）',
            '神皮／黑焰类直接攻击祷告':'神皮/黑焰直接祷告',
            '（不放大持续百分比灼烧）':'','（不含香药）':'',
            '所有行动的精力消耗':'行动耗精','（含格斗武器）':'',
            '对参数标记为龙类（D）的敌人':'对龙类敌人',
            '弓箭飞行距离修正':'弓箭距离',' 个百分点':'百分点',
            '敌人对自身的听觉侦测距离系数':'敌人听觉侦测距离',
            '受到敌人的物理与各属性伤害':'敌人造成的伤害',
            '施法速度用的虚拟灵巧 +90（不增加面板灵巧；受施法速度上限限制）':'施法虚拟灵巧 +90',
            '对重力生物标记 A 的敌人伤害':'对重力生物伤害',
            '（如白王、黑王、艾丝缇、坠星兽）':'',
            '对不死标记 B 的敌人伤害':'对不死敌人伤害',
            '对龙族标记 D 的敌人伤害':'对龙类敌人伤害',
            '（此系数不作为血瓶／蓝瓶回复倍率）':'',
            '常规受击动作等级被设为 1；不增加面板强韧度':'受击动作等级 1',
            '血瓶与蓝瓶':'红/蓝瓶','红露滴与蓝露滴圣杯瓶':'红/蓝瓶',
            '红露滴圣杯瓶':'红瓶','蓝露滴圣杯瓶':'蓝瓶','装备重量上限':'负重上限',
            '保留原版头部命中防护规则；其独立百分比不能由该装备参数确认':'头部命中防护',
            '保留对应头冠的原版外观／发光规则':'',
            '保留原版特殊效果及全部触发条件':'特殊单件效果',
            '按原版死亡面具规则':'','按原版机制':'',
            '翻滚碰撞的原版攻击力基值':'翻滚碰撞攻击力',
            '；最终伤害受目标防御影响':'',
            '（不治疗自身）':'（仅友方）',
            '附近发生中毒或腐败后，':'附近中毒/腐败后，',
            '附近发生出血后：':'附近出血后：',
            '原版触发增伤':'伤害',
        }
        for old,new in replacements.items():text=text.replace(old,new)
        text=re.sub(r'[×x](\d+(?:\.\d+)?)', lambda m: f'{(float(m[1])-1)*100:+.5g}%', text)
        text=text.replace('原版','').strip('；。 ')
    else:
        replacements={
            ' points/s':'/s','damage received':'damage taken','Equip load limit':'Max equip load','Charged regular heavy attack':'Charged heavy attack',
            'Final regular combo attack':'Combo final hit',
            '(Spellblade-supported skill categories)':'(Spellblade skills)',
            '(not percentage HP burn)':'','(not perfumes)':'',
            'Blood loss nearby: all damage':'Nearby bleed: damage',
            'Poison or rot nearby: all damage':'Nearby poison/rot: damage',
            '; retrigger refreshes duration':', refreshable',
            'All action stamina cost':'Action stamina cost',
            '(including martial arts)':'',
            'Damage to enemies flagged dragon type D':'Damage to dragons',
            'Bow flight-distance correction':'Bow range',
            'Enemy hearing detection range against you':'Enemy hearing range',
            'Virtual Dexterity for casting speed +90 (no character Dexterity increase; subject to casting speed cap)':'Casting virtual Dexterity +90',
            'Damage versus gravity-creature flag A':'Damage to gravity creatures',
            '(e.g. Alabaster/Onyx Lords, Astel, Fallingstar Beasts)':'',
            'Damage versus undead flag B':'Damage to undead',
            'Damage versus dragon flag D':'Damage to dragons',
            '(not a flask recovery multiplier)':'',
            'Regular hit-reaction grades set to 1; does not increase displayed poise':'Hit-reaction grade 1',
            'Preserves original headshot protection; no independent percentage is exposed by this armor parameter':'Headshot protection',
            'Preserves the crown visual/glow rule':'',
            'Preserves the original special effect and its complete trigger conditions':'Special piece effect',
            'Original rolling-collision base attack power':'Rolling-collision attack power',
            '; final damage depends on target defense':'',
            'original regeneration restores':'restore',
            'through the original Death Mask rule':'',
            '(not self-healing)':'(allies only)',
            'original triggered damage':'damage',
        }
        for old,new in replacements.items():text=text.replace(old,new)
        text=re.sub(r'[×x](\d+(?:\.\d+)?)', lambda m: f'{(float(m[1])-1)*100:+.5g}%', text).strip('; . ')
    return re.sub(r' +', ' ', text).strip()
