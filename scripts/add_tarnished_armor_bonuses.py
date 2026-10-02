"""Fill Tarnished Pack single-piece bonuses on the latest integrated regulation.

Keeps native bonuses/penalties and set effects. Reuses existing Ascended IDs;
no new effects, event edits, packaging, or release creation.
"""
import argparse, json, os, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from disable_player_debuffs import unpack,sha
from build_minor_boss_heart import pack_regulation
from analyze_regulation import read_param
from field_diff import fields,decode
from formats import bnd_entries,bnd_repack,param_patch
CONFIG=ROOT/'systems/armor/config/tarnished_piece_bonuses.json'
SLOTS=['residentSpEffectId','residentSpEffectId2','residentSpEffectId3']


def patch(raw,protector_def,effect_def):
    config=json.loads(CONFIG.read_text());parts=bnd_entries(raw)
    assert len(parts)==194 and raw[24:32]==b'11711000'
    fs,size=fields(protector_def);lm={f[0]:f for f in fs}
    armor=read_param(parts['EquipParamProtector.param'][1],'EquipParamProtector')
    assert size==armor['row_size']
    ef,esize=fields(effect_def);em={f[0]:f for f in ef}
    sp=read_param(parts['SpEffectParam.param'][1],'SpEffectParam')
    assert esize==sp['row_size']==912
    for eid,description in config['effects'].items():
        effect=sp['rows'][int(eid)]['data']
        for field,expected in description['expected_fields'].items():
            actual=decode(effect,em[field])
            assert abs(actual-expected)<1e-6,(eid,field,actual,expected)
    updates={};audit=[]
    for s,rec in config['armors'].items():
        rid=int(s);original=armor['rows'][rid]['data'];body=bytearray(original)
        before=[decode(original,lm[k]) for k in SLOTS];after=before.copy()
        assert all(eid in before for eid in rec['preserve_native_ids']),('native effect missing',rid,before)
        for eid in rec['add_effect_ids']:
            if eid in after:continue
            free=next((i for i,v in enumerate(after) if v<=0),None)
            assert free is not None,('No free slot; do not overwrite current effects',rid,after)
            after[free]=eid
        assert set(e for e in before if e>0)<=set(after)
        assert len(set(e for e in after if e>0))>=2
        for field,eid in zip(SLOTS,after):struct.pack_into('<i',body,lm[field][2],eid)
        updates[rid]=bytes(body)
        audit.append({'id':rid,'name':rec['name'],'before':before,'after':after,
                      'added':rec['add_effect_ids'],'native_effects_preserved':rec['preserve_native_ids']})
    out=bnd_repack(raw,{'EquipParamProtector.param':param_patch(parts['EquipParamProtector.param'][1],updates,{},size)})
    checked=bnd_entries(out)
    assert all(checked[k][1]==v[1] for k,v in parts.items() if k!='EquipParamProtector.param')
    reread=read_param(checked['EquipParamProtector.param'][1],'EquipParamProtector')
    assert reread['rows'].keys()==armor['rows'].keys()
    allowed={i for field in SLOTS for i in range(lm[field][2],lm[field][2]+4)}
    for rid,rec in armor['rows'].items():
        new=reread['rows'][rid]
        assert new['name']==rec['name']
        if rid not in updates:assert new['data']==rec['data']
        else:assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(rec['data'],new['data'])))
    return out,{'armor':audit,'changed_armor_rows':sum(rec['before']!=rec['after'] for rec in audit),
                'other_tables_byte_identical':193,'existing_effect_rows_byte_identical':True,
                'non_target_armor_rows_unchanged':True,'native_and_set_effects':'preserved',
                'game_validation':'not run'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ('input','output','protector-def','effect-def','audit'):
        p.add_argument('--'+flag,type=Path,required=True)
    a=p.parse_args();key=bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX']);src=a.input.read_bytes()
    h,raw=unpack(src,key);out,report=patch(raw,a.protector_def,a.effect_def)
    assert patch(out,a.protector_def,a.effect_def)[0]==out
    blob=pack_regulation(h,out,key);assert unpack(blob,key)[1]==out
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(blob)
    report.update(input_sha256=sha(src),output_sha256=sha(blob),idempotent=True,encrypted_roundtrip=True)
    a.audit.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
