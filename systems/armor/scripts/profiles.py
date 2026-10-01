"""Final implementable reward profiles. Text and parameter values share one source."""
RATE_FIELDS=['physicsAttackRate','magicAttackRate','fireAttackRate','thunderAttackRate','darkAttackRate']
def reward(zh,en,fields=None,template=0,chains=None):
    return dict(zh=zh,en=en,fields=fields or {},template=template,chains=chains or [])
def damage(zh,en,rate,subcats=(),template=0):
    f={k:rate for k in RATE_FIELDS}
    f.update({f'magicSubCategoryChange{i+1}':n for i,n in enumerate(subcats)})
    return reward(zh,en,f,template)
def crit(rate):return damage(f'背刺与处决伤害 +{round((rate-1)*100)}%',f'Critical attack damage +{round((rate-1)*100)}%',rate,template=320900)
def trigger(state,rate,duration):
    f={f'atk{t}DmgCorrectRate_{a}':rate for t in ['Player','Enemy'] for a in ['Physics','Magic','Fire','Thunder','Dark']}
    child=reward('', '',dict(f,effectEndurance=duration,iconId=-1,vfxId=-1),6068001)
    return reward(f'附近发生{"出血" if state==379 else "中毒或腐败"}时，所有伤害 +{round((rate-1)*100)}%，持续 {duration} 秒；再次触发刷新时间',
                  f'{"Blood loss" if state==379 else "Poison or rot"} nearby: all damage +{round((rate-1)*100)}% for {duration}s; retrigger refreshes duration',
                  {'invocationConditionsStateChange1':state},6068000,[child])
P={}
P['guard']=([reward('格挡精力消耗 -8%','Guarding stamina cost -8%',{'guardStaminaCutRate':.92})],
             [damage('防御反击伤害 +12%','Guard counter damage +12%',1.12,(103,))])
P['heavy']=([damage('蓄力普通重击伤害 +8%','Charged regular heavy attack damage +8%',1.08,(100,))],
             [reward('蓄力普通重击削韧系数 +10%','Charged regular heavy attack stance damage +10%',{'magicSubCategoryChange1':100,'saAttackPowerRate':1.10})])
P['light']=([reward('精力恢复速度 +4 点/秒','Stamina recovery +4 points/s',{'staminaRecoverChangeSpeed':4})],
             [damage('普通连段最后一击伤害 +10%','Final regular combo attack damage +10%',1.10,(104,))])
P['stealth']=([reward('敌人对自身的听觉侦测距离系数 ×0.80','Enemy hearing detection range against you x0.80',{'hearingSearchEnemyRate':.8})],[crit(1.15)])
P['crit']=([crit(1.08)],[crit(1.15)]) # full replaces 2-piece to avoid two conditional critical multipliers
P['sorcery']=([reward('魔法 FP 消耗 -6%','Sorcery FP cost -6%',{'magicConsumptionRate':.94})],
               [damage('魔法伤害 +8%','Sorcery damage +8%',1.08,template=330010)])
P['incant']=([reward('祷告 FP 消耗 -6%','Incantation FP cost -6%',{'miracleConsumptionRate':.94})],
              [reward('祷告伤害 +8%','Incantation damage +8%',dict({k:1.08 for k in RATE_FIELDS},magParamChange=0,miracleParamChange=1),330010)])
P['magic_skill']=([reward('魔力属性战技伤害 +8%（魔法剑士对应的战技类别）','Magic skill damage +8% (Spellblade-supported skill categories)',{'magicAttackRate':1.08},6013000)],
                   [reward('所有战技 FP 消耗 -10%','All skill FP costs -10%',{'artsConsumptionRate':.90})])
for code,field,resist,title in [('fire','fireAttackRate','fireDamageCutRate','火焰'),('holy','darkAttackRate','darkDamageCutRate','圣'),('lightning','thunderAttackRate','thunderDamageCutRate','雷电')]:
    P[code]=([reward(f'{title}属性伤害 +6%',f'{code.title()} damage +6%',{field:1.06})],
              [reward(f'受到的{title}属性伤害 -10%',f'{code.title()} damage received -10%',{resist:.90})])
P['blackflame']=([damage('神皮／黑焰类直接攻击祷告伤害 +8%（不放大持续百分比灼烧）','Godskin/blackflame direct incantation damage +8% (not percentage HP burn)',1.08,template=1922)],
                  [reward('所有祷告 FP 消耗 -10%','All incantation FP costs -10%',{'miracleConsumptionRate':.90})])
P['frost']=([reward('冻伤抗性 +80 点','Frost resistance +80 points',{'changeFreezeResistPoint':80})],
             [damage('寒冰魔法伤害 +8%','Cold sorcery damage +8%',1.08,template=6101000)])
P['bleed']=([reward('感应 +3','Arcane +3',{'addLuckStatus':3})],[trigger(379,1.08,15)])
P['poison']=([reward('中毒与腐败抗性各 +80 点','Poison and rot resistance +80 points each',{'changePoisonResistPoint':80,'changeDiseaseResistPoint':80})],[trigger(380,1.08,20)])
P['rot']=([reward('腐败抗性 +100 点','Rot resistance +100 points',{'changeDiseaseResistPoint':100})],[trigger(380,1.08,20)])
P['dragon']=([damage('龙飨祷告直接伤害 +8%','Dragon Communion direct incantation damage +8%',1.08,template=1927)],
              [reward('对参数标记为龙类（D）的敌人伤害 +10%','Damage to enemies flagged dragon type D +10%',{'weakDmgRateD':1.10})])
P['crucible']=([damage('熔炉百相祷告伤害 +8%','Aspects of the Crucible incantation damage +8%',1.08,template=6057000)],P['guard'][1])
P['bow']=([damage('箭矢与弩箭伤害 +8%','Arrow and bolt damage +8%',1.08,template=321500)],
           [reward('弓箭飞行距离修正 +25 个百分点','Bow flight-distance correction +25 percentage points',{'bowDistRate':25},321000)])
P['jump']=([damage('跳跃攻击伤害 +8%','Jump attack damage +8%',1.08,(102,))],
            [reward('跳跃攻击削韧系数 +10%','Jump attack stance damage +10%',{'magicSubCategoryChange1':102,'saAttackPowerRate':1.10})])
P['counter']=([damage('防御反击伤害 +8%','Guard counter damage +8%',1.08,(103,))],
               [reward('防御反击削韧系数 +12%','Guard counter stance damage +12%',{'magicSubCategoryChange1':103,'saAttackPowerRate':1.12})])
def flask(n):return reward(f'红露滴与蓝露滴圣杯瓶回复量 +{n}%',f'Crimson/Cerulean flask recovery +{n}%',{'changeHpEstusFlaskCorrectRate':1+n/100,'changeMpEstusFlaskCorrectRate':1+n/100})
P['flask']=([flask(8)],[flask(15)])
def pots(n):return damage(f'投掷壶与大壶伤害 +{n}%（不含香药）',f'Thrown pot and hefty pot damage +{n}% (not perfumes)',1+n/100,(108,131))
P['craft']=([pots(8)],[pots(15)])
P['regen']=([reward('每 5 秒恢复最大生命值的 1%','Restore 1% max HP every 5s',{'motionInterval':5,'changeHpRate':-1,'stateInfo':50})],
             [reward('生命值低于 30% 时，每 5 秒恢复最大生命值的 2%；否则恢复 1%','Restore 2% max HP every 5s below 30% HP; otherwise 1%',{'motionInterval':5,'changeHpRate':-2,'stateInfo':50})])
P['martial']=([reward('所有行动的精力消耗 -8%（含格斗武器）','All action stamina cost -8% (including martial arts)',{'consumeStaminaRate':.92})],P['heavy'][0])
P['spirit']=([reward('最大 FP +8%','Maximum FP +8%',{'maxMpRate':1.08})],
              [reward('受到敌人的物理与各属性伤害 -8%','Damage received from enemies -8%',{f'defEnemyDmgCorrectRate_{t}':.92 for t in ['Physics','Magic','Fire','Thunder','Dark']})])
P['frenzy']=([damage('癫火祷告直接伤害 +8%','Frenzied Flame direct incantation damage +8%',1.08,template=1928)],
              [reward('发狂抗性 +80 点','Madness resistance +80 points',{'changeMadnessResistPoint':80})])
P['dance']=([damage('舞蹈战技伤害 +8%','Dancing skill damage +8%',1.08,template=6508000)],P['magic_skill'][1])
P['bloodmagic']=([damage('荆棘魔法伤害 +8%','Thorn sorcery damage +8%',1.08,template=6012000)],
                  [reward('所有魔法 FP 消耗 -10%','All sorcery FP costs -10%',{'magicConsumptionRate':.90})])
P['bloodskill']=([damage('鲜血系战技伤害 +8%','Blood skill damage +8%',1.08,template=6511010)],P['magic_skill'][1])
P['gravity']=([damage('重力魔法伤害 +8%','Gravity sorcery damage +8%',1.08,template=1920)],P['magic_skill'][1])
P['throw']=([pots(8)],[pots(10)])
P['sleep']=([reward('睡眠抗性 +80 点','Sleep resistance +80 points',{'changeSleepResistPoint':80})],
             [reward('最大 FP +8%','Maximum FP +8%',{'maxMpRate':1.08})])
REPLACE={'crit','flask','craft'}

def identify(text):
    if '鲜血系战技' in text:return 'bloodskill'
    for needle,code in [('持盾','guard'),('蓄力重击','heavy'),('精力恢复','light'),('听觉','stealth'),('背刺','crit'),('魔法消耗','sorcery'),('魔力属性战技','magic_skill'),('祷告消耗','incant'),('火焰属性','fire'),('黑焰','blackflame'),('圣属性','holy'),('雷电属性','lightning'),('冻伤','frost'),('出血异常','bleed'),('中毒与','poison'),('猩红腐败','rot'),('龙飨','dragon'),('熔炉百相','crucible'),('弓箭','bow'),('跳跃攻击','jump'),('防御反击','counter'),('血瓶','flask'),('壶类','craft'),('每 5 秒','regen'),('徒手','martial'),('召唤骨灰','spirit'),('癫火','frenzy'),('舞蹈','dance'),('荆棘','bloodmagic'),('重力','gravity'),('投掷道具','throw'),('睡眠异常','sleep')]:
        if needle in text:return code
    if text.startswith('—'):return None
    raise ValueError(text)

# Approved spreadsheet revision, 2026-10-01. Unmentioned tiers remain intact.
P['heavy']=([reward('蓄力普通重击削韧系数 +10%','Charged regular heavy attack stance damage +10%',{'magicSubCategoryChange1':100,'saAttackPowerRate':1.10})],[damage('蓄力普通重击伤害 +10%','Charged regular heavy attack damage +10%',1.10,(100,))])
P['crit']=([crit(1.10)],[crit(1.20)])
P['sorcery']=(P['sorcery'][0],[damage('魔法伤害 +10%','Sorcery damage +10%',1.10,template=330010)])
P['incant']=(P['incant'][0],[reward('祷告伤害 +10%','Incantation damage +10%',dict({k:1.10 for k in RATE_FIELDS},magParamChange=0,miracleParamChange=1),330010)])
P['magic_skill']=(P['magic_skill'][0],[reward('魔力属性战技伤害 +15%（魔法剑士对应的战技类别）','Magic skill damage +15% (Spellblade-supported skill categories)',{'magicAttackRate':1.15},6013000)])
for code,field,resist,title in [('fire','fireAttackRate','fireDamageCutRate','火焰'),('holy','darkAttackRate','darkDamageCutRate','圣'),('lightning','thunderAttackRate','thunderDamageCutRate','雷电')]:
    P[code]=([reward(f'{title}属性伤害 +10%',f'{code.title()} damage +10%',{field:1.10})],[reward(f'受到的{title}属性伤害 -20%',f'{code.title()} damage received -20%',{resist:.80})])
P['blackflame']=([damage('神皮／黑焰类直接攻击祷告伤害 +10%（不放大持续百分比灼烧）','Godskin/blackflame direct incantation damage +10% (not percentage HP burn)',1.10,template=1922)],P['blackflame'][1])
P['frost']=([reward('冻伤抗性 +200 点','Frost resistance +200 points',{'changeFreezeResistPoint':200})],[damage('寒冰魔法伤害 +15%','Cold sorcery damage +15%',1.15,template=6101000)])
P['bleed']=([reward('感应 +20','Arcane +20',{'addLuckStatus':20})],[trigger(379,1.10,600)])
P['poison']=([reward('中毒与腐败抗性各 +100 点','Poison and rot resistance +100 points each',{'changePoisonResistPoint':100,'changeDiseaseResistPoint':100})],[trigger(380,1.10,600)])
P['rot']=([reward('腐败抗性 +200 点','Rot resistance +200 points',{'changeDiseaseResistPoint':200})],[trigger(380,1.08,600)])
P['dragon']=([damage('龙飨祷告直接伤害 +10%','Dragon Communion direct incantation damage +10%',1.10,template=1927)],[reward('对参数标记为龙类（D）的敌人伤害 +20%','Damage to enemies flagged dragon type D +20%',{'weakDmgRateD':1.20})])
P['crucible']=([damage('熔炉百相祷告伤害 +10%','Aspects of the Crucible incantation damage +10%',1.10,template=6057000)],[damage('熔炉百相祷告伤害 +15%','Aspects of the Crucible incantation damage +15%',1.15,template=6057000)])
P['bow']=([damage('箭矢与弩箭伤害 +10%','Arrow and bolt damage +10%',1.10,template=321500)],[reward('弓箭飞行距离修正 +30 个百分点','Bow flight-distance correction +30 percentage points',{'bowDistRate':30},321000)])
P['jump']=([reward('跳跃攻击削韧系数 +10%','Jump attack stance damage +10%',{'magicSubCategoryChange1':102,'saAttackPowerRate':1.10})],[damage('跳跃攻击伤害 +10%','Jump attack damage +10%',1.10,(102,))])
P['counter']=([reward('防御反击削韧系数 +15%','Guard counter stance damage +15%',{'magicSubCategoryChange1':103,'saAttackPowerRate':1.15})],[damage('防御反击伤害 +12%','Guard counter damage +12%',1.12,(103,))])
P['craft']=([pots(10)],[pots(20)])
P['martial']=([reward('所有行动的精力消耗 -10%（含格斗武器）','All action stamina cost -10% (including martial arts)',{'consumeStaminaRate':.90})],P['heavy'][1])
P['frenzy']=([damage('癫火祷告直接伤害 +10%','Frenzied Flame direct incantation damage +10%',1.10,template=1928)],[reward('发狂抗性 +100 点','Madness resistance +100 points',{'changeMadnessResistPoint':100})])
for code,template,zh,en in [('dance',6508000,'舞蹈战技','Dancing skill'),('bloodmagic',6012000,'荆棘魔法','Thorn sorcery'),('gravity',1920,'重力魔法','Gravity sorcery'),('bloodskill',6511010,'鲜血系战技','Blood skill')]:
    P[code]=([damage(zh+'伤害 +8%',en+' damage +8%',1.08,template=template)],[damage(zh+'伤害 +15%',en+' damage +15%',1.15,template=template)])
P['sleep']=([reward('睡眠抗性 +100 点','Sleep resistance +100 points',{'changeSleepResistPoint':100})],[reward('最大生命值 +10%','Maximum HP +10%',{'maxHpRate':1.10})])
REPLACE.update({'magic_skill','crucible','dance','bloodmagic','gravity','bloodskill'})
