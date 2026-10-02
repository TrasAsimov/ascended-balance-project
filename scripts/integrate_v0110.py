"""Rebuild every completed post-v0.10.9 module on the released runtime."""
import argparse, hashlib, json, os, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
import set_initial_memory_slots as memory
import set_item_durations as durations
import update_new_class_loadouts as loadouts
import boost_melee_reinforcement as melee
import add_tarnished_armor_bonuses as armor
import revise_new_class_builds as builds
import update_leontiel_skill as leontiel
import set_alexander_and_player_hp as alexander
import update_hit_stagger_text as stagger
import update_tarnished_armor_text as armor_text
from disable_player_debuffs import unpack, sha
from build_minor_boss_heart import pack_regulation
from formats import bnd_entries,dcx_unpack,dcx_pack
from package_v0109 import compact_text

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ['base_zip','paramdefs','official_bnd','emedf','candidate','candidate_common','output']:
        p.add_argument('--'+flag.replace('_','-'),type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    os.environ['ARMOR_PARAMDEFS']=str(a.paramdefs)
    import field_diff
    field_diff.DEFROOT=a.paramdefs
    key=bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    assert sha(a.base_zip.read_bytes())=='188d077e816e79e906901f23654523801dafe77eda511b51d88e9e1d2d49dbbf'
    z=zipfile.ZipFile(a.base_zip); assert z.testzip() is None
    prefix='Ascended_Balance_v0.10.9/ModEngine/mod/'
    source=z.read(prefix+'regulation.bin');header,raw=unpack(source,key)
    native=a.official_bnd.read_bytes(); report={'modules':[],'game_validation':'not run'}
    item=z.read(prefix+'msg/engus/item_dlc02.msgbnd.dcx')
    steps=[('memory',memory.patch),('durations',lambda r:durations.patch_params(r,a.paramdefs)[:2]),
      ('loadouts',loadouts.patch),('melee',lambda r:melee.apply(r,a.paramdefs,item)),
      ('armor',lambda r:armor.patch(r,a.paramdefs/'EquipParamProtector.xml',a.paramdefs/'SpEffect.xml')),
      ('builds',builds.patch),('leontiel',lambda r:leontiel.patch_params(r,native,a.paramdefs/'SpEffect.xml')),
      ('alexander_hp',lambda r:alexander.patch(r,native,a.paramdefs))]
    for name,fn in steps:
        before=sha(raw);raw,audit=fn(raw);assert fn(raw)[0]==raw,(name,'not idempotent')
        report['modules'].append({'name':name,'before_raw_sha256':before,'after_raw_sha256':sha(raw),'audit':audit,'idempotent':True})
        print(name,'passed',flush=True)
    blob=pack_regulation(header,raw,key);assert unpack(blob,key)[1]==raw
    expected=a.candidate/'01_Alexander40_HP250_20261002_regulation.bin'
    candidate_raw=unpack(expected.read_bytes(),key)[1]
    actual,expected_parts=bnd_entries(raw),bnd_entries(candidate_raw)
    assert actual.keys()==expected_parts.keys()
    from analyze_regulation import read_param
    mismatches={}
    for n,(_,body) in actual.items():
        if body!=expected_parts[n][1]:
            left,right=read_param(body,n[:-6]),read_param(expected_parts[n][1],n[:-6])
            changed=[rid for rid in left['rows'] if left['rows'][rid]!=right['rows'].get(rid)]
            mismatches[n]={'rows':changed,'added_or_removed':list(set(left['rows'])^set(right['rows'])),'size_actual':len(body),'size_candidate':len(expected_parts[n][1])}
    print('candidate differences',json.dumps(mismatches),flush=True)
    assert all(not v['rows'] and not v['added_or_removed'] for v in mismatches.values()),'Candidate PARAM row mismatch'
    assert set(mismatches)<= {'ReinforceParamWeapon.param'}
    from field_diff import fields
    from verify_layout import directory
    for n in mismatches:
        _,size=fields(a.paramdefs/(n[:-6]+'.xml'))
        directory(actual[n][1],size);directory(expected_parts[n][1],size)
    report['candidate_container_layout_differences']=mismatches
    (a.output/'regulation.bin').write_bytes(blob)
    common,event_audit=leontiel.patch_events(z.read(prefix+'event/common.emevd.dcx'),a.emedf)
    assert leontiel.patch_events(common,a.emedf)[0]==common
    assert common==a.candidate_common.read_bytes()
    (a.output/'common.emevd.dcx').write_bytes(common);report['events']=event_audit
    report['texts']={}
    for suffix in ['01','02']:
        text=z.read(prefix+f'msg/engus/item_dlc{suffix}.msgbnd.dcx');records=[]
        for name,fn in [('durations',durations.patch_text),('stagger',stagger.patch_archive),('armor',armor_text.archive),('leontiel',leontiel.patch_text),('alexander',alexander.patch_text)]:
            text,changed=fn(text);assert fn(text)[0]==text;records.append({'module':name,'changed':changed})
        cand=(a.candidate/f'01_Alexander40_HP250_20261002_engus_item_dlc{suffix}.msgbnd.dcx').read_bytes()
        before,other=bnd_entries(dcx_unpack(text)),bnd_entries(dcx_unpack(cand))
        assert before.keys()==other.keys() and all(b==other[n][1] for n,(_,b) in before.items()),'Candidate FMG mismatch'
        clean=compact_text(dcx_unpack(text));assert compact_text(clean)==clean
        text=dcx_pack(clean);(a.output/f'item_dlc{suffix}.msgbnd.dcx').write_bytes(text)
        report['texts'][suffix]={'records':records,'all_live_candidate_FMGs_identical':True,'sha256':sha(text)}
    report.update(regulation_sha256=sha(blob),common_sha256=sha(common),all_194_candidate_PARAM_rows_and_names_identical=True,encrypted_roundtrip=True)
    (a.output/'integration_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['modules','texts','events']}))

if __name__=='__main__':main()
