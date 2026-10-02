"""Set Shield Grease to 300000s and normal Baldachin's Blessing to 1800s.

Run after older item-duration modules on the latest integrated inputs.
Uses existing project helpers, matching PARAM defs and
ARMOR_REGULATION_KEY_HEX. Includes no embedded format key.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import sys
import hashlib
import zstandard as zstd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'systems/armor/scripts'))
from disable_player_debuffs import unpack
from analyze_regulation import read_param
from formats import bnd_entries, bnd_repack, param_patch, bnd_patch, dcx_pack, dcx_unpack
from field_diff import fields, decode
from build_zhocn_patch import fmg_read, fmg_write

TARGETS = {503355: (3360, 1800.0, (30.0, 120.0, 1800.0)),
           501690: (1690, 300000.0, (60.0, 300000.0))}
INFOS = {3360: 'Uses 10 FP to boost poise for 30 minutes',
         1690: 'Boosts guarding and damage negation for 300,000 seconds'}
SUFFIX = '\n\nEffect: When used, spends 10 FP to boost poise for '
SHIELD_SUFFIX = '\n\nEffect: Guarding and damage negation boost lasts 300,000 seconds.'

def sha(blob): return hashlib.sha256(blob).hexdigest()

def patch_params(raw, defs):
    parts = bnd_entries(raw); assert len(parts) == 194 and raw[24:32] == b'11711000'
    spraw = parts['SpEffectParam.param'][1]
    sp = read_param(spraw, 'SpEffectParam')
    goods = read_param(parts['EquipParamGoods.param'][1], 'EquipParamGoods')
    sf, size = fields(defs/'SpEffect.xml'); gf, gs = fields(defs/'EquipParamGoods.xml')
    assert size == sp['row_size'] == 912 and gs == goods['row_size'] == 176
    sl = {f[0]: f for f in sf}; gl = {f[0]: f for f in gf}
    f = sl['effectEndurance']; assert f[1] == 'f32' and f[2:4] == (8,4)
    changes = {}; records = []
    for eid,(gid,value,accepted) in TARGETS.items():
        g = goods['rows'][gid]['data']; row = sp['rows'][eid]['data']
        assert decode(g,gl['refCategory']) == 2 and decode(g,gl['refId_default']) == eid
        old = decode(row,f); assert old in accepted
        body = bytearray(row); struct.pack_into('<f',body,8,value)
        if bytes(body) != row: changes[eid] = bytes(body)
        records.append({'goods_id':gid,'speffect_id':eid,'field':'effectEndurance','before':old,'after':value})
    updated = param_patch(spraw, changes, {}, size)
    allowed = set()
    for j in range(struct.unpack_from('<H',spraw,10)[0]):
        rid,_,off,_ = struct.unpack_from('<iIQQ',spraw,64+24*j)
        if rid in TARGETS: allowed.update(range(off+8,off+12))
    assert len(allowed)==8 and len(updated)==len(spraw)
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(spraw,updated)))
    after = read_param(updated,'SpEffectParam'); assert after['rows'].keys()==sp['rows'].keys()
    changed = [i for i in sp['rows'] if sp['rows'][i] != after['rows'][i]]
    assert set(changed)==set(changes)
    for eid,(_,v,_) in TARGETS.items(): assert decode(after['rows'][eid]['data'],f)==v
    result = bnd_repack(raw,{'SpEffectParam.param':updated}); checked = bnd_entries(result)
    assert checked.keys()==parts.keys()
    assert all(checked[n][1]==b for n,(_,b) in parts.items() if n!='SpEffectParam.param')
    return result,records,len(sp['rows'])-len(changed)

def patch_text(blob):
    raw=dcx_unpack(blob); parts=bnd_entries(raw); updates={}; records=[]
    names=fmg_read(parts['GoodsName.fmg'][1])
    assert names[3360]=="Baldachin's Blessing" and names[1690]=='Shield Grease'
    for name in ['GoodsInfo.fmg','GoodsCaption.fmg']:
        d=fmg_read(parts[name][1]); before=dict(d)
        for gid in INFOS:
            old=d[gid]; assert isinstance(old,str)
            if name=='GoodsInfo.fmg': d[gid]=INFOS[gid]
            elif gid==3360:
                base=old
                for ending in [SUFFIX+'2 minutes.',SUFFIX+'30 minutes.']:
                    if base.endswith(ending): base=base[:-len(ending)]
                d[gid]=base+SUFFIX+'30 minutes.'
            else:
                base=old.replace('\nThe effect lasts only for a short time.','')
                d[gid]=base if base.endswith(SHIELD_SUFFIX) else base+SHIELD_SUFFIX
            records.append({'fmg':name,'id':gid,'before':old,'after':d[gid]})
        assert all(d[i]==before[i] for i in d if i not in INFOS)
        if d!=before: updates[name]=fmg_write(d)
    result=dcx_pack(bnd_patch(raw,updates)) if updates else blob
    checked=bnd_entries(dcx_unpack(result))
    for name,(_,body) in parts.items():
        if name not in updates: assert checked[name][1]==body
        else:
            old,new=fmg_read(body),fmg_read(checked[name][1]); assert old.keys()==new.keys()
            assert all(old[i]==new[i] for i in old if i not in INFOS)
    return result,records

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--paramdefs',type=Path,required=True)
    p.add_argument('--text1',type=Path,required=True);p.add_argument('--text2',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    key=bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX']);source=a.input.read_bytes()
    header,raw=unpack(source,key);patched,records,unchanged=patch_params(raw,a.paramdefs)
    assert patch_params(patched,a.paramdefs)[0]==patched
    packed=zstd.ZstdCompressor(compression_params=zstd.ZstdCompressionParameters.from_level(
        15,window_log=16,write_content_size=False)).compress(patched)
    h=bytearray(header);struct.pack_into('>II',h,28,len(patched),len(packed))
    plain=bytes(h)+packed;plain+=bytes(-len(plain)%16);iv=bytes(16)
    enc=Cipher(algorithms.AES(key),modes.CBC(iv)).encryptor();result=iv+enc.update(plain)+enc.finalize()
    assert unpack(result,key)[1]==patched
    prefix='07_ShieldGrease_Baldachin_20261002'
    (a.out/(prefix+'_regulation.bin')).write_bytes(result)
    audit={'input_sha256':sha(source),'output_sha256':sha(result),'output_bytes':len(result),
           'param_version':'11711000','rows':records,'unchanged_tables':193,
           'unchanged_speffect_rows':unchanged,'texts':[],
           'checks':['only two duration fields changed; all other row bytes and names retained',
                     'all 193 other tables identical; compact BND; idempotence; encrypted round trip',
                     'text only GoodsInfo/Caption 1690 and 3360; all other active entries unchanged'],
           'game_validation':'not run'}
    for suffix,path in [('dlc01',a.text1),('dlc02',a.text2)]:
        blob=path.read_bytes();text,rows=patch_text(blob);assert patch_text(text)[0]==text
        name=prefix+'_engus_item_'+suffix+'.msgbnd.dcx';(a.out/name).write_bytes(text)
        audit['texts'].append({'input_sha256':sha(blob),'output_sha256':sha(text),'name':name,'rows':rows})
    (a.out/(prefix+'_audit.json')).write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:audit[k] for k in ['output_sha256','output_bytes','rows','unchanged_tables','unchanged_speffect_rows']}))

if __name__=='__main__':main()
