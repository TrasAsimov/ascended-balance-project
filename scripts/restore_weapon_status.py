"""Restore official inherent weapon statuses and passive-effect labels.

Use after final integration. Enemy/consumable/spell shared effects are kept
intact; official weapon status chains use private copies. Reinforcement
effect offsets are preserved by a constant ID translation.
Requires ARMOR_REGULATION_KEY_HEX and matching ARMOR_PARAMDEFS.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import struct
import sys
import zstandard as zstd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from disable_player_debuffs import sha, unpack
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'systems/armor/scripts'))
from analyze_regulation import read_param
from field_diff import decode,defs,fields,TYPES
from formats import bnd_entries,bnd_repack,param_patch

PRIVATE_OFFSET=76000000
STATUS=['poizonAttackPower','diseaseAttackPower','bloodAttackPower','curseAttackPower',
        'freezeAttackPower','sleepAttackPower','madnessAttackPower']
CHAINS=['replaceSpEffectId','cycleOccurrenceSpEffectId','atkOccurrenceSpEffectId']
BEHAVIOR=['spEffectBehaviorId'+str(i) for i in range(3)]
MESSAGES=['spEffectMsgId'+str(i) for i in range(3)]
RESIDENT=['residentSpEffectId','residentSpEffectId1','residentSpEffectId2']
CORRECTION=['correctType_Poison','correctType_Blood','correctType_Sleep','correctType_Madness']


def patch(raw,official):
    parts,orig=bnd_entries(raw),bnd_entries(official)
    assert len(parts)==len(orig)==194
    names=['EquipParamWeapon','SpEffectParam','ReinforceParamWeapon']
    cur={t:read_param(parts[t+'.param'][1],t) for t in names}
    van={t:read_param(orig[t+'.param'][1],t) for t in names}
    layout={};sizes={};D=defs()
    for t in names:
        fs,size=fields(D[cur[t]['ptype']])
        assert size==cur[t]['row_size']==van[t]['row_size'],t
        layout[t]={f[0]:f for f in fs};sizes[t]=size
    def get(t,i,k,old=False):
        return decode((van if old else cur)[t]['rows'][i]['data'],layout[t][k])
    def put(body,t,k,value):
        f=layout[t][k];assert f[4] is None and f[6]==1
        struct.pack_into('<'+TYPES[f[1]][0],body,f[2],value)
    def closure(ids,old=False):
        rows=(van if old else cur)['SpEffectParam']['rows'];seen=set();pending=list(ids)
        while pending:
            i=pending.pop()
            if i in seen or i not in rows:continue
            seen.add(i);pending.extend(get('SpEffectParam',i,k,old) for k in CHAINS)
        return seen
    def has_status(ids,old=False):
        return any(any(get('SpEffectParam',i,k,old)>0 for k in STATUS) for i in closure(ids,old))
    base_ids={}
    for i in cur['EquipParamWeapon']['rows']:
        if i in van['EquipParamWeapon']['rows']:base_ids[i]=i
        else:
            base=get('EquipParamWeapon',i,'originEquipWep')
            assert base in van['EquipParamWeapon']['rows'],('No official source for custom weapon',i,base)
            base_ids[i]=base
    rein=cur['ReinforceParamWeapon']['rows']
    offset_values={}
    for i in cur['EquipParamWeapon']['rows']:
        kind=get('EquipParamWeapon',i,'reinforceTypeId')
        offset_values[i]={j:{get('ReinforceParamWeapon',r,'spEffectId'+str(j+1))
                              for r in rein if kind<=r<kind+26}
                          for j in range(3)}
    native_roots=set();selected_roots=set()
    for i,base in base_ids.items():
        for j,field in enumerate(BEHAVIOR):
            eid=get('EquipParamWeapon',base,field,True)
            if has_status([eid],True):
                selected_roots.add(eid)
                for offset in offset_values[i][j] or {0}:
                    assert eid+offset in van['SpEffectParam']['rows'],('Missing official upgraded effect',i,eid,offset)
                    native_roots.add(eid+offset)
    native=closure(native_roots,True)
    mapping={i:i+PRIVATE_OFFSET for i in native}
    assert all(i<2**31 for i in mapping.values())
    additions={}
    for i,j in mapping.items():
        body=bytearray(van['SpEffectParam']['rows'][i]['data'])
        for field in CHAINS:
            target=get('SpEffectParam',i,field,True)
            if target in mapping:put(body,'SpEffectParam',field,mapping[target])
        if j in cur['SpEffectParam']['rows']:
            assert cur['SpEffectParam']['rows'][j]['data']==body,('Private ID collision',j)
        else:additions[j]=bytes(body)
    weapon_changes={};records=[];removed=[]
    for i,base in base_ids.items():
        original=cur['EquipParamWeapon']['rows'][i]['data'];body=bytearray(original)
        for field in MESSAGES+CORRECTION:
            put(body,'EquipParamWeapon',field,get('EquipParamWeapon',base,field,True))
        for field in BEHAVIOR:
            eid=get('EquipParamWeapon',base,field,True)
            put(body,'EquipParamWeapon',field,mapping.get(eid,eid))
        for field in RESIDENT:
            eid=get('EquipParamWeapon',i,field)
            expected=get('EquipParamWeapon',base,field,True)
            # Remove weapon-equipped automatic poison/rot and other extra
            # buildup sources, while retaining unrelated resident bonuses.
            if has_status([eid]):
                if expected in van['SpEffectParam']['rows'] and has_status([expected],True):
                    assert expected in mapping,('Native resident status needs a private copy',expected)
                target=mapping.get(expected,expected)
                put(body,'EquipParamWeapon',field,target)
                if target!=eid:removed.append({'weapon_id':i,'slot':field,'before':eid,'after':target})
        if body!=original:
            weapon_changes[i]=bytes(body)
            records.append({'weapon_id':i,'official_source_id':base,
                            'fields':{k:{'before':decode(original,layout['EquipParamWeapon'][k]),
                                         'after':decode(body,layout['EquipParamWeapon'][k])}
                                      for k in layout['EquipParamWeapon']
                                      if decode(original,layout['EquipParamWeapon'][k])!=decode(body,layout['EquipParamWeapon'][k])}})
    updates={'EquipParamWeapon.param':param_patch(parts['EquipParamWeapon.param'][1],weapon_changes,{},sizes['EquipParamWeapon']),
             'SpEffectParam.param':param_patch(parts['SpEffectParam.param'][1],{},additions,sizes['SpEffectParam'])}
    output=bnd_repack(raw,updates);out=bnd_entries(output)
    assert all(out[k][1]==v[1] for k,v in parts.items() if k not in updates)
    after={t:read_param(out[t+'.param'][1],t) for t in names}
    allowed=set(BEHAVIOR+MESSAGES+RESIDENT+CORRECTION)
    for i,row in cur['EquipParamWeapon']['rows'].items():
        new=after['EquipParamWeapon']['rows'][i]['data'];base=base_ids[i]
        assert row['name']==after['EquipParamWeapon']['rows'][i]['name']
        for k,f in layout['EquipParamWeapon'].items():
            if k not in allowed:assert decode(new,f)==decode(row['data'],f),(i,k)
        for k in MESSAGES+CORRECTION:
            assert decode(new,layout['EquipParamWeapon'][k])==get('EquipParamWeapon',base,k,True)
        for j,k in enumerate(BEHAVIOR):
            eid=get('EquipParamWeapon',base,k,True)
            target=decode(new,layout['EquipParamWeapon'][k])
            assert target==mapping.get(eid,eid)
            if eid in mapping:
                for off in offset_values[i][j] or {0}:assert target+off==mapping[eid+off]
        for k in RESIDENT:
            target=decode(new,layout['EquipParamWeapon'][k])
            if has_status([get('EquipParamWeapon',i,k)]):
                expected=get('EquipParamWeapon',base,k,True)
                assert target==mapping.get(expected,expected)
    assert after['EquipParamWeapon']['rows'].keys()==cur['EquipParamWeapon']['rows'].keys()
    for i,row in cur['SpEffectParam']['rows'].items():
        assert after['SpEffectParam']['rows'][i]==row,('Existing shared effect changed',i)
    for i,j in mapping.items():
        data=after['SpEffectParam']['rows'][j]['data']
        for k,f in layout['SpEffectParam'].items():
            expected=get('SpEffectParam',i,k,True)
            if k in CHAINS:expected=mapping.get(expected,expected)
            assert decode(data,f)==expected,(i,j,k)
    audit={'weapon_rows_checked':len(base_ids),'changed_weapon_rows':len(weapon_changes),
           'custom_weapon_sources':{str(i):base for i,base in base_ids.items() if i!=base},
           'official_status_chain_rows':len(native),'new_private_effect_rows':len(additions),
           'private_offset':PRIVATE_OFFSET,'mapping':{str(i):j for i,j in sorted(mapping.items())},
           'removed_resident_status_slots':removed,'weapon_changes':records,
           'changed_field_counts':dict(Counter(k for r in records for k in r['fields'])),
           'validation':['192 non-target PARAM members byte-identical',
                         'all existing shared SpEffect rows byte-identical',
                         'all weapon passive-message slots match official source',
                         'all weapon inherent status-hit effects match official graph via private copies',
                         'all reinforcement status-effect ID offsets resolve correctly',
                         'all other weapon fields including damage, scaling, skill, weight and defense identical',
                         'extra resident status sources restored to official resident slots'],
           'scope_note':'Global attribute/reinforcement scaling remains the existing damage balance; this restores native status-hit effects, their damage/timing/chains, weapon status selectors and passive labels, not all global damage-growth curves.',
           'game_validation':'not run'}
    return output,audit


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--official-bnd',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--expected-sha256');args=p.parse_args()
    assert args.input.resolve()!=args.output.resolve()
    source=args.input.read_bytes();key=bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    if args.expected_sha256:assert sha(source)==args.expected_sha256
    header,raw=unpack(source,key);output,audit=patch(raw,args.official_bnd.read_bytes())
    assert patch(output,args.official_bnd.read_bytes())[0]==output,'Not idempotent'
    packed=zstd.ZstdCompressor(compression_params=zstd.ZstdCompressionParameters.from_level(
        15,window_log=16,write_content_size=False)).compress(output)
    h=bytearray(header);struct.pack_into('>II',h,28,len(output),len(packed))
    plain=bytes(h)+packed;plain+=bytes(-len(plain)%16);iv=bytes(16)
    enc=Cipher(algorithms.AES(key),modes.CBC(iv)).encryptor();result=iv+enc.update(plain)+enc.finalize()
    assert unpack(result,key)[1]==output
    audit.update(input_sha256=sha(source),output_sha256=sha(result),output_bytes=len(result),
                 official_bnd_sha256=sha(args.official_bnd.read_bytes()),bnd_bytes=len(output),
                 status='static checks passed; game validation not run')
    audit['validation']+=['idempotence and encrypted round-trip passed']
    args.output.parent.mkdir(parents=True,exist_ok=True);args.audit.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(result);args.audit.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:audit[k] for k in ['weapon_rows_checked','changed_weapon_rows',
                                        'new_private_effect_rows','output_sha256','output_bytes']}))


if __name__=='__main__':main()
