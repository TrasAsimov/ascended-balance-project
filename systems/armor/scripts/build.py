from pathlib import Path
import sys, struct, json, hashlib, re, itertools, csv, copy
ROOT=Path(__file__).resolve().parent.parent
REF=ROOT/'inputs/reference'
OLD=ROOT/'inputs'
sys.path.insert(0,str(ROOT.parents[1]/'scripts'))
from analyze_regulation import read_bnd,read_param
from field_diff import defs,fields,decode,TYPES,names
from build_zhocn_patch import fmg_read,fmg_write,unpack
from formats import *
from profiles import *
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
import zstandard as zstd

BASE=OLD/'pending_v0105/adjusted.bnd'
KEY=bytes.fromhex(__import__('os').environ['ARMOR_REGULATION_KEY_HEX'])
for directory in ['data','docs','ModEngine/mod/msg/engus']:(ROOT/directory).mkdir(parents=True,exist_ok=True)
expected=json.loads((ROOT/'config/input_hashes.json').read_text())
for relative,digest in expected.items():
    source=OLD/relative
    assert source.exists(),f'Missing owned input: {source}'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,f'Input version mismatch: {source}'
VERSION,tables=read_bnd(BASE)
_,van=read_bnd(OLD/'work/vanilla.bnd')
assert VERSION=='11711000'
layout={t:{f[0]:f for f in fields(defs()[tables[t]['ptype']])[0]} for t in ['EquipParamProtector','SpEffectParam','BehaviorParam_PC','Bullet','AtkParam_Pc']}
for t,l in layout.items():assert max(f[2]+f[3] for f in l.values())==tables[t]['row_size']
def get(t,body,key):return decode(body,layout[t][key])
def put(t,body,key,val):
    f=layout[t][key];typ,pos,size,bits,shift,n=f[1:]
    if bits:
        raw=int.from_bytes(body[pos:pos+size],'little');mask=((1<<bits)-1)<<shift
        body[pos:pos+size]=((raw&~mask)|((val<<shift)&mask)).to_bytes(size,'little')
    else:struct.pack_into('<'+TYPES[typ][0],body,pos,val)

def parse_sets():
    config=json.loads((ROOT/'config/families.json').read_text())
    groups,armor=config['groups'],{int(k):v for k,v in config['armors'].items()}
    for g in groups.values():g['pieces']={int(k):v for k,v in g['pieces'].items()}
    assert len(groups)==187 and len(armor)==741
    return groups,armor

approval=json.loads((ROOT/'config/approved_edits.json').read_text())
groups,armors=parse_sets()
slots=['residentSpEffectId','residentSpEffectId2','residentSpEffectId3']
efields=layout['SpEffectParam']
sp=van['SpEffectParam']['rows'];cur=tables['SpEffectParam']['rows']
added={};changes={};armchanges={};chainmap={};audit=[];restored=[];rewards=[]
reserved=set(cur)
next_restore=7100000;next_reward=7200000
external_added={t:{} for t in ['BehaviorParam_PC','Bullet','AtkParam_Pc']}
external_map={t:{} for t in external_added}
def reserve(kind):
    global next_restore,next_reward
    val=next_restore if kind=='restore' else next_reward
    while val in reserved:val+=1
    reserved.add(val)
    if kind=='restore':next_restore=val+1
    else:next_reward=val+1
    return val
LINKS=['replaceSpEffectId','cycleOccurrenceSpEffectId','atkOccurrenceSpEffectId']
def external_original(t,rid):
    if rid in external_map[t]:return external_map[t][rid]
    assert rid in van[t]['rows'],(t,rid)
    body=bytearray(van[t]['rows'][rid]['data'])
    newid=7300000+len(external_map[t])
    while newid in tables[t]['rows']:newid+=1
    external_map[t][rid]=newid
    if t=='BehaviorParam_PC':
        ref=get(t,body,'refId');kind=get(t,body,'refType')
        if ref>0 and kind in [0,1]:put(t,body,'refId',external_original('AtkParam_Pc' if kind==0 else 'Bullet',ref))
    elif t=='Bullet':
        for k in ['spEffectId0','spEffectId1','spEffectId2','spEffectId3','spEffectId4','spEffectIDForShooter']:
            child=get(t,body,k)
            if child>0:put(t,body,k,original_effect(child))
        atk=get(t,body,'atkId_Bullet')
        if atk>0:put(t,body,'atkId_Bullet',external_original('AtkParam_Pc',atk))
    elif t=='AtkParam_Pc':
        for k in ['spEffectId0','spEffectId1','spEffectId2','spEffectId3','spEffectId4']:
            child=get(t,body,k)
            if child>0:put(t,body,k,original_effect(child))
    if tables[t]['rows'].get(rid,{}).get('data')==bytes(body):external_map[t][rid]=rid
    else:external_added[t][newid]=bytes(body)
    return external_map[t][rid]

def original_effect(eid):
    if eid in chainmap:return chainmap[eid]
    assert eid in sp,('missing official effect',eid)
    body=bytearray(sp[eid]['data'])
    for key,value in approval['original_overrides'].get(str(eid),{}).items():put('SpEffectParam',body,key,value)
    # Cycle-safe: reserve before recursion; use original ID when the entire
    # chain is already official, otherwise use an armor-local copy.
    clone=reserve('restore');chainmap[eid]=clone
    for k in LINKS:
        child=get('SpEffectParam',body,k)
        if child>0:put('SpEffectParam',body,k,original_effect(child))
    behavior=get('SpEffectParam',body,'behaviorId')
    if behavior>0:put('SpEffectParam',body,'behaviorId',external_original('BehaviorParam_PC',behavior))
    if eid in cur and cur[eid]['data']==bytes(body):chainmap[eid]=eid
    else:added[clone]=bytes(body)
    return chainmap[eid]

UTILITY={'iconId','conditionHp','conditionHpRate','effectEndurance','motionInterval','stateInfo','spCategory','categoryPriority','saveCategory','atkAttribute','spAttribute','vfxId','vfxId1','vfxId2','vfxId3','vfxId4','vfxId5','vfxId6','vfxId7','behaviorId','magicSubCategoryChange1','magicSubCategoryChange2','magicSubCategoryChange3'}|set(LINKS)
def active_fields(body):
    neutral=sp[1950]['data']
    return {k for k,f in efields.items() if k not in UTILITY and f[1]!='dummy8' and not f[4] and get('SpEffectParam',body,k)!=get('SpEffectParam',neutral,k)}

tarnished_bonuses=json.loads((ROOT/'config/tarnished_piece_bonuses.json').read_text())['armors']
for rid,rec in sorted(tables['EquipParamProtector']['rows'].items()):
    data=rec['data'];baseline=van['EquipParamProtector']['rows'][rid]['data']
    own=[get('EquipParamProtector',data,s) for s in slots]
    orig=[get('EquipParamProtector',baseline,s) for s in slots]
    official=[e for e in orig if e>0]
    new=[];removed=[]
    if official:
        official_fields=set().union(*(active_fields(sp[e]['data']) for e in official))
        official_cats={get('SpEffectParam',sp[e]['data'],'spCategory') for e in official}-{0,10,20}
        new=own.copy()
        for index,e in enumerate(orig):
            if e>0:
                if own[index]>0 and own[index]!=e:removed.append(own[index])
                new[index]=original_effect(e)
            elif own[index]>0:
                me=own[index]
                conflict=(me in official or active_fields(cur[me]['data'])&official_fields or get('SpEffectParam',cur[me]['data'],'spCategory') in official_cats)
                if conflict:removed.append(me);new[index]=-1
        restored.append({'armor_id':rid,'official_ids':official,'official_slots':orig,'applied_ids':[original_effect(e) for e in official],'before':own,'after':new,'removed_mod_effects':removed})
    else:new=[e for e in own if e>0]
    # These five legacy vitality bonuses have no corresponding ER attribute;
    # the prosthetic row was confirmed to reference the wrong trigger.
    bad={6202033}
    if rid==1970200:bad.add(6201000)
    removed += [e for e in new if e in bad]
    new=[-1 if e in bad else e for e in new]
    padded=[(-1 if e in bad else e) for e in new] if official else [(-1 if e in bad else e) for e in own]
    if official and len(padded)<3:padded+= [-1]*(3-len(padded))
    extra=approval['piece_additions'].get(str(rid))
    if extra and extra not in padded:
        assert -1 in padded,('no free resident slot',rid)
        padded[padded.index(-1)]=extra
    for eid in tarnished_bonuses.get(str(rid),{}).get('add_effect_ids',[]):
        if eid not in padded:
            free=next((i for i,v in enumerate(padded) if v<=0),None)
            assert free is not None,('no free Tarnished resident slot',rid,padded)
            padded[free]=eid
    if official:restored[-1]['after']=padded
    if own!=padded:
        body=bytearray(data)
        for k,e in zip(slots,padded):put('EquipParamProtector',body,k,e)
        armchanges[rid]=bytes(body)
        audit.append({'table':'EquipParamProtector','id':rid,'before':own,'after':padded,'removed':removed})

# Core damage targets only alter the existing damage multipliers. Attack
# selectors, categories, lifetimes and boss growth effects stay byte-identical.
core_audit=[]
for row,target in approval['core_targets'].items():
    eid=int(row);body=bytearray(cur[eid]['data']);diff={}
    for field in ([k.replace('AttackRate','AttackPowerRate') for k in RATE_FIELDS] if eid==321400 else RATE_FIELDS):
        before=get('SpEffectParam',body,field)
        assert abs(before-({321400:3.8,321300:4.2,321800:2.5,321200:2.5}[eid]))<1e-6,(eid,field,before)
        put('SpEffectParam',body,field,target)
        diff[field]={'before':before,'after':get('SpEffectParam',body,field)}
    changes[eid]=bytes(body);core_audit.append({'id':eid,'fields':diff})
(ROOT/'data/core_changes.json').write_text(json.dumps(core_audit,indent=2))

def make_reward(spec):
    eid=reserve('reward')
    template=spec['template'] or 1950
    body=bytearray(sp[template]['data'])
    # Strip original lifetime, icon, cycle/VFX and overwriting category. Keep
    # the official attack selectors and conditional state implementation.
    clean={'iconId':-1,'vfxId':-1,'effectEndurance':-1,'motionInterval':0,'spCategory':0,'categoryPriority':0,'saveCategory':-1,'dontDeleteOnDead':0}
    clean.update({k:-1 for k in LINKS})
    # 1950 is a crown visual effect with recipient masks disabled. Numeric
    # armor rewards must be applicable to the wearer like vanilla wearables.
    for key in ['effectTargetSelf','effectTargetFriend','effectTargetPlayer','effectTargetAI','effectTargetLive','effectTargetGhost']:
        clean[key]=1
    if template==1950:clean['stateInfo']=0
    if template==1950:
        # Native wearable attack modifiers use 0 (no weapon restriction),
        # not 3 (Self/body scope). Spell applicability is
        # controlled separately, then narrowed by the attack subcategory.
        clean.update({'magParamChange':1,'miracleParamChange':1,'wepParamChange':0})
    for k,v in clean.items():put('SpEffectParam',body,k,v)
    for k,v in spec['fields'].items():put('SpEffectParam',body,k,v)
    kids=[]
    for sub in spec['chains']:
        child,k=make_reward(sub);kids.extend([child]+k);put('SpEffectParam',body,'cycleOccurrenceSpEffectId',child)
    added[eid]=bytes(body)
    return eid,kids

for g in groups.values():
    g['rewards']=[]
    singles={
        '85':P['bow'][0],
        '92':P['light'][0],
        '130':[reward('魔力承伤 -8%','Magic damage received -8%',{'magicDamageCutRate':.92})],
    }
    if g['full']<2:
        if g['key'] not in singles:continue
        code=None;tiers=[(1,singles[g['key']])]
    else:
        if not g['profile']:continue
        code=g['profile'];two,full=P[code]
        tiers=[(2,two),(g['full'],full)] if g['full']>2 else [(2,two)]
    for tier,specs in tiers:
        for spec in specs:
            eid,kids=make_reward(spec)
            r=dict(key=g['key'],tier=tier,effect=eid,children=kids,zh=spec['zh'],en=spec['en'],fields=spec['fields'],template=spec['template'])
            r['exclusive']=tier==2 and g['full']>2 and code in REPLACE
            r['regen']=('low' if tier>2 else 'normal') if code=='regen' and g['full']>2 else None
            g['rewards'].append(r);rewards.append(r)

def count_conditions(I,g,threshold,orgrp,first):
    ins=[]
    for j,slot in enumerate(sorted(g['pieces'])):
        for rid in g['pieces'][slot]:ins.append(I(3,34,-(j+1),slot,rid,-1))
    for n,combo in enumerate(itertools.combinations(range(1,g['full']+1),threshold)):
        cond=first+n
        for slot in combo:ins.append(I(0,0,cond,1,-slot))
        ins.append(I(0,0,orgrp,1,cond))
    return ins

I=instruction_builder(REF/'er-common.emedf.json')
ev=Emevd((REF/'common.emevd').read_bytes());original_events=copy.deepcopy(ev.events)
constructor=next(e for e in ev.events if e['id']==0)
assert all(e['id']<9000000 or e['id']>=9100000 for e in ev.events)
initializers=[]
for n,r in enumerate(rewards):
    g=groups[r['key']];ins=count_conditions(I,g,r['tier'],-5,1)
    ins.append(I(0,0,15,1,-5))
    if r['exclusive'] or r['regen']=='normal':
        ins+=count_conditions(I,g,g['full'],-6,9)
        if r['regen']=='normal':
            ins.append(I(0,0,12,1,-6));ins.append(I(4,2,12,10000,3,.30,4,1.0))
            ins.append(I(0,0,15,0,12))
        else:ins.append(I(0,0,15,0,-6))
    if r['regen']=='low':ins.append(I(4,2,15,10000,3,.30,4,1.0))
    ins.append(I(4,14,15,10000,2,0,4,1.0))
    # Branches check current equipment each 6 frames, applying only if absent
    # so periodic healing and conditional buffs are not constantly reset.
    ins.append(I(1000,1,3,0,15))
    ins.append(I(1004,0,1,10000,r['effect'],1,4,1))
    ins.append(I(2004,8,10000,r['effect']))
    ins.append(I(1000,3,1+len(r['children'])))
    for eid in [r['effect']]+r['children']:ins.append(I(2004,21,10000,eid))
    ins.append(I(1001,1,6));ins.append(I(1000,4,1))
    eventid=9000000+n;r['event']=eventid
    ev.events.append(dict(id=eventid,rest=1,ins=ins,params=[]))
    initializers.append(I(2000,0,0,eventid,0))
# Local equipment checks must start before the constructor's host/world
# and 2052 early exits. Preserve every existing instruction and its order.
constructor['ins']=initializers+constructor['ins']
eventraw=ev.write()
out=ROOT/'ModEngine/mod'
(out/'event').mkdir(parents=True,exist_ok=True)
(out/'event/common.emevd.dcx').write_bytes(dcx_pack(eventraw))
assert Emevd(dcx_unpack((out/'event/common.emevd.dcx').read_bytes())).events==ev.events

parts=bnd_entries(BASE.read_bytes());updates={}
for t,changed,new in [('EquipParamProtector',armchanges,{}),('SpEffectParam',changes,added)]+[(t,{},a) for t,a in external_added.items() if a]:
    raw=param_patch(parts[t+'.param'][1],changed,new,tables[t]['row_size'])
    check=read_param(raw,t)
    assert len(check['rows'])==len(tables[t]['rows'])+len(new)
    for rid,rec in tables[t]['rows'].items():assert check['rows'][rid]['data']==changed.get(rid,rec['data']),(t,rid)
    for rid,body in new.items():assert check['rows'][rid]['data']==body
    updates[t+'.param']=raw
raw=bnd_repack(BASE.read_bytes(),updates)
(ROOT/'data/result.bnd').write_bytes(raw)
source=(OLD/'pending_v0105/ModEngine/mod/regulation.bin').read_bytes()
dec=Cipher(algorithms.AES(KEY),modes.CBC(source[:16])).decryptor();plain=dec.update(source[16:])+dec.finalize()
size,cs=struct.unpack_from('>II',plain,28)
assert zstd.ZstdDecompressor().decompress(plain[76:76+cs],max_output_size=size)==BASE.read_bytes()
packed=zstd.ZstdCompressor(compression_params=zstd.ZstdCompressionParameters.from_level(15,window_log=16,write_content_size=False)).compress(raw)
h=bytearray(plain[:76]);struct.pack_into('>II',h,28,len(raw),len(packed));p=bytes(h)+packed;p+=bytes(-len(p)%16)
iv=bytes(16);enc=Cipher(algorithms.AES(KEY),modes.CBC(iv)).encryptor();encrypted=iv+enc.update(p)+enc.finalize()
(out/'regulation.bin').write_bytes(encrypted)
dec=Cipher(algorithms.AES(KEY),modes.CBC(iv)).decryptor();p=dec.update(encrypted[16:])+dec.finalize();s,c=struct.unpack_from('>II',p,28)
assert zstd.ZstdDecompressor().decompress(p[76:76+c],max_output_size=s)==raw
data=ROOT/'data'
(data/'sets.json').write_text(json.dumps(groups,ensure_ascii=False,indent=2))
(data/'armor_index.json').write_text(json.dumps(armors,ensure_ascii=False,indent=2))
(data/'restoration.json').write_text(json.dumps(restored,ensure_ascii=False,indent=2))
(data/'effects.json').write_text(json.dumps({e:{f[0]:decode(b,f) for f in efields.values() if f[1]!='dummy8'} for e,b in added.items()},ensure_ascii=False,indent=2))
(data/'changes.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
(data/'original_effect_map.json').write_text(json.dumps(chainmap,indent=2))
(data/'external_effect_dependencies.json').write_text(json.dumps(external_map,indent=2))
(data/'official_effect_fields.json').write_text(json.dumps({e:{f[0]:decode(added.get(chainmap[e],cur[chainmap[e]]['data'] if chainmap[e] in cur else sp[e]['data']),f) for f in efields.values() if f[1]!='dummy8'} for e in chainmap},indent=2))
manifest=dict(base='v0.10.4 + pending_v0105',version=VERSION,sets=len(groups),reward_sets=sum(bool(g['rewards']) for g in groups.values()),named_armor=len(armors),restored_armor=len(restored),changed_armor=len(armchanges),new_effect_rows=len(added),reward_events=len(rewards),official_chain_rows=len(chainmap),status='02 armor activation and compact text follow-up; game effects require retest',param_writer='in-place edits plus conservative row-directory extension',binder_writer='original metadata; each live member packed once',uncompressed_binder_bytes=len(raw),game_validation={'startup':'not run','load':'not run','save_and_reload':'not run','armor_and_set_effects':'not run'},regulation_sha256=hashlib.sha256(encrypted).hexdigest(),common_sha256=hashlib.sha256((out/'event/common.emevd.dcx').read_bytes()).hexdigest())
(data/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(manifest,ensure_ascii=False,indent=2))
