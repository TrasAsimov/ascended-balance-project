"""Patch only approved English strings and produce a full audited v0.10.8 ZIP."""
import argparse,copy,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from update_minor_boss_heart_text import patch as heart_patch,ZH
from formats import bnd_entries,bnd_patch,dcx_pack,dcx_unpack
from fmg import fmg_read,fmg_write
from disable_player_debuffs import sha

def patch_text(blob):
    original=blob;blob=heart_patch(blob);raw=dcx_unpack(blob);parts=bnd_entries(raw);updates={}
    target={2130:'Charged heavy attack damage +300%.',2140:'Sorcery/incantation attack power +220%.'}
    for name,(_,body) in parts.items():
        if not name.startswith('AccessoryCaption'):continue
        d=fmg_read(body)
        if not any(rid in d for rid in target):continue
        for rid,text in target.items():
            assert rid in d;d[rid]=text
        updates[name]=fmg_write(d)
    assert updates
    result=dcx_pack(bnd_patch(raw,updates));after=bnd_entries(dcx_unpack(result));before=bnd_entries(dcx_unpack(original))
    assert before.keys()==after.keys()
    changed={}
    for name,(_,body) in before.items():
        if body==after[name][1]:continue
        a=fmg_read(body);b=fmg_read(after[name][1]);assert a.keys()==b.keys()
        ids=[rid for rid in a if a[rid]!=b[rid]]
        allowed={2130,2140} if name.startswith('AccessoryCaption') else {2001431} if name in ['GoodsInfo_dlc01.fmg','GoodsCaption_dlc01.fmg'] else set()
        assert set(ids)<=allowed,(name,ids);changed[name]=ids
    assert patch_again(result)==result
    return result,changed

def patch_again(blob):
    parts=bnd_entries(dcx_unpack(blob))
    assert heart_patch(blob)==blob
    for name,(_,body) in parts.items():
        if name=='AccessoryCaption.fmg':
            d=fmg_read(body);assert d[2130]=='Charged heavy attack damage +300%.';assert d[2140]=='Sorcery/incantation attack power +220%.'
    return blob

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    base=a.inputs/'Ascended_Balance_v0.10.7_Armor_Text_Layout.zip'
    assert sha(base.read_bytes())=='973c9fa4f65ac0c734376fb1049d5802fe3837efb5f6d84f86f2b045cd962b21'
    z=zipfile.ZipFile(base);assert z.testzip() is None;names=z.namelist();assert len(names)==len(set(names))
    prefix='Elden_Ascended_Mod_Age of the Endless Mod/';updates={};textaudit={}
    reg=(a.build/'regulation.bin').read_bytes()
    for name in ['regulation.bin','ModEngine/mod/regulation.bin']:updates[prefix+name]=reg
    updates[prefix+'ModEngine/mod/event/common.emevd.dcx']=(a.build/'heart/common.emevd.dcx').read_bytes()
    for name in ['item_dlc01.msgbnd.dcx','item_dlc02.msgbnd.dcx']:
        path=prefix+'ModEngine/mod/msg/engus/'+name;updates[path],textaudit[name]=patch_text(z.read(path))
    zh=json.loads(z.read(prefix+'Armor_Core/description_zh.json'))
    zh['accessory_core']={'2130':'蓄力重击伤害提高300%。','2140':'魔法/祷告攻击力提高220%。'}
    zh['heart']={'goods_id':2001431,'text':ZH,'status':'源合并数据；非 zhocn 游戏档案'}
    updates[prefix+'Armor_Core/description_zh.json']=(json.dumps(zh,ensure_ascii=False,indent=2)+'\n').encode()
    for name in ['README.md','README.zh-CN.md','CHANGELOG.md','docs/integration_20261002.md']:
        updates[prefix+'v0.10.8/'+name]=(ROOT/name).read_bytes()
    for name in ['integration_audit.json','penalty_audit.json','spell_audit.json','heart_simulation.json']:
        updates[prefix+'v0.10.8/audits/'+name]=(a.build/name).read_bytes()
    updates[prefix+'v0.10.8/audits/heart_audit.json']=(a.build/'heart/audit.json').read_bytes()
    updates[prefix+'v0.10.8/audits/text_audit.json']=(json.dumps(textaudit,indent=2)+'\n').encode()
    a.output.mkdir(parents=True,exist_ok=True);dest=a.output/'Ascended_Balance_v0.10.8_Unified_Integration.zip'
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        for info in z.infolist():out.writestr(copy.copy(info),updates.pop(info.filename,z.read(info.filename)))
        for name,body in updates.items():out.writestr(name,body)
    out=zipfile.ZipFile(dest);assert out.testzip() is None;assert len(out.namelist())==len(set(out.namelist()))
    changed=[n for n in names if z.read(n)!=out.read(n)]
    assert len(changed)==6,changed
    assert out.read(prefix+'regulation.bin')==out.read(prefix+'ModEngine/mod/regulation.bin')==reg
    hks=prefix+'ModEngine/mod/action/script/c0000.hks'
    assert sha(out.read(hks))=='30b1a2d3bb683169feff55c79528dbe2bb3cb96a58cca5c05d9cdb3a1e60d3d3'
    report={'package':dest.name,'bytes':dest.stat().st_size,'sha256':sha(dest.read_bytes()),'members':len(out.namelist()),'changed_existing_members':changed,'unchanged_existing_members':len(names)-len(changed),'new_members':len(out.namelist())-len(names),'crc':'passed','game_validation':'not run'}
    (a.output/'v0.10.8_package_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (a.output/'SHA256SUMS.txt').write_text(report['sha256']+'  '+dest.name+'\n')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
