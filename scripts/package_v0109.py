"""Produce a runtime-only ZIP; archive removed development records in Git."""
import argparse,gzip,hashlib,json,struct,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from formats import bnd_entries,bnd_repack,dcx_unpack,dcx_pack
from disable_player_debuffs import sha

def compact_text(raw):
    parts=bnd_entries(raw);end=struct.unpack_from('<Q',raw,40)[0]
    assert 64+36*len(parts)<=end<=min(struct.unpack_from('<I',raw,h+24)[0] for h,_ in parts.values())
    out=bytearray(raw[:end])
    for name,(h,body) in parts.items():
        nameoff=struct.unpack_from('<I',raw,h+32)[0];assert 64+36*len(parts)<=nameoff<end
        stop=raw.find(b'\x00\x00',nameoff)
        # Names are UTF-16; locate the actual aligned terminator.
        while stop%2!=nameoff%2:stop=raw.find(b'\x00\x00',stop+1)
        assert nameoff<=stop<end
        out.extend(bytes(-len(out)%16));offset=len(out)
        struct.pack_into('<QQI',out,h+8,len(body),len(body),offset);out.extend(body)
    checked=bnd_entries(out);assert checked.keys()==parts.keys()
    assert all(v[1]==checked[n][1] for n,v in parts.items())
    return bytes(out)

INSTALL='''Ascended Balance v0.10.9 — 最终整合测试版

备份存档并解压到全新目录，离线测试。Steam可用时运行ModEngine/launchmod_eldenring.bat。
ME3用户把mod目录指向ModEngine/mod；实际参数只有ModEngine/mod/regulation.bin。
不要混用旧版文件；缺少中文游戏档案时请使用英文显示查看新说明。

新增：盗贼面罩归属和护甲/盾牌Effect分区、大盾格挡减耗80%、武器固有异常恢复官方、
看门犬杖安装战灰、普通床帘恩泽120秒、蓝露滴10FP/s及其余已审计来源5FP/s。
保留核心、心脏成长、法术异常50%、高跳和其余已完成改动。
静态检查通过；游戏内效果、加载/保存、叠加和显示仍待复测。

先验证启动/读档/保存再载入，再比较大盾、战灰、武器异常、床帘120秒、10秒FP恢复，
并复测面罩套装、心脏/贝勒、法术异常及跳跃。需本体及全部DLC。
内部SHA256_FILES.txt校验运行文件；ZIP整体校验见Release的SHA256SUMS.txt。
开发文档、源码、对比和历史记录均在仓库，不在本安装包。
https://github.com/TrasAsimov/ascended-balance-project
'''

def keep(p):
    if p=='steam_appid.txt':return True,None
    if p.startswith('ModEngine/mod/'):
        if any(x in p for x in ['_DSAS_CACHE','_DSAS_PROJECT']):return False,'editor cache'
        if p.endswith(('.js','.temp','.log','.txt','.json','.patch','.zip','.csv')):return False,'development or temporary file'
        return True,None
    if p in ['ModEngine/config_eldenring.toml','ModEngine/launchmod_eldenring.bat','ModEngine/modengine2_launcher.exe']:return True,None
    if any(p.startswith('ModEngine/modengine2/'+d+'/') for d in ['bin','assets','crashpad','tools']):return True,None
    return False,'development documentation, SDK, unrelated launcher or duplicate'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-zip',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--layout',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    z=zipfile.ZipFile(a.base_zip);assert z.testzip() is None
    assert sha(a.base_zip.read_bytes())=='d73a47f780e27b2d9fdfeeaa329503188902113898f8a7f83f6448ca51027bba'
    prefix='Elden_Ascended_Mod_Age of the Endless Mod/';destprefix='Ascended_Balance_v0.10.9/'
    updates={'ModEngine/mod/regulation.bin':(a.build/'regulation.bin').read_bytes(),
             'ModEngine/mod/event/common.emevd.dcx':(a.layout/'ModEngine/mod/event/common.emevd.dcx').read_bytes()}
    compact={}
    for suffix in ['01','02']:
        n=f'01_FP_Regen_20261002_engus_item_dlc{suffix}.msgbnd.dcx'
        original=(a.build/'fp_text'/n).read_bytes();raw=dcx_unpack(original);clean=compact_text(raw)
        before=bnd_entries(raw);after=bnd_entries(clean)
        assert before.keys()==after.keys() and all(v[1]==after[k][1] for k,v in before.items())
        assert compact_text(clean)==clean
        blob=dcx_pack(clean);updates[f'ModEngine/mod/msg/engus/item_dlc{suffix}.msgbnd.dcx']=blob
        compact[suffix]={'source_bytes':len(original),'compact_bytes':len(blob),'all_live_FMG_members_identical':True,'sha256':sha(blob)}
    files={};removed=[];archived=[];unchanged=[];changed=[]
    for info in z.infolist():
        if info.is_dir():continue
        assert info.filename.startswith(prefix);relative=info.filename[len(prefix):]
        yes,reason=keep(relative);body=z.read(info.filename)
        if not yes:
            removed.append({'path':relative,'reason':reason})
            if relative.startswith(('审查清单/','Armor_Core/','changes/','v0.10.8/')) or relative.endswith(('.md','.csv')) and not relative.startswith('ModEngine/modengine2/'):
                folder='docs/archive/package_records' if relative.endswith('.md') else 'changes/archive/package_records'
                target=ROOT/folder/relative
                if len(body)>65536 and target.suffix in ['.csv','.json']:
                    target=target.with_name(target.name+'.gz');body=gzip.compress(body,mtime=0)
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.exists():assert target.read_bytes()==body
                else:target.write_bytes(body)
                archived.append(str(target.relative_to(ROOT)))
            continue
        new=updates.pop(relative,body);files[relative]=new
        (unchanged if new==body else changed).append(relative)
    assert not updates and len(changed)==4
    assert [n for n in files if n.endswith('regulation.bin')]==['ModEngine/mod/regulation.bin']
    assert sha(files['ModEngine/mod/action/script/c0000.hks'])=='30b1a2d3bb683169feff55c79528dbe2bb3cb96a58cca5c05d9cdb3a1e60d3d3'
    assert all(not p.endswith(('.zip','.patch','.temp','.js','.log','.csv','.json')) for p in files)
    files['README.txt']=INSTALL.encode('utf-8-sig')
    listing={n:{'bytes':len(b),'sha256':sha(b)} for n,b in sorted(files.items())}
    files['SHA256_FILES.txt']=''.join(v['sha256']+'  '+n+'\n' for n,v in listing.items()).encode()
    dest=a.output/'Ascended_Balance_v0.10.9_Final_Integration.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
        for n,b in sorted(files.items()):out.writestr(destprefix+n,b)
    check=zipfile.ZipFile(dest);assert check.testzip() is None
    assert len(check.namelist())==len(set(check.namelist()))==len(files)
    for n,b in files.items():assert check.read(destprefix+n)==b
    sums=check.read(destprefix+'SHA256_FILES.txt').decode()
    for line in sums.splitlines():digest,n=line.split('  ',1);assert sha(check.read(destprefix+n))==digest
    report={'version':'0.10.9','package':dest.name,'bytes':dest.stat().st_size,'sha256':sha(dest.read_bytes()),
            'file_count':len(files),'unchanged_runtime_files':len(unchanged),'changed_runtime_files':changed,
            'removed_files':removed,'archived_records':archived,'text_compaction':compact,'files':listing,
            'crc':'passed','extracted_bytes':'all identical','duplicate_paths':0,'regulation_copies':1,'game_validation':'not run'}
    (a.output/'package_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (a.output/'SHA256SUMS.txt').write_text(report['sha256']+'  '+dest.name+'\n')
    print(json.dumps({k:report[k] for k in ['package','bytes','sha256','file_count','unchanged_runtime_files','changed_runtime_files','crc']}))

if __name__=='__main__':main()
