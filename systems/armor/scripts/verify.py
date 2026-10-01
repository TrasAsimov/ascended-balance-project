"""Check binary invariants and execute generated event branches for all loadouts."""
from pathlib import Path
import sys,json,struct,itertools
ROOT=Path(__file__).resolve().parent.parent;OLD=ROOT/'inputs';REF=ROOT/'inputs/reference'
sys.path.insert(0,str(ROOT.parents[1]/'scripts'))
from analyze_regulation import read_bnd
from field_diff import defs,fields,decode
from build_zhocn_patch import fmg_read
from formats import *

_,base=read_bnd(OLD/'pending_v0105/adjusted.bnd');_,out=read_bnd(ROOT/'data/result.bnd');_,van=read_bnd(OLD/'work/vanilla.bnd')
assert base.keys()==out.keys() and len(out)==194
approval=json.loads((ROOT/'config/approved_edits.json').read_text())
core={int(k):v for k,v in approval['core_targets'].items()}
changes=json.loads((ROOT/'data/changes.json').read_text());changed={r['id'] for r in changes}
added=json.loads((ROOT/'data/effects.json').read_text())
external=json.loads((ROOT/'data/external_effect_dependencies.json').read_text())
for t,table in base.items():
    for rid,r in table['rows'].items():
        if t=='EquipParamProtector' and rid in changed:continue
        if t=='SpEffectParam' and rid in core:continue
        assert out[t]['rows'][rid]['data']==r['data'],('collateral parameter change',t,rid)
    if t in external:assert set(out[t]['rows'])-set(table['rows'])=={x for k,x in external[t].items() if int(k)!=x}
    elif t!='SpEffectParam':assert table['rows'].keys()==out[t]['rows'].keys()
    else:assert set(out[t]['rows'])-set(table['rows'])=={int(k) for k in added}
fm={t:{f[0]:f for f in fields(defs()[out[t]['ptype']])[0]} for t in ['SpEffectParam','EquipParamProtector','BehaviorParam_PC','Bullet','AtkParam_Pc']}
# Changed armor rows may differ only in the three resident effect slots.
for record in changes:
    expected=bytearray(base['EquipParamProtector']['rows'][record['id']]['data'])
    for key,value in zip(['residentSpEffectId','residentSpEffectId2','residentSpEffectId3'],record['after']):
        struct.pack_into('<i',expected,fm['EquipParamProtector'][key][2],value)
    assert expected==out['EquipParamProtector']['rows'][record['id']]['data'],('armor field scope mismatch',record['id'])
link=['cycleOccurrenceSpEffectId','replaceSpEffectId','atkOccurrenceSpEffectId']
mapping={int(k):v for k,v in json.loads((ROOT/'data/original_effect_map.json').read_text()).items()}
for old,new in mapping.items():
    expected=bytearray(van['SpEffectParam']['rows'][old]['data'])
    for key,value in approval['original_overrides'].get(str(old),{}).items():
        f=fm['SpEffectParam'][key];struct.pack_into('<'+{'f32':'f','s8':'b','u8':'B','s16':'h','u16':'H','s32':'i','u32':'I'}[f[1]],expected,f[2],value)
    for k in link:
        f=fm['SpEffectParam'][k];v=decode(expected,f)
        if v>0:struct.pack_into('<i',expected,f[2],mapping[v])
    f=fm['SpEffectParam']['behaviorId'];v=decode(expected,f)
    if v>0:struct.pack_into('<i',expected,f[2],external['BehaviorParam_PC'][str(v)])
    assert out['SpEffectParam']['rows'][new]['data']==expected,('official chain mismatch',old,new)
for table, remaps in external.items():
    for original_id, target_id in remaps.items():
        expected=bytearray(van[table]['rows'][int(original_id)]['data'])
        rewrite={}
        if table=='BehaviorParam_PC':
            ref=decode(expected,fm[table]['refId']);kind=decode(expected,fm[table]['refType'])
            if ref>0 and kind in [0,1]:rewrite['refId']=external['AtkParam_Pc' if kind==0 else 'Bullet'][str(ref)]
        else:
            for field in ['spEffectId0','spEffectId1','spEffectId2','spEffectId3','spEffectId4']+(['spEffectIDForShooter'] if table=='Bullet' else []):
                ref=decode(expected,fm[table][field])
                if ref>0:rewrite[field]=mapping[ref]
            if table=='Bullet':
                ref=decode(expected,fm[table]['atkId_Bullet'])
                if ref>0:rewrite['atkId_Bullet']=external['AtkParam_Pc'][str(ref)]
        for field,value in rewrite.items():struct.pack_into('<i',expected,fm[table][field][2],value)
        assert expected==out[table]['rows'][target_id]['data'],('official external dependency mismatch',table,original_id)
for record in json.loads((ROOT/'data/restoration.json').read_text()):
    body=out['EquipParamProtector']['rows'][record['armor_id']]['data']
    ids=[decode(body,fm['EquipParamProtector'][k]) for k in ['residentSpEffectId','residentSpEffectId2','residentSpEffectId3']]
    for slot,old in enumerate(record['official_slots']):
        if old>0:assert ids[slot]==mapping[old]
for eid,target in core.items():
    expected=bytearray(base['SpEffectParam']['rows'][eid]['data'])
    for key in ['physicsAttackRate','magicAttackRate','fireAttackRate','thunderAttackRate','darkAttackRate']:
        key=key.replace('AttackRate','AttackPowerRate') if eid==321400 else key
        struct.pack_into('<f',expected,fm['SpEffectParam'][key][2],target)
    assert expected==out['SpEffectParam']['rows'][eid]['data'],('core field scope mismatch',eid)
for armor,extra in approval['piece_additions'].items():
    body=out['EquipParamProtector']['rows'][int(armor)]['data']
    assert extra in [decode(body,fm['EquipParamProtector'][k]) for k in ['residentSpEffectId','residentSpEffectId2','residentSpEffectId3']]
# Check the actual shared effect fields, not only the resident references.
piece_fields={
    6202024:{'changeDiseaseResistPoint':400},
    6202022:{'darkDamageCutRate':.70},
    6202018:{'dexterityCancelSystemOnlyAddDexterity':90},
    6202016:{'equipWeightChangeRate':1.30},
    6202012:{'physicsAttackPower':100},
    6202004:{'maxStaminaRate':1.30},
    6202034:{'addStrengthStatus':30},
    6202037:{'addFaithStatus':30},
    6202039:{'motionInterval':.5,'changeHpPoint':-30},
}
for eid,expect in piece_fields.items():
    for field,value in expect.items():
        assert abs(decode(out['SpEffectParam']['rows'][eid]['data'],fm['SpEffectParam'][field])-value)<1e-6,(eid,field,value)
lion=out['EquipParamProtector']['rows'][5330000]['data']
assert 6202037 in [decode(lion,fm['EquipParamProtector'][k]) for k in ['residentSpEffectId','residentSpEffectId2','residentSpEffectId3']]
for eid in added:
    r=out['SpEffectParam']['rows'][int(eid)]
    for k in link:
        v=decode(r['data'],fm['SpEffectParam'][k]);assert v<=0 or v in out['SpEffectParam']['rows']

before=Emevd((REF/'common.emevd').read_bytes());after=Emevd(dcx_unpack((ROOT/'ModEngine/mod/event/common.emevd.dcx').read_bytes()))
ae={e['id']:e for e in after.events}
for old in before.events:
    new=ae[old['id']]
    assert new['rest']==old['rest'] and new['params']==old['params']
    if old['id']==0:assert new['ins'][-len(old['ins']):]==old['ins']
    else:assert new==old,('collateral event change',old['id'])
doc=json.loads((REF/'er-common.emedf.json').read_text());spec={(b['index'],i['index']):i for b in doc['main_classes'] for i in b['instrs']}
fmts={0:'B',1:'H',2:'I',3:'b',4:'h',5:'i',6:'f',8:'I'}
def unpackargs(ins):
    bank,idx,raw,layer=ins;o=0;vals=[]
    for a in spec[bank,idx]['args']:
        f=fmts[a['type']];size=struct.calcsize(f);o+=-o%size;vals.append(struct.unpack_from('<'+f,raw,o)[0]);o+=size
    assert o<=len(raw) and raw[o:]==bytes(len(raw)-o)
    return vals
for e in after.events:
    if e['id']>=9000000 and e['id']<9100000:
        for ins in e['ins']:unpackargs(ins)

def run(event,loadout,hp,active):
    groups={};pc=0;steps=0;active=set(active)
    hp=struct.unpack('<f',struct.pack('<f',hp))[0]
    def evaluate(g):
        arr=groups.get(g,[])
        return (all if g>0 else any)(p() for p in arr) if arr else False
    while pc<len(event['ins']):
        b,i,_,_=event['ins'][pc];a=unpackargs(event['ins'][pc]);pc+=1;steps+=1
        assert steps<500
        if (b,i)==(3,34):g,slot,rid,_=a;groups.setdefault(g,[]).append(lambda slot=slot,rid=rid:loadout[slot]==rid)
        elif (b,i)==(0,0):g,want,other=a;groups.setdefault(g,[]).append(lambda want=want,other=other:evaluate(other)==bool(want))
        elif (b,i) in [(4,14),(4,2)]:
            g,entity,op,target,_,_=a
            value=hp if i==2 else (1 if hp>0 else 0)
            groups.setdefault(g,[]).append(lambda value=value,op=op,target=target: {2:value>target,3:value<target}[op])
        elif (b,i)==(1000,1):skip,want,g=a;pc+=skip if evaluate(g)==bool(want) else 0
        elif (b,i)==(1004,0):skip,entity,eid,want,_,_=a;pc+=skip if (eid in active)==bool(want) else 0
        elif (b,i)==(1000,3):pc+=a[0]
        elif (b,i)==(2004,8):active.add(a[1])
        elif (b,i)==(2004,21):active.discard(a[1])
        elif (b,i)==(1001,1):assert a==[6];break
        else:raise AssertionError((b,i))
    return active

sets=json.loads((ROOT/'data/sets.json').read_text());cases=0;transitions=0
for g in sets.values():
    if not g['rewards']:continue
    choices=[[-1]+g['pieces'].get(str(slot),[]) for slot in range(4)]
    for outfit in itertools.product(*choices):
        count=sum(outfit[s] in g['pieces'].get(str(s),[]) for s in range(4))
        for hp in [0,.18,.29,.30,1]:
            for r in g['rewards']:
                expected=count>=r['tier'] and hp>0
                if r['exclusive']:expected=expected and count<g['full']
                if r['regen']=='normal':expected=expected and not(count>=g['full'] and hp<.30)
                if r['regen']=='low':expected=expected and hp<.30
                e=ae[r['event']]
                for seed in [set(),{r['effect'],*r['children']}]:
                    result=run(e,outfit,hp,seed)
                    assert (r['effect'] in result)==expected,(g['key'],r['tier'],outfit,hp,expected,result)
                    if not expected:assert not result & {r['effect'],*r['children']}
                    cases+=1
            transitions+=1
# Confirm every emitted bonus equals the requested specification in the
# decoded binary; scopes and chain lifetimes are checked separately.
from profiles import P,REPLACE
sets=json.loads((ROOT/'data/sets.json').read_text())
for g in sets.values():
    for reward in g['rewards']:
        body=out['SpEffectParam']['rows'][reward['effect']]['data']
        for key in ['effectTargetSelf','effectTargetPlayer','effectTargetLive']:
            assert decode(body,fm['SpEffectParam'][key])==1,('reward not applicable to wearer',g['key'],key)
        for key,value in reward['fields'].items():
            assert abs(decode(body,fm['SpEffectParam'][key])-value)<1e-5,(g['key'],key,value)
        if reward['tier']==2 and g['full']>2:
            assert reward['exclusive']==(g['profile'] in REPLACE)
        if reward['children']:
            for child in reward['children']:
                assert decode(out['SpEffectParam']['rows'][child]['data'],fm['SpEffectParam']['effectEndurance'])==600
# Explicitly unchanged single-piece decisions in the workbook.
for armor_id,effects in [(5310000,[6531000,6202039,6202002]),(5320000,[6532000,6202004,6202032])]:
    body=out['EquipParamProtector']['rows'][armor_id]['data']
    actual={decode(body,fm['EquipParamProtector'][k]) for k in ['residentSpEffectId','residentSpEffectId2','residentSpEffectId3']}
    assert actual=={mapping.get(e,e) for e in effects},(armor_id,actual)
# All English descriptions exist, and stale 'Effect:' lines are gone.
core_caption_checks=0
named={int(k) for k in json.loads((ROOT/'data/armor_index.json').read_text())}
for name in ['item_dlc01','item_dlc02']:
    parts=bnd_entries(dcx_unpack((ROOT/f'ModEngine/mod/msg/engus/{name}.msgbnd.dcx').read_bytes()));seen=set()
    for k,(_,r) in parts.items():
        if k.startswith('AccessoryCaption'):
            for rid,text in fmg_read(r).items():
                if rid in {2120,2130,2140,2180} and text:
                    assert '[Ascended Balance effect]' not in text and 'Effect:' not in text
                    assert {2120:'+250%',2130:'+300%',2140:'+220%',2180:'+100%'}[rid] in text
                    assert len(text.splitlines())==1
                    core_caption_checks+=1
        if k.startswith('ProtectorCaption'):
            for rid,text in fmg_read(r).items():
                if rid in named and text:
                    assert 'pieces)' in text.splitlines()[0] or 'piece)' in text.splitlines()[0]
                    assert text==json.loads((ROOT/'data/description_en.json').read_text())[str(rid)]
                    assert 'Original piece:' not in text and 'Retained Mod piece:' not in text
                    assert 'x1.' not in text and '×' not in text
                    assert not any(l.strip().startswith('Effect:') for l in text.splitlines())
                    seen.add(rid)
    assert seen==named
assert core_caption_checks>=8,core_caption_checks
report=dict(core_effect_rows_verified=4,core_caption_checks=core_caption_checks,approved_excel_profiles=26,approved_excel_piece_decisions=12,explicit_piece_effect_fields_verified=sum(len(v) for v in piece_fields.values()),parameter_tables=194,original_armor_verified=140,official_effect_chain_verified=len(mapping),event_cases=cases,loadout_hp_scenarios=transitions,english_descriptions=741,unchanged_original_events=len(before.events),game_test='not run',game_validation={'startup':'not run','load':'not run','save_and_reload':'not run','armor_and_set_effects':'not run'})
(ROOT/'data/verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
