"""Apply user-approved FP regeneration rates to the latest owned regulation.

Only five audited effects change. Each now ticks once per second; durations,
links, categories, costs, capacities, and every other parameter stay intact.
"""
import argparse,json,os,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from disable_player_debuffs import unpack,sha
from build_minor_boss_heart import pack_regulation
from analyze_regulation import read_param
from field_diff import fields,decode
from formats import bnd_entries,bnd_repack,param_patch

TARGETS={501290:5,501291:5,6202040:5,6202041:5,20380000:10}

def patch(raw,paramdef):
    parts=bnd_entries(raw)
    assert len(parts)==194 and raw[24:32]==b'11711000'
    fs,size=fields(paramdef);layout={f[0]:f for f in fs}
    sp=read_param(parts['SpEffectParam.param'][1],'SpEffectParam')
    assert size==sp['row_size']==912
    updates={};audit=[]
    for rid,rate in TARGETS.items():
        row=sp['rows'][rid]['data'];body=bytearray(row)
        assert decode(row,layout['changeMpRate'])==0
        assert decode(row,layout['changeHpRate'])==decode(row,layout['changeHpPoint'])==0
        before={k:decode(row,layout[k]) for k in ['motionInterval','changeMpPoint','effectEndurance','cycleOccurrenceSpEffectId','stateInfo']}
        assert before['motionInterval']>0 and before['changeMpPoint']<0
        struct.pack_into('<f',body,layout['motionInterval'][2],1.0)
        struct.pack_into('<i',body,layout['changeMpPoint'][2],-rate)
        updates[rid]=bytes(body)
        audit.append({'id':rid,'before':before,'before_fp_per_second':-before['changeMpPoint']/before['motionInterval'],
                      'after':{'motionInterval':1.0,'changeMpPoint':-rate},'after_fp_per_second':rate})
    out=bnd_repack(raw,{'SpEffectParam.param':param_patch(parts['SpEffectParam.param'][1],updates,{},size)})
    after=bnd_entries(out)
    assert all(after[k][1]==v[1] for k,v in parts.items() if k!='SpEffectParam.param')
    check=read_param(after['SpEffectParam.param'][1],'SpEffectParam')
    assert check['rows'].keys()==sp['rows'].keys()
    allowed=set(range(layout['motionInterval'][2],layout['motionInterval'][2]+4))|set(range(layout['changeMpPoint'][2],layout['changeMpPoint'][2]+4))
    changed=[]
    for rid,rec in sp['rows'].items():
        new=check['rows'][rid]
        assert new['name']==rec['name']
        if rid not in TARGETS:assert new['data']==rec['data']
        else:
            assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(rec['data'],new['data'])))
            assert decode(new['data'],layout['motionInterval'])==1.0
            assert decode(new['data'],layout['changeMpPoint'])==-TARGETS[rid]
            if new['data']!=rec['data']:changed.append(rid)
    return out,{'effects':audit,'actual_changed_effect_rows':changed,'other_tables_unchanged':193,
                'all_non_target_effect_rows_unchanged':True,'all_non_recovery_fields_unchanged':True,
                'game_validation':'not run','stacking':'unchanged; no global cap or new exclusion group'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--paramdef',type=Path,required=True);p.add_argument('--audit',type=Path,required=True)
    a=p.parse_args();key=bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX']);src=a.input.read_bytes()
    h,raw=unpack(src,key);out,report=patch(raw,a.paramdef);assert patch(out,a.paramdef)[0]==out
    blob=pack_regulation(h,out,key);assert unpack(blob,key)[1]==out
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(blob)
    report.update(input_sha256=sha(src),output_sha256=sha(blob),idempotence=True,encrypted_roundtrip=True)
    a.audit.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
