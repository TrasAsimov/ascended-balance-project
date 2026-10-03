from pathlib import Path
import argparse,sys,struct,zipfile,json,hashlib,re
from inspect_maps import actors,sections
sys.path.insert(0,str(Path(__file__).resolve().parent/'source'))
from formats import dcx_unpack,dcx_pack
ROOT=Path(__file__).resolve().parent
PREFIX='Evernight_Reforged_Boss_HP_T2/'
TARGETS={'m60_48_51_00.msb.dcx':'c3160_9002','m60_49_53_00.msb.dcx':'c4210_9009'}
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);args=ap.parse_args()
    assert sha(args.base.read_bytes())=='dd57506cfcf913fe264589c230cce5459eedbd0a5f752c12e2623fa16b73eb0f'
    out=ROOT/'package';out.mkdir(exist_ok=True);module=out/'Field_Giant_Cleanup';(module/'maps').mkdir(parents=True,exist_ok=True)
    reports=[];replacements={}
    with zipfile.ZipFile(args.base) as z:
        for name,actor_name in TARGETS.items():
            rel='ModEngine/mod/map/MapStudio/'+name;blob=z.read(PREFIX+rel);raw=dcx_unpack(blob);old=actors(raw)
            targets=[a for a in old if a['name']==actor_name and a['model']=='c4760' and a['npc']==47600000]
            assert len(targets)==1;target=targets[0];assert target['edition_disable']==0
            patched=bytearray(raw);struct.pack_into('<I',patched,target['offset']+68,1)
            changes=[i for i,(a,b) in enumerate(zip(raw,patched)) if a!=b]
            assert changes==[target['offset']+68] and len(raw)==len(patched)
            assert sections(raw)==sections(patched)
            now=actors(patched)
            for a,b in zip(old,now):
                if a['name']==actor_name:assert b=={**a,'edition_disable':1}
                else:assert a==b
            packed=dcx_pack(patched);assert dcx_unpack(packed)==bytes(patched)
            (module/'maps'/name).write_bytes(packed);replacements[rel]=packed
            reports.append(dict(map=name,actor=target,operation='GameEditionDisable: 0 -> 1 (DisableInRelease)',raw_changed_offsets=changes,before_SHA256=sha(blob),after_SHA256=sha(packed),size=len(packed)))
        # Simulate the installer's narrow checksum replacements against the current Music Fix01 check file.
        with zipfile.ZipFile(ROOT.parent/'gnoster_music/Gnoster_Music_Fix01_With_HP_T2_Update.zip') as music:
            ps=music.read('ModEngine/check_gnoster_t1.ps1').decode('utf-8-sig');before=re.findall(r" '([^']+)'='([0-9a-f]{64})'",ps)
            for report in reports:
                key='mod\\map\\MapStudio\\'+report['map'];pattern=re.escape("'"+key+"'='")+r'[0-9a-fA-F]{64}'+re.escape("'")
                assert len(re.findall(pattern,ps))==1
                ps=re.sub(pattern,lambda m:"'"+key+"'='"+report['after_SHA256']+"'",ps)
            after=re.findall(r" '([^']+)'='([0-9a-f]{64})'",ps);assert len(before)==len(after)==1014
            checksum_changes=[]
            for (k,h),(k2,h2) in zip(before,after):
                assert k==k2;rel='ModEngine/'+k.replace('\\','/')
                b=replacements.get(rel)
                if b is None:b=music.read(rel) if rel in music.namelist() else z.read(PREFIX+rel)
                assert sha(b)==h2
                if h!=h2:checksum_changes.append(rel)
            assert set(checksum_changes)==set(replacements)
        formal=z.read(PREFIX+'ModEngine/mod/map/MapStudio/m60_13_13_02.msb.dcx')
        assert sum(a['model']=='c4760' and a['edition_disable']==0 for a in actors(dcx_unpack(formal)))==5
    audit={'version':'Field Giant Cleanup01','base':'Boss HP T2 maps; Music Fix01/other parameter updates retained in place','maps':reports,'modified_gameplay_files':list(replacements),'raw_total_changed_bytes':2,'all_indices_references_and_other_bytes_preserved':True,'formal_fire_giant_boss_map_untouched_SHA256':sha(formal),'installer_checksums_verified_in_python':len(after),'installer_edits_only_target_map_hashes':True,'regulation_and_events_in_package':False,'in_game_test':'NOT RUN','Windows_PowerShell_execution':'NOT RUN'}
    (module/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    (module/'Apply_Field_Giant_Cleanup.ps1').write_bytes(b'\xef\xbb\xbf'+(ROOT/'Apply_Field_Giant_Cleanup.ps1').read_bytes())
    bat='@echo off\ncd /d "%~dp0"\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Field_Giant_Cleanup\\Apply_Field_Giant_Cleanup.ps1"\nset "cleanup_result=%errorlevel%"\npause\nexit /b %cleanup_result%\n';(out/'Apply_Field_Giant_Cleanup.bat').write_bytes(bat.replace('\n','\r\n').encode('ascii'))
    readme='''野外巨人清理01：禁域与洛德大升降机
移除两只Ascended额外火焰巨人：禁域途中m60_48_51_00/c3160_9002；升降机上方萨米尔废墟附近m60_49_53_00/c4210_9009。
1. 完全退出游戏，把本包解压到当前完整包根目录，Apply_Field_Giant_Cleanup.bat应与ModEngine文件夹并列。
2. 双击Apply_Field_Giant_Cleanup.bat，显示Two field Fire Giants removed后关闭窗口。
3. 继续使用ModEngine/launchmod_eldenring.bat启动，重新载入该区域。
安装器仅更新这两个地图和对应启动校验/清单，自动备份原件；保留你当前regulation、音乐事件及其它模块。若这两个地图已被其它补丁改过，会停止并提示先合并，不会覆盖未知版本。重复运行不会再次修改敌人数值。
采用地图GameEditionDisable=1（正式游戏版本禁用），原Parts索引、实体/组、事件和所有引用保持。正式火焰巨人Boss场地保持，普通山妖与其他地区敌人保持。之前已禁用的7只雪山野外火焰巨人保持。
无需再击杀这两只，重新加载地图后应不出现。未运行Windows游戏/PowerShell；文件字节隔离、DCX读回、1014项启动哈希模拟、ZIP检查已通过，请游戏内确认两个地点。
后续统一整合：从Field_Giant_Cleanup/maps取这两个候选地图，替换同名路径，并刷新最新完整包check*.ps1及manifest对应SHA；不要拿旧regulation覆盖其它线程参数更新。audit.json记录原/新SHA及演员偏移；source包含可重建脚本。
''';(out/'README_Field_Giant_Cleanup.txt').write_bytes(b'\xef\xbb\xbf'+readme.encode())
    (module/'source').mkdir(exist_ok=True)
    for source in [ROOT/'build_cleanup.py',ROOT/'inspect_maps.py']:(module/'source'/source.name).write_bytes(source.read_bytes())
    (module/'source'/'source').mkdir(exist_ok=True)
    (module/'source'/'source'/'formats.py').write_bytes((ROOT/'source/formats.py').read_bytes())
    package=ROOT/'Evernight_Field_Giant_Cleanup_Update.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(out))
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        for p in out.rglob('*'):
            if p.is_file():assert z.read(str(p.relative_to(out)))==p.read_bytes()
    summary={'package':str(package),'size':package.stat().st_size,'sha256':sha(package.read_bytes()),'audit':audit};(ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
