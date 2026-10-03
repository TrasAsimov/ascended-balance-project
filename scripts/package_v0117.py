"""Integrate the fixed HP T2, music, academy and field maps into one NIGHTTIDE ZIP."""
import argparse,hashlib,json,re,tomllib,zipfile
from pathlib import Path

INPUT_SHA={
 'baseline.zip':'dd57506cfcf913fe264589c230cce5459eedbd0a5f752c12e2623fa16b73eb0f',
 'Gnoster_Music_Fix01_With_HP_T2_Update.zip':'5f0e19c55a213a0ab86aa8fd65c9e2f8e6c4827c5f517e992fe7104ee4193826',
 'Evernight_Field_Giant_Cleanup_Update.zip':'42505e0afc7d81e5561bd1a5068c6daede2d3bf3fba22572cd8281fc81c93cf4',
 '01_Academy_Global_Enemy_Balance_20261003_regulation.bin':'dfd0e8eab3442925d654a72f1515939e52a3e073be16fde6bc35dc1a9372585c',
 '01_Academy_Global_Enemy_Balance_20261003_m14_00_00_00.msb.dcx':'1bb6d0aa061073b67c6c542e62ce18330d1c0f2fd2f202437f323618450598e0'}

README='''ELDEN RING: NIGHTTIDE / 艾尔登法环：黑夜入侵
v0.10.17 完整整合测试版
只下载本完整ZIP，解压到全新目录；不需要旧核心、扩展或补丁。
需要游戏本体及全部DLC、已安装ME3、Steam可用；备份存档并离线测试。
运行 ModEngine/launchmod_eldenring.bat。启动前自动校验所有运行文件。
找不到ME3时，请用已安装ME3打开 ModEngine/nighttide_v0117.me3。
ME3安装：https://github.com/garyttierney/me3/releases

包含最新核心、Caligo与地下双石像鬼区域的Gnoster/Faurtis完整资源。
静态NG0名义HP：Caligo1125000，Gnoster585384，Faurtis914616。
Caligo在当前最大HP60%转阶段；双虫保留作者80%/55%/10%阶段比例。
周目与联机仍另缩放。高血量需CaligoHpCapFix.log显示APPLIED或ALREADY_APPLIED；
此模块解除本次进程全局HP上限，其它超上限角色也可能受影响。
双虫采用法环原生MidBoss_Cave音乐，修正主机入场通知/音乐旗标；非黑夜君临原曲。
全游戏死亡骑士名义HP150000/圣减伤-40%，鲜血怪物首领名义HP136000，
大型七鳃鳗圣减伤-20%。学院红狼、女王召唤拉达冈及两只洛雷塔物理减伤10%，
召唤拉达冈HP180000；最终拉达冈与其它地区洛雷塔保持原值。
禁域途中与洛德大升降机上方两只额外野外火焰巨人在正式版禁用，正式Boss保留。
核心保留六护符（原生4+赐福菜单额外2）、玩家基础HP×2.5、小战士壶战技40%、
初始十种护符/两新职业/8记忆槽/心脏奖励/套装/近战强化/高跳/碎星回血减半。

文件与静态检查通过，本轮未运行Windows游戏。用户已反馈双虫移植测试通过，
后续HP、音乐、学院数值及地图清理仍需复测；不代表本整包已实机验收。
源资源既有缺引用与共享AI/材质/音频风险仍存在；英文文本包含，中文游戏档案未取得。
测试：读档保存/六槽/HP模块日志；Caligo满红与60%阶段；双虫首次/重试/骑乘BGM、
击败停止/心脏奖励/棺材；学院和全游戏目标敌人数值；禁域及大升降机路线。

第三方资源及源码归各原作者，署名见CREDITS.txt；未宣称作者背书。
https://github.com/TrasAsimov/ELDEN-RING--NIGHTTIDE
'''
def sha(b):return hashlib.sha256(b).hexdigest()
def load(path,prefix=''):
 assert sha(path.read_bytes())==INPUT_SHA[path.name],path.name
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  names=z.namelist();assert len(names)==len(set(names))
  assert all(n.startswith(prefix) and '..' not in Path(n).parts and not n.startswith('/') for n in names)
  return {n[len(prefix):]:z.read(n) for n in names if not n.endswith('/')}
def build(inputs,out):
 base=load(inputs/'baseline.zip','Evernight_Reforged_Boss_HP_T2/')
 music=load(inputs/'Gnoster_Music_Fix01_With_HP_T2_Update.zip')
 giants=load(inputs/'Evernight_Field_Giant_Cleanup_Update.zip')
 final={n:b for n,b in base.items() if n.startswith('ModEngine/mod/') or n in ('ModEngine/CaligoHpCapFix.dll','ModEngine/ExpandedTalismanSlots.dll','ModEngine/ExpandedTalismanSlots.ini')}
 overrides=[]
 def replace(n,b,before,after):
  assert sha(final[n])==before,(n,'baseline mismatch')
  assert sha(b)==after,(n,'candidate mismatch')
  overrides.append({'path':n,'before':before,'after':after});final[n]=b
 audit=json.loads((inputs/'01_Academy_Global_Enemy_Balance_20261003_audit.json').read_text())
 # Music's regulation is the unmodified HP T2 regulation; never overlay it after academy.
 assert music['ModEngine/mod/regulation.bin']==final['ModEngine/mod/regulation.bin']
 replace('ModEngine/mod/event/m12_02_00_00.emevd.dcx',music['ModEngine/mod/event/m12_02_00_00.emevd.dcx'],'9395cb31aed4c0157fe4ab3ac06313cf500b76ceda05300b65aadf41a03fd4d7','a5feaf2d155be8bf3f71c364955b3a86dd09ae140924030126c720157c3d73da')
 for suffix,k in [('regulation.bin','regulation'),('map/MapStudio/m14_00_00_00.msb.dcx','map')]:
  filename='01_Academy_Global_Enemy_Balance_20261003_'+('regulation.bin' if k=='regulation' else 'm14_00_00_00.msb.dcx')
  b=(inputs/filename).read_bytes();assert sha(b)==INPUT_SHA[filename]
  replace('ModEngine/mod/'+suffix,b,audit['baseline_'+k+'_sha256'],audit[k+'_sha256'])
 for entry in json.loads(giants['Field_Giant_Cleanup/audit.json'])['maps']:
  replace('ModEngine/mod/map/MapStudio/'+entry['map'],giants['Field_Giant_Cleanup/maps/'+entry['map']],entry['before_SHA256'],entry['after_SHA256'])
 profile=base['ModEngine/evernight_gnoster_t1.me3'].decode().replace('evernight_gnoster_t1','nighttide_v0117')
 cfg=tomllib.loads(profile);assert len(cfg['packages'])==1 and len(cfg['natives'])==2
 assert cfg['packages'][0]['path']=='mod'
 hp=[x for x in cfg['natives'] if x['path']=='CaligoHpCapFix.dll'][0]
 assert hp['initializer']['function']=='CaligoHpCapInitialize' and hp['load_early']
 final['ModEngine/nighttide_v0117.me3']=profile.encode()
 checks={n[len('ModEngine/'):].replace('/','\\'):sha(b) for n,b in final.items()}
 ps="$ErrorActionPreference = 'Stop'\n$checks = @{\n"+''.join(" '"+n+"' = '"+h+"'\n" for n,h in sorted(checks.items()))+"}\nforeach ($rel in $checks.Keys) {\n $p=Join-Path $PSScriptRoot $rel\n if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw \"Missing file: $rel\" }\n if ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $checks[$rel]) { throw \"File mismatch: $rel. Extract the complete NIGHTTIDE v0.10.17 ZIP into a clean directory.\" }\n}\nWrite-Host 'NIGHTTIDE v0.10.17 runtime verified.'\n"
 final['ModEngine/check_v0117.ps1']=ps.encode()
 bat=base['ModEngine/launchmod_eldenring.bat'].decode().replace('check_gnoster_t1.ps1','check_v0117.ps1').replace('evernight_gnoster_t1.me3','nighttide_v0117.me3').replace('Gnoster T1','NIGHTTIDE v0.10.17')
 final['ModEngine/launchmod_eldenring.bat']=bat.replace('\r\n','\n').replace('\n','\r\n').encode()
 final['README.txt']=README.encode('utf-8-sig')
 final['CREDITS.txt']=base['Gnoster_Test/CREDITS.txt']+b'\nCaligo: DDMMDD09, Nexus8583\nHP-cap signature: NymicRazor / Named-Blade, Nexus5732\nExpanded Talisman Slots 1.1.6: imCioco, Nexus10481\nAscended: original mod author; Elden Ring assets: FromSoftware / Bandai Namco.\n'
 runtime_checks=re.findall(r" '([^']+)' = '([a-f0-9]{64})'",ps)
 assert len(runtime_checks)==len(checks) and len(checks)==1014
 for n,h in runtime_checks:assert sha(final['ModEngine/'+n.replace('\\','/')])==h
 assert sum(n.endswith('/regulation.bin') for n in final)==1
 assert sum(n.endswith('.bat') for n in final)==1
 assert not any('expansions/' in n or 'Gnoster_Test/' in n or 'Boss_HP_T2/' in n for n in final)
 changed={x['path'] for x in overrides};preserved=[n for n in base if n.startswith('ModEngine/mod/') and n not in changed]
 assert all(final[n]==base[n] for n in preserved)
 manifest={n:{'bytes':len(b),'sha256':sha(b)} for n,b in sorted(final.items())}
 final['SHA256_FILES.txt']=''.join(v['sha256']+'  '+n+'\n' for n,v in manifest.items()).encode()
 out.mkdir(parents=True,exist_ok=True);dest=out/'ELDEN_RING_NIGHTTIDE_v0.10.17_Full_Test.zip';prefix='ELDEN_RING_NIGHTTIDE_v0.10.17/'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for n,b in sorted(final.items()):
   i=zipfile.ZipInfo(prefix+n,(2026,10,3,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b,compresslevel=6)
 with zipfile.ZipFile(dest) as z:
  assert z.testzip() is None and len(z.namelist())==len(final)
  for n,b in final.items():assert z.read(prefix+n)==b
  for n,v in manifest.items():assert sha(z.read(prefix+n))==v['sha256']
 report={'version':'v0.10.17','filename':dest.name,'bytes':dest.stat().st_size,'sha256':sha(dest.read_bytes()),'file_count':len(final),'runtime_checks':len(checks),'preserved_base_runtime_files':len(preserved),'overrides':overrides,'removed_developer_or_old_loader_paths':sorted(set(base)-set(final)),'inputs':INPUT_SHA,'CRC_all_bytes_internal_hashes':'passed','one_mod_one_regulation_one_bat':True,'Windows_game_test':'NOT RUN'}
 (out/'package_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 (out/'runtime_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 (out/'SHA256SUMS.txt').write_text(report['sha256']+'  '+dest.name+'\n')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.inputs,a.output)
