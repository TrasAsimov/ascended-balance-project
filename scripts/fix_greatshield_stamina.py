"""Fix only Greatshield Talisman guarding cost; preserve all other rows.

The legacy owned 912-byte SpEffect definition labels guardStaminaMult as
the first four bytes of pad3[8]. libER/Smithbox identify it at offset 0x388.
"""
import argparse, json, os, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from disable_player_debuffs import unpack,sha
from build_minor_boss_heart import pack_regulation
from analyze_regulation import read_param
from field_diff import fields,decode
from formats import bnd_entries,bnd_repack,param_patch

def patch(raw,paramdef):
    parts=bnd_entries(raw)
    assert len(parts)==194 and raw[24:32]==b'11711000'
    fs,size=fields(paramdef); layout={f[0]:f for f in fs}
    sp=read_param(parts['SpEffectParam.param'][1],'SpEffectParam')
    assert size==sp['row_size']==912
    if 'guardStaminaMult' in layout:
        offset=layout['guardStaminaMult'][2]
    else:
        assert layout['pad3'][2:4]==(904,8)
        offset=904
    assert offset==0x388
    row=sp['rows'][341000]['data']; body=bytearray(row)
    assert decode(row,layout['stateInfo'])==158
    cut=layout['guardStaminaCutRate'][2]
    struct.pack_into('<f',body,cut,1.0)
    struct.pack_into('<f',body,offset,0.2)
    out=bnd_repack(raw,{'SpEffectParam.param':param_patch(
        parts['SpEffectParam.param'][1],{341000:bytes(body)},{},size)})
    after=bnd_entries(out)
    assert all(after[n][1]==v[1] for n,v in parts.items() if n!='SpEffectParam.param')
    check=read_param(after['SpEffectParam.param'][1],'SpEffectParam')
    assert check['rows'].keys()==sp['rows'].keys()
    allowed=set(range(cut,cut+4))|set(range(offset,offset+4))
    for rid,rec in sp['rows'].items():
        new=check['rows'][rid]
        assert new['name']==rec['name']
        if rid!=341000: assert new['data']==rec['data']
        else: assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(rec['data'],new['data'])))
    assert struct.unpack_from('<f',check['rows'][341000]['data'],offset)[0]>0
    return out,{'effect':341000,'guardStaminaCutRate_before':struct.unpack_from('<f',row,cut)[0],
        'guardStaminaCutRate_after':1.0,'guardStaminaMult_offset':offset,
        'guardStaminaMult_before':struct.unpack_from('<f',row,offset)[0],
        'guardStaminaMult_after':0.2,'other_effect_rows_unchanged':True,'other_param_tables_unchanged':193}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--paramdef',type=Path,required=True);p.add_argument('--audit',type=Path,required=True)
    a=p.parse_args();key=bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    src=a.input.read_bytes();h,raw=unpack(src,key)
    out,report=patch(raw,a.paramdef); assert patch(out,a.paramdef)[0]==out
    # The positive remaining cost is reduced by 80%, never forced to zero.
    for boost in range(100):
        for incoming in [1,10,100,1000]:
            baseline=incoming*(1-boost/100);new=baseline*.2
            assert new>0 and abs(new/baseline-.2)<1e-12
    blob=pack_regulation(h,out,key);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(blob)
    report.update(input_sha256=sha(src),output_sha256=sha(blob),idempotence=True,
        modeled_guard_cases=400,game_validation='not run',
        target='80% less guarding stamina cost relative to no talisman; no Guard Boost change')
    a.audit.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
