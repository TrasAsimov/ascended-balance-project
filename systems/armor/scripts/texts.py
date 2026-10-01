"""Generate descriptions from final effect values and patch all English FMGs."""
from pathlib import Path
import json,sys,re
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT/'inputs'
sys.path.insert(0,str(ROOT.parents[1]/'scripts'))
from analyze_regulation import read_bnd
from field_diff import defs,fields,decode
from build_zhocn_patch import fmg_read,fmg_write,unpack
from formats import bnd_entries,bnd_patch,dcx_pack,dcx_unpack
from short_text import compact

_,result=read_bnd(ROOT/'data/result.bnd')
_,original=read_bnd(OLD/'work/vanilla.bnd')
_,before=read_bnd(OLD/'pending_v0105/adjusted.bnd')
groups=json.loads((ROOT/'data/sets.json').read_text());armors=json.loads((ROOT/'data/armor_index.json').read_text())
restore=json.loads((ROOT/'data/restoration.json').read_text());rr={str(r['armor_id']):r for r in restore}
official=json.loads((ROOT/'data/official_effect_fields.json').read_text())
lm={f[0]:f for f in fields(defs()[result['SpEffectParam']['ptype']])[0]}
la={f[0]:f for f in fields(defs()[result['EquipParamProtector']['ptype']])[0]}
reverse={v:int(k) for k,v in json.loads((ROOT/'data/original_effect_map.json').read_text()).items()}

def num(n):return f'{n:.5g}'
def pct(n):return num(round((n-1)*100,4))
CAT={6:('辉石彗星魔法','Glintstone Comet sorceries'),7:('辉石星类魔法','Glintstone star sorceries'),9:('荆棘魔法','Thorn sorceries'),11:('重力魔法','Gravity sorceries'),13:('寒冰魔法','Cold sorceries'),14:('彗星亚兹勒','Comet Azur'),15:('毁灭流星','Stars of Ruin'),16:('手指魔法','Finger sorceries'),17:('灵光环魔法','Spectral ring sorceries'),20:('神皮／黑焰祷告直接伤害','Godskin/blackflame direct incantation damage'),21:('巨人火焰祷告','Giantsflame incantations'),22:('古龙信仰祷告','Dragon Cult incantations'),24:('黄金律法祷告','Golden Order incantations'),25:('龙飨祷告','Dragon Communion incantations'),26:('癫火祷告','Frenzied Flame incantations'),27:('神皮贵族压腹祷告','Noble Presence'),28:('熔炉百相祷告','Aspects of the Crucible incantations'),31:('红熊咆哮战技','Red Bear roar skill'),32:('守护灵祷告','Watchful Spirit'),33:('梅瑟莫火焰祷告','Messmer fire incantations'),35:('神鸟羽毛祷告','Divine Bird Feathers'),37:('米凯拉的光祷告','Light of Miquella'),39:('该面具对应的原版祷告流派','The mask-supported original incantation school'),100:('蓄力普通重击','Charged regular heavy attacks'),102:('跳跃攻击','Jump attacks'),103:('防御反击','Guard counters'),104:('普通连段最后一击','Final regular combo attacks'),105:('箭矢','Arrows'),108:('投掷壶','Thrown pots'),111:('对应魔法类战技','Supported magic skills'),112:('对应寒冰类战技','Supported cold skills'),113:('弩箭','Bolts'),114:('祖灵婴儿头','Ancestral Infant Head'),115:('使者长笛战技','Envoy bubble skills'),118:('对应特殊箭矢','Supported special arrows'),121:('翻滚攻击','Rolling attacks'),122:('冲刺攻击','Running attacks'),124:('风暴类技能','Storm skills'),127:('踢击','Kicks'),129:('舞蹈战技','Dancing skills'),130:('火焰骑士战技','Fire Knight skills'),131:('投掷大壶','Hefty pots'),132:('鲜血系战技','Blood skills'),133:('对应古龙信仰战技','Supported Dragon Cult skills')}
ATTR={'LifeForce':('生命力','Vigor'),'Willpower':('集中力','Mind'),'Endure':('耐力','Endurance'),'Strength':('力量','Strength'),'Dexterity':('灵巧','Dexterity'),'Magic':('智力','Intelligence'),'Faith':('信仰','Faith'),'Luck':('感应','Arcane')}
RESIST={'Poison':('中毒','Poison'),'Disease':('腐败','Rot'),'Blood':('出血','Blood loss'),'Curse':('死疫','Death blight'),'Freeze':('冻伤','Frost'),'Sleep':('睡眠','Sleep'),'Madness':('发狂','Madness')}
ELEMENT={'physics':('物理','Physical'),'magic':('魔力','Magic'),'fire':('火焰','Fire'),'thunder':('雷电','Lightning'),'dark':('圣','Holy')}

def describe_original(eid):
    d=official[str(eid)];zh=[];en=[]
    def add(z,e):zh.append(z);en.append(e)
    for k,(z,e) in ATTR.items():
        n=d['add'+k+'Status']
        if n:add(f'{z} {n:+d}',f'{e} {n:+d}')
    for key,z,e in [('maxHpRate','最大生命值','Maximum HP'),('maxMpRate','最大 FP','Maximum FP'),('maxStaminaRate','最大精力','Maximum stamina'),('equipWeightChangeRate','装备重量上限','Equip load limit')]:
        if d[key]!=1:add(f'{z} ×{num(d[key])}',f'{e} x{num(d[key])}')
    for k,(z,e) in RESIST.items():
        n=d['change'+k+'ResistPoint']
        if n:add(f'{z}抗性 {n:+d} 点',f'{e} resistance {n:+d} points')
    for key,z,e in [('magicConsumptionRate','魔法 FP 消耗','Sorcery FP cost'),('miracleConsumptionRate','祷告 FP 消耗','Incantation FP cost'),('artsConsumptionRate','战技 FP 消耗','Skill FP cost'),('changeHpEstusFlaskCorrectRate','红露滴圣杯瓶回复量','Crimson flask recovery'),('changeMpEstusFlaskCorrectRate','蓝露滴圣杯瓶回复量','Cerulean flask recovery'),('physicsAttackPowerRate','物理攻击力','Physical attack power'),('magicDiffenceRate','魔力防御力','Magic defense')]:
        if d[key]!=1:add(f'{z} ×{num(d[key])}',f'{e} x{num(d[key])}')
    cats=[d['magicSubCategoryChange'+str(i)] for i in [1,2,3] if d['magicSubCategoryChange'+str(i)]]
    scopez='／'.join(CAT.get(c,(f'原版攻击分类 {c}',f'Original attack category {c}'))[0] for c in cats)
    scopee='/'.join(CAT.get(c,('',f'Original attack category {c}'))[1] for c in cats)
    rates={d[k+'AttackRate'] for k in ELEMENT}
    if len(rates)==1 and next(iter(rates))!=1:
        r=next(iter(rates));add(f'{scopez or "所有属性攻击"}伤害系数 ×{num(r)}',f'{scopee or "All attack types"} damage multiplier x{num(r)}')
    else:
        for k,(z,e) in ELEMENT.items():
            if d[k+'AttackRate']!=1:add(f'{scopez}的{z}伤害系数 ×{num(d[k+"AttackRate"])}',f'{scopee} {e} damage multiplier x{num(d[k+"AttackRate"])}')
    if d['atkEnemyDmgCorrectRate_Physics']!=1:
        a=d['atkEnemyDmgCorrectRate_Physics'];p=d['atkPlayerDmgCorrectRate_Physics']
        add(f'{scopez or "所有"}伤害：对敌人 ×{num(a)}；对玩家 ×{num(p)}',f'{scopee or "All"} damage: versus enemies x{num(a)}; versus players x{num(p)}')
    cuts=[d[x+'DamageCutRate'] for x in ['slash','blow','thrust','neutral','magic','fire','thunder','dark']]
    if len(set(cuts))==1 and cuts[0]!=1:add(f'所有类型承伤 ×{num(cuts[0])}',f'All damage received x{num(cuts[0])}')
    if d['targetPriority']:add(f'吸引敌人注意（目标优先级 {d["targetPriority"]:+.2f}）',f'Draw enemy attention (target priority {d["targetPriority"]:+.2f})')
    if eid==6018010:add('消除移动脚步声','Silences movement footsteps')
    if 6021000<=eid<=6021110:
        add(f'翻滚碰撞的原版攻击力基值 {d["physicsAttackPower"]}；最终伤害受目标防御影响',f'Original rolling-collision base attack power {d["physicsAttackPower"]}; final damage depends on target defense')
    if eid==6044000:add('保留原版头部命中防护规则；其独立百分比不能由该装备参数确认','Preserves original headshot protection; no independent percentage is exposed by this armor parameter')
    if 6069000<=eid<=6069030:add('生命值不高于 18% 时，按原版机制每秒恢复 2 HP','At or below 18% HP, original regeneration restores 2 HP/s')
    if eid==6193010:add('半径 7 米内友方每秒恢复 2 HP（不治疗自身）','Allies within 7m restore 2 HP/s (not self-healing)')
    if eid in [1950,1952,1954,1956,1958,486]:add('保留对应头冠的原版外观／发光规则','Preserves the crown visual/glow rule')
    if eid==6518200:add('骨灰召唤 FP 消耗按原版死亡面具规则减少 15%','Spirit summon FP cost reduced by 15% through the original Death Mask rule')
    if eid==6068000:add('附近发生出血后：对敌人伤害 +10%、对玩家 +6%，持续 20 秒','Blood loss nearby: damage versus enemies +10%, versus players +6%, for 20s')
    if eid==6201000:add('附近发生中毒或腐败后，伤害 +10%，持续 600 秒','Poison/rot nearby: damage +10% for 600s')
    if eid==6202000:add('自身发狂后，伤害 +10%，持续 600 秒','After suffering madness: damage +10% for 600s')
    if not zh:add('保留原版特殊效果及全部触发条件','Preserves the original special effect and its complete trigger conditions')
    return '；'.join(zh),'; '.join(en)

MOD={6202002:('最大生命值 +30%','Maximum HP +30%'),6202003:('最大 FP +30%','Maximum FP +30%'),6202004:('最大精力 +30%','Maximum stamina +30%'),6202016:('装备重量上限 +30%','Equip load limit +30%'),6202017:('血瓶与蓝瓶回复倍率 ×1.35；寿命防御系数 ×1.6（此系数不作为血瓶／蓝瓶回复倍率）','Crimson/Cerulean flask recovery x1.35; life-reduction defense coefficient x1.6 (not a flask recovery multiplier)'),6202018:('施法速度用的虚拟灵巧 +90（不增加面板灵巧；受施法速度上限限制）','Virtual Dexterity for casting speed +90 (no character Dexterity increase; subject to casting speed cap)'),6202019:('对重力生物标记 A 的敌人伤害 ×1.30（如白王、黑王、艾丝缇、坠星兽）','Damage versus gravity-creature flag A x1.30 (e.g. Alabaster/Onyx Lords, Astel, Fallingstar Beasts)'),6202020:('对不死标记 B 的敌人伤害 ×1.30','Damage versus undead flag B x1.30'),6202021:('对龙族标记 D 的敌人伤害 ×1.30','Damage versus dragon flag D x1.30'),6202039:('每 0.5 秒恢复 30 HP','Restore 30 HP every 0.5s'),6202040:('每 2 秒恢复 30 FP','Restore 30 FP every 2s'),6202041:('每 2 秒恢复 40 FP','Restore 40 FP every 2s'),6351:('常规受击动作等级被设为 1；不增加面板强韧度','Regular hit-reaction grades set to 1; does not increase displayed poise'),322100:('投掷壶伤害 +70%','Thrown pot damage +70%'),6201000:('附近发生中毒或腐败后，原版触发增伤 ×1.10，持续 20 秒','Poison/rot nearby: original triggered damage x1.10 for 20s')}
for e,(zh,en) in zip(range(6202005,6202012),[('斩击','Slash'),('打击','Strike'),('突刺','Pierce'),('标准物理','Standard physical'),('魔力','Magic'),('火焰','Fire'),('雷电','Lightning')]):MOD[e]=(f'{zh}承伤 -30%',f'{en} damage received -30%')
MOD[6202022]=('圣属性承伤 -30%','Holy damage received -30%')
for e,(zh,en) in zip([6202012,6202013,6202014,6202015,6202058],ELEMENT.values()):MOD[e]=(f'{zh}攻击力 +100',f'{en} attack power +100')
for e,(zh,en) in zip(range(6202023,6202030),[RESIST[k] for k in ['Poison','Disease','Blood','Curse','Freeze','Madness','Sleep']]):MOD[e]=(f'{zh}抗性 +400 点',f'{en} resistance +400 points')
for e,k in zip([6202030,6202031,6202032,6202034,6202035,6202036,6202037,6202038],ATTR):
    zh,en=ATTR[k];MOD[e]=(f'{zh} +30',f'{en} +30')

def effect_lines(label, effects, language):
    # Separate effects without discarding their enclosing trigger or scope.
    separator='；' if language=='zh' else ';'
    fragments=[part.strip() for effect in effects for part in effect.split(separator) if part.strip()]
    return [(label+' · ' if i==0 else '    ')+part for i,part in enumerate(fragments)]

def display_name(name):
    for note in ['（官方装束家族）','（单件家族）','（单件）','（六种单件）','（旧版／Mod条目）','（Mod条目）','（暂译）']:
        name=name.replace(note,'')
    return name

texts={}
for s,r in armors.items():
    rid=int(s);body=result['EquipParamProtector']['rows'][rid]['data']
    resident=[decode(body,la[k]) for k in ['residentSpEffectId','residentSpEffectId2','residentSpEffectId3']]
    g=groups[r['key']]
    z=[display_name(g['name'])+f"（{g['full']}件）",'']
    e=[g['english_name']+f" ({g['full']} {'piece' if g['full']==1 else 'pieces'})",'']
    singles_z=[];singles_e=[]
    for eid in rr.get(s,{}).get('official_ids',[]):
        zh,en=describe_original(eid)
        zh,en=compact(zh,'zh'),compact(en,'en')
        if zh:singles_z.append(zh)
        if en:singles_e.append(en)
    for eid in resident:
        if eid<=0 or eid in reverse:continue
        assert eid in MOD,('missing resident description',rid,eid)
        zh,en=MOD[eid];singles_z.append(compact(zh,'zh'));singles_e.append(compact(en,'en'))
    # One-slot families use the same single-piece block, without a duplicate label.
    for reward in g['rewards']:
        if reward['tier']==1:
            singles_z.append(compact(reward['zh'],'zh'))
            singles_e.append(compact(reward['en'],'en'))
    z.extend(effect_lines('单件',singles_z,'zh'));e.extend(effect_lines('Piece',singles_e,'en'))
    tiers=sorted({x['tier'] for x in g['rewards'] if x['tier']>1})
    if tiers and singles_z:z.append('')
    if tiers and singles_e:e.append('')
    for tier in tiers:
        rewards=[x for x in g['rewards'] if x['tier']==tier]
        zh=[compact(x['zh'],'zh') for x in rewards]
        en=[compact(x['en'],'en') for x in rewards]
        if tier>2 and any(x['exclusive'] for x in g['rewards']):
            zh[-1]+='（替换2件）';en[-1]+=' (replaces 2 pcs)'
        z.extend(effect_lines(f'{tier}件',zh,'zh'))
        e.extend(effect_lines(f'{tier} pcs',en,'en'))
    texts[s]={'zh':'\n'.join(z).rstrip(),'en':'\n'.join(e).rstrip(),'set':g['name'],'name':r['name']}
(ROOT/'data/description_zh.json').write_text(json.dumps({k:v['zh'] for k,v in texts.items()},ensure_ascii=False,indent=2))
(ROOT/'data/description_en.json').write_text(json.dumps({k:v['en'] for k,v in texts.items()},ensure_ascii=False,indent=2))

stats={}
for name in ['item_dlc01','item_dlc02']:
    p=OLD/'pending_v0105/ModEngine/mod/msg/engus'/f'{name}.msgbnd.dcx'
    raw=unpack(p.read_bytes());parts=bnd_entries(raw);updates={};covered=set()
    for fname,(_,data) in parts.items():
        if fname.startswith('AccessoryCaption'):
            entries=fmg_read(data)
            coretext={2090:'Critical damage +400%.',2120:'Combo final hit damage +250%.',2130:'Charged heavy attack damage +300%.',2140:'Sorcery/incantation attack power +220%.',2150:'Arrow/bolt damage +100%.',2180:'Jump attack damage +100%.',2200:'Guard counter damage +300%.',4100:'Guard stamina cost -50%.'}
            for rid,line in coretext.items():
                if rid in entries:
                    entries[rid]=line
            updates[fname]=fmg_write(entries)
            continue
        if not fname.startswith('ProtectorCaption'):continue
        suffix=fname[len('ProtectorCaption'):]
        nf='ProtectorName'+suffix
        nentries=fmg_read(parts[nf][1]);entries=fmg_read(data)
        for s,v in texts.items():
            rid=int(s)
            if rid not in nentries:continue
            entries[rid]=v['en'];covered.add(rid)
        updates[fname]=fmg_write(entries)
    assert len(covered)==len(texts),(name,len(covered),len(texts))
    raw=bnd_patch(raw,updates);packed=dcx_pack(raw)
    assert dcx_unpack(packed)==raw
    out=ROOT/'ModEngine/mod/msg/engus'/f'{name}.msgbnd.dcx';out.write_bytes(packed)
    check=bnd_entries(dcx_unpack(packed));assert all(check[k][1]==p[1] for k,p in parts.items() if k not in updates)
    stats[name]=len(covered)

doc=['# 护甲套装系统实现清单','',
     '当前为可安装测试版：完成参数和事件生成、回读与静态检查，尚需游戏实测。基于 v0.10.4 高跳集成版及 pending_v0105 平衡调整。',
     '', '原版单件特色和代价优先恢复；蘑菇王冠、黑头罩的时长及神兽头部属性按用户指定调整；同 ID 的具体叠加次数仍需游戏验证。套装检测只读实际穿戴槽，使用独立效果 ID。本次提交为护甲与核心伤害平衡的源代码及检查记录；未生成下载包或 Release。',
     '', '## 全套目录','', '| 套装家族 | 穿戴槽数 | 两件奖励 | 满套额外／替换奖励 |','|---|---:|---|---|']
for g in groups.values():
    two='；'.join(r['zh'] for r in g['rewards'] if r['tier']==2) or ('新增单件：'+'；'.join(r['zh'] for r in g['rewards'] if r['tier']==1) if g['full']==1 and g['rewards'] else '无')
    full='；'.join(r['zh'] for r in g['rewards'] if r['tier']>2) or '无'
    if any(x['exclusive'] for x in g['rewards']) and g['full']>2:full+='（替换两件奖励）'
    doc.append(f'| {g["name"]}（{g["key"]}） | {g["full"]} | {two} | {full} |')
doc+=['','## 逐件准确描述','']
for s,v in texts.items():doc += [f'### {v["name"]} — {s}','',v['zh'],'']
(ROOT/'docs/ARMOR_SYSTEM.md').write_text('\n'.join(doc))
(ROOT/'data/text_manifest.json').write_text(json.dumps(stats,indent=2))
print('descriptions',len(texts),'English archives',stats)
