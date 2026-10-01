"""Conservative post-v0.10.7 integration; requires authorized local inputs."""
import argparse, json, os, struct, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'systems/armor/scripts')]
from disable_player_debuffs import unpack, sha
from build_minor_boss_heart import pack_regulation
from analyze_regulation import read_param
from field_diff import fields, decode, TYPES
from formats import bnd_entries, bnd_repack, param_patch

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--paramdef',type=Path,required=True)
    p.add_argument('--emedf',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    key=bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    z=zipfile.ZipFile(a.inputs/'Ascended_Balance_v0.10.7_Armor_Text_Layout.zip')
    prefix='Elden_Ascended_Mod_Age of the Endless Mod/'
    base=z.read(prefix+'ModEngine/mod/regulation.bin')
    candidate=(a.inputs/'02_Armor_Weapon_Filter_Fix_20261002_regulation.bin').read_bytes()
    assert sha(candidate)=='5fd2f52972159dfda55683af4b87f30beb1fbfa1a7ce6edd19d6fc118801c89a'
    header,raw=unpack(candidate,key); _,old=unpack(base,key)
    parts=bnd_entries(raw); prior=bnd_entries(old)
    assert parts.keys()==prior.keys()
    assert all(v[1]==prior[n][1] for n,v in parts.items() if n!='SpEffectParam.param')
    fs,size=fields(a.paramdef); lm={f[0]:f for f in fs}
    table=read_param(parts['SpEffectParam.param'][1],'SpEffectParam')
    bt=read_param(prior['SpEffectParam.param'][1],'SpEffectParam')
    assert table['rows'].keys()==bt['rows'].keys()
    changed=[]
    for rid,r in table['rows'].items():
        b=bt['rows'][rid]
        assert r['name']==b['name']
        if r['data']!=b['data']:
            diff=[f[0] for f in fs if decode(r['data'],f)!=decode(b['data'],f)]
            assert diff==['wepParamChange'],(rid,diff)
            assert decode(b['data'],lm['wepParamChange'])==3
            assert decode(r['data'],lm['wepParamChange'])==0
            changed.append(rid)
    assert len(changed)==234
    targets={321300:('AttackRate',4.0),321400:('AttackPowerRate',3.2)}
    updates={}
    for rid,(suffix,value) in targets.items():
        body=bytearray(table['rows'][rid]['data'])
        for attr in ['physics','magic','fire','thunder','dark']:
            f=lm[attr+suffix]; struct.pack_into('<'+TYPES[f[1]][0],body,f[2],value)
        updates[rid]=bytes(body)
    raw=bnd_repack(raw,{'SpEffectParam.param':param_patch(parts['SpEffectParam.param'][1],updates,{},size)})
    core=a.output/'core.bin'; core.write_bytes(pack_regulation(header,raw,key))
    common=a.output/'base_common.emevd.dcx'; common.write_bytes(z.read(prefix+'ModEngine/mod/event/common.emevd.dcx'))
    def run(script,*args):
        subprocess.run([sys.executable,str(ROOT/'scripts'/script),*map(str,args)],check=True)
    penalty=a.output/'penalty.bin'
    run('disable_player_debuffs.py','--input',core,'--output',penalty,'--paramdef',a.paramdef,'--audit',a.output/'penalty_audit.json')
    heart=a.output/'heart'
    run('build_minor_boss_heart.py','--regulation',penalty,'--common',common,'--paramdef',a.paramdef,'--emedf',a.emedf,'--output',heart)
    assert (heart/'common.emevd.dcx').read_bytes()==(a.inputs/'01_Minor_Boss_Heart_Bayle_20261002_common.emevd.dcx').read_bytes()
    run('verify_minor_boss_heart.py','--emedf',a.emedf,'--common',heart/'common.emevd.dcx','--report',a.output/'heart_simulation.json')
    final=a.output/'regulation.bin'
    run('reduce_player_spell_status.py','--input',heart/'regulation.bin','--output',final,'--audit',a.output/'spell_audit.json')
    _,actual=unpack(final.read_bytes(),key)
    _,reference=unpack((a.inputs/'06_Player_Spell_Status_50pct_20261002_regulation.bin').read_bytes(),key)
    ap=bnd_entries(actual); rp=bnd_entries(reference); delta={}
    assert ap.keys()==rp.keys()
    for n,v in ap.items():
        if v[1]==rp[n][1]:continue
        at=read_param(v[1],n[:-6]); rt=read_param(rp[n][1],n[:-6])
        assert at['rows'].keys()==rt['rows'].keys()
        assert n=='SpEffectParam.param',n
        for rid,r in at['rows'].items():
            b=rt['rows'][rid]; assert r['name']==b['name']
            if r['data']==b['data']:continue
            assert rid in targets,rid
            suffix,value=targets[rid]
            diff=[f[0] for f in fs if decode(r['data'],f)!=decode(b['data'],f)]
            assert set(diff)=={attr+suffix for attr in ['physics','magic','fire','thunder','dark']}
            assert all(abs(decode(r['data'],lm[f])-value)<1e-6 for f in diff)
            allowed={pos for f in diff for pos in range(lm[f][2],lm[f][2]+lm[f][3])}
            assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(r['data'],b['data'])))
            delta[str(rid)]=diff
    assert set(delta)=={'321300','321400'}
    report={'version':'0.10.8','armor_filter_rows':234,'composed_candidate_delta':delta,
            'regulation_sha256':sha(final.read_bytes()),'game_validation':'not run',
            'status':'all independent static integration checks passed'}
    (a.output/'integration_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
