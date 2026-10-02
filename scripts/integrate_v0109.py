"""Sequential v0.10.9 integration with independently audited owned inputs."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from disable_player_debuffs import unpack,sha
from analyze_regulation import read_param
from field_diff import fields,decode
from formats import bnd_entries,dcx_unpack

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['base','layout','inputs','output','paramdefs','official_bnd']:p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    def run(n,*args):subprocess.run([sys.executable,str(ROOT/'scripts'/n),*map(str,args)],check=True)
    base=a.base/'ModEngine/mod/regulation.bin';assert sha(base.read_bytes())=='bf923783389021372e1d33d7bcc5e776c9b32e155af59f58fc0003142da44398'
    great=a.output/'great.bin';weapon=a.output/'weapon.bin';watch=a.output/'watchdog.bin';final=a.output/'regulation.bin'
    run('fix_greatshield_stamina.py','--input',base,'--output',great,'--paramdef',a.paramdefs/'SpEffect.xml','--audit',a.output/'greatshield_audit.json')
    assert sha(great.read_bytes())=='af8aef4daa0cee52542cb64c19672e2e0539c914c8f0ea0b51d526899ebc35f9'
    run('restore_weapon_status.py','--input',great,'--official-bnd',a.official_bnd,'--output',weapon,'--audit',a.output/'weapon_audit.json')
    assert sha(weapon.read_bytes())=='990fd980ee5311f380399f085f4c7f1dd11e2c73eac2cb4841306ae2376b7243'
    text=a.output/'great_text';run('update_greatshield_stamina_text.py','--input',a.layout/'ModEngine/mod/msg/engus','--output',text)
    bald=a.output/'baldachin'
    run('extend_baldachin_blessing.py','--input',weapon,'--output',bald,'--paramdefs',a.paramdefs,'--item-dlc01',text/'01_Greatshield_80pct_20261002_engus_item_dlc01.msgbnd.dcx','--item-dlc02',text/'01_Greatshield_80pct_20261002_engus_item_dlc02.msgbnd.dcx')
    baldreg=bald/'07_Baldachin_2min_20261002_regulation.bin'
    assert sha(baldreg.read_bytes())=='90ada3b2bb9a147e164d78421fec9ba9fe8da3e8cb9470648ccea829bca75f65'
    run('fix_watchdog_ashes.py','--input',baldreg,'--output',watch,'--audit',a.output/'watchdog_audit.json')
    run('normalize_fp_regen.py','--input',watch,'--output',final,'--paramdef',a.paramdefs/'SpEffect.xml','--audit',a.output/'fp_audit.json')
    textin=a.output/'bald_text';textin.mkdir(exist_ok=True)
    for suffix in ['01','02']:shutil.copyfile(bald/f'07_Baldachin_2min_20261002_engus_item_dlc{suffix}.msgbnd.dcx',textin/f'item_dlc{suffix}.msgbnd.dcx')
    run('update_fp_regen_text.py','--regulation',final,'--input',textin,'--output',a.output/'fp_text','--paramdefs',a.paramdefs,'--metadata-input',a.layout/'Armor_Core')
    key=bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    _,raw=unpack(final.read_bytes(),key);_,ref=unpack((a.inputs/'01_FP_Regen_20261002_regulation.bin').read_bytes(),key)
    ap=bnd_entries(raw);bp=bnd_entries(ref);assert ap.keys()==bp.keys()
    changes={}
    for name,(_,body) in ap.items():
        if body==bp[name][1]:continue
        assert name=='EquipParamWeapon.param',name
        at=read_param(body,'EquipParamWeapon');bt=read_param(bp[name][1],'EquipParamWeapon')
        assert at['rows'].keys()==bt['rows'].keys()
        lm={f[0]:f for f in fields(a.paramdefs/'EquipParamWeapon.xml')[0]}
        for rid,row in at['rows'].items():
            old=bt['rows'][rid];assert old['name']==row['name']
            if old['data']==row['data']:continue
            assert rid==23010000
            delta=[f for f in lm if decode(row['data'],lm[f])!=decode(old['data'],lm[f])]
            assert delta==['gemMountType'];assert decode(row['data'],lm['gemMountType'])==2;assert decode(old['data'],lm['gemMountType'])==0
            assert decode(row['data'],lm['swordArtsParamId'])==10;assert decode(row['data'],lm['disableGemAttr'])==1
            changes[str(rid)]=delta
    assert changes=={'23010000':['gemMountType']}
    textchecks={}
    for suffix in ['01','02']:
        name=f'01_FP_Regen_20261002_engus_item_dlc{suffix}.msgbnd.dcx'
        # Append-only text binders can retain different obsolete payloads.
        # Compare every live FMG byte rather than compression/layout history.
        current=bnd_entries(dcx_unpack((a.output/'fp_text'/name).read_bytes()))
        handed=bnd_entries(dcx_unpack((a.inputs/name).read_bytes()))
        assert current.keys()==handed.keys()
        assert all(v[1]==handed[n][1] for n,v in current.items())
        textchecks[name]=sha((a.output/'fp_text'/name).read_bytes())
    common=a.layout/'ModEngine/mod/event/common.emevd.dcx'
    assert sha(common.read_bytes())=='55d6ea60f6e5c812ccac3ebb5b316ba1f80e4d70436ed848895edeefec0d9ff5'
    report={'version':'0.10.9','regulation_sha256':sha(final.read_bytes()),'regulation_bytes':final.stat().st_size,
            'independent_FP_candidate_delta':changes,'english_matches_handoff':textchecks,'common_sha256':sha(common.read_bytes()),
            'inherited_v0108_modules':'preserved; no second spell-status reduction','game_validation':'not run'}
    (a.output/'integration_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
