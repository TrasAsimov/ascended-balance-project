"""Patch only Leontiel's two reward rows, exclusive threshold, and captions.

Use the latest integrated regulation, event and text inputs. The skill selector
comes from official Shard of Alexander 312310, not its modified Ascended row.
No packages or releases are produced. Runtime damage still requires game QA.
"""
import argparse, copy, itertools, json, os, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from disable_player_debuffs import unpack,sha
from build_minor_boss_heart import pack_regulation
from analyze_regulation import read_param
from field_diff import fields,decode,TYPES
from formats import bnd_entries,bnd_repack,bnd_patch,param_patch,Emevd,dcx_pack,dcx_unpack,instruction_builder
from fmg import fmg_read,fmg_write
from profiles import P

GROUP=json.loads((ROOT/'systems/armor/config/families.json').read_text())['groups']['536']
IDS={rid for members in GROUP['pieces'].values() for rid in members}
EVENTS={2:9000298,4:9000299}
EFFECTS={2:7200304,4:7200305}

def write_field(body,field,value):
    _,typ,pos,size,bits,shift,_=field
    if bits is None:struct.pack_into('<'+TYPES[typ][0],body,pos,value)
    else:
        mask=((1<<bits)-1)<<shift
        n=(int.from_bytes(body[pos:pos+size],'little')&~mask)|(int(value)<<shift)
        body[pos:pos+size]=n.to_bytes(size,'little')

def patch_params(raw,native,effect_def):
    parts=bnd_entries(raw);nparts=bnd_entries(native)
    table=read_param(parts['SpEffectParam.param'][1],'SpEffectParam')
    official=read_param(nparts['SpEffectParam.param'][1],'SpEffectParam')
    fs,size=fields(effect_def);lm={f[0]:f for f in fs}
    assert size==table['row_size']==official['row_size']==912
    template=official['rows'][312310]['data']
    assert [decode(template,lm['magicSubCategoryChange'+str(i)]) for i in (1,2,3)]==[112,111,0]
    changes={}
    for tier,spec in zip((2,4),(P['skill'][0][0],P['skill'][1][0])):
        body=bytearray(template)
        clean=dict(iconId=-1,vfxId=-1,effectEndurance=-1,motionInterval=0,
                   spCategory=0,categoryPriority=0,saveCategory=-1,dontDeleteOnDead=0)
        clean.update({k:-1 for k in ['replaceSpEffectId','cycleOccurrenceSpEffectId','atkOccurrenceSpEffectId']})
        clean.update({k:1 for k in ['effectTargetSelf','effectTargetFriend','effectTargetPlayer','effectTargetAI','effectTargetLive','effectTargetGhost']})
        for k,v in dict(clean,**spec['fields']).items():write_field(body,lm[k],v)
        assert decode(body,lm['magicConsumptionRate'])==1
        assert decode(body,lm['stateInfo'])==decode(template,lm['stateInfo'])
        changes[EFFECTS[tier]]=bytes(body)
    out=bnd_repack(raw,{'SpEffectParam.param':param_patch(parts['SpEffectParam.param'][1],changes,{},size)})
    checked=bnd_entries(out)
    assert all(checked[k][1]==v[1] for k,v in parts.items() if k!='SpEffectParam.param')
    rows=read_param(checked['SpEffectParam.param'][1],'SpEffectParam')['rows']
    assert rows.keys()==table['rows'].keys()
    for rid,r in table['rows'].items():assert rows[rid]['data']==changes.get(rid,r['data'])
    return out,{'target_effects':EFFECTS,'official_skill_template':312310,
                'skill_selectors':[112,111],'other_tables_byte_identical':len(parts)-1,
                'all_other_effect_rows_byte_identical':True}

def conditions(I,threshold,org,first):
    ins=[]
    for n,(slot,members) in enumerate(sorted(GROUP['pieces'].items())):
        for rid in members:ins.append(I(3,34,-(n+1),int(slot),rid,-1))
    for n,combo in enumerate(itertools.combinations(range(1,5),threshold)):
        for slot in combo:ins.append(I(0,0,first+n,1,-slot))
        ins.append(I(0,0,org,1,first+n))
    return ins

def active(event,equipment):
    state={}
    def add(group,value):
        state[group]=(state.get(group,False) or value if group<0 else state.get(group,True) and value)
    for bank,index,args,_ in event['ins']:
        if (bank,index)==(3,34):
            group,slot,rid,comp=struct.unpack('<bb2xii',args);assert comp==-1
            add(group,equipment[slot]==rid)
        elif (bank,index)==(0,0):
            group,expected,source,pad=struct.unpack('<bBbB',args);assert pad==0
            add(group,state[source]==bool(expected))
        elif (bank,index)==(4,14):return state[15]
        else:raise AssertionError((bank,index))
    raise AssertionError('missing combat gate')

def patch_events(blob,emedf):
    original=Emevd(dcx_unpack(blob));ev=copy.deepcopy(original)
    byid={e['id']:e for e in ev.events};two=byid[EVENTS[2]];full=byid[EVENTS[4]]
    for tier,event in [(2,two),(4,full)]:
        assert not event['params']
        assert any((b,i)==(2004,8) and struct.unpack('<ii',a)==(10000,EFFECTS[tier]) for b,i,a,_ in event['ins'])
        assert {struct.unpack_from('<i',a,4)[0] for b,i,a,_ in event['ins'] if (b,i)==(3,34)}==IDS
    tail=next(n for n,(b,i,_,_) in enumerate(two['ins']) if (b,i)==(4,14))
    I=instruction_builder(emedf)
    two['ins']=conditions(I,2,-5,1)+[I(0,0,15,1,-5)]+conditions(I,4,-6,9)+[I(0,0,15,0,-6)]+two['ins'][tail:]
    assert all(a==b for a,b in zip(original.events,ev.events) if a['id']!=EVENTS[2])
    tested=0
    options=[[None,9999999]+members for members in GROUP['pieces'].values()]
    for gear in itertools.product(*options):
        count=sum(gear[int(slot)] in members for slot,members in GROUP['pieces'].items())
        assert active(two,gear)==(2<=count<4),(gear,count)
        assert active(full,gear)==(count==4),(gear,count)
        tested+=1
    result=dcx_pack(ev.write());assert Emevd(dcx_unpack(result)).events==ev.events
    return result,{'changed_event':EVENTS[2],'all_other_events_unchanged':True,
                   'equipment_combinations_checked':tested,'four_piece_total':'+20%, replaces +10%'}

def caption(rid,text,language):
    if not str(rid).isdigit() or int(rid) not in IDS or not text:return text
    labels=('2件效果: ','4件效果: ') if language=='zh' else ('2-Piece Effect: ','4-Piece Effect: ')
    specs=(P['skill'][0][0],P['skill'][1][0]);key=language
    blocks=text.split('\n\n')
    for n,label in enumerate(labels):
        positions=[i for i,b in enumerate(blocks) if b.startswith(label)]
        assert len(positions)==1,(rid,label)
        suffix=('（替换2件）' if language=='zh' else ' (replaces 2 pcs)') if n==1 else ''
        blocks[positions[0]]=label+specs[n][key]+suffix
    return '\n\n'.join(blocks)

def patch_text(blob):
    parts=bnd_entries(dcx_unpack(blob));changes={};ids=[]
    for name,(_,body) in parts.items():
        if not name.startswith('ProtectorCaption'):continue
        entries=fmg_read(body);after={rid:caption(rid,text,'en') for rid,text in entries.items()}
        changed=[rid for rid in entries if entries[rid]!=after[rid]]
        if changed:changes[name]=fmg_write(after);ids+=changed
    if not changes:return blob,ids
    out=dcx_pack(bnd_patch(dcx_unpack(blob),changes));checked=bnd_entries(dcx_unpack(out))
    for name,(_,body) in parts.items():
        if name not in changes:assert checked[name][1]==body
        else:assert fmg_read(checked[name][1])=={rid:caption(rid,text,'en') for rid,text in fmg_read(body).items()}
    return out,ids

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ('regulation','native-bnd','effect-def','common','emedf','texts','output'):
        p.add_argument('--'+flag,type=Path,required=True)
    a=p.parse_args();key=bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    src=a.regulation.read_bytes();header,raw=unpack(src,key)
    out,report=patch_params(raw,a.native_bnd.read_bytes(),a.effect_def)
    assert patch_params(out,a.native_bnd.read_bytes(),a.effect_def)[0]==out
    blob=pack_regulation(header,out,key);assert unpack(blob,key)[1]==out
    a.output.mkdir(parents=True,exist_ok=True);prefix='02_Leontiel_Skill_20261002_'
    (a.output/(prefix+'regulation.bin')).write_bytes(blob)
    common,eventreport=patch_events(a.common.read_bytes(),a.emedf)
    assert patch_events(common,a.emedf)[0]==common
    (a.output/(prefix+'common.emevd.dcx')).write_bytes(common)
    textreport={}
    for name in ('item_dlc01','item_dlc02'):
        source=a.texts/('02_Tarnished_Armor_20261002_engus_'+name+'.msgbnd.dcx')
        result,changed=patch_text(source.read_bytes());assert patch_text(result)==(result,[])
        (a.output/(prefix+'engus_'+name+'.msgbnd.dcx')).write_bytes(result);textreport[name]=changed
    for language in ('en','zh'):
        source=a.texts/('02_Tarnished_Armor_20261002_armor_description_'+language+'.json')
        before=json.loads(source.read_text());after={rid:caption(rid,text,language) for rid,text in before.items()}
        assert {int(rid) for rid in before if before[rid]!=after[rid]}==IDS
        (a.output/(prefix+'armor_description_'+language+'.json')).write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
    report.update(events=eventreport,texts=textreport,input_sha256=sha(src),output_sha256=sha(blob),
                  idempotent=True,encrypted_roundtrip=True,game_validation='not run')
    report['files']={f.name:sha(f.read_bytes()) for f in a.output.iterdir() if f.is_file() and f.name!=prefix+'audit.json'}
    (a.output/(prefix+'audit.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
