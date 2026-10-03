"""Flatten the v0.10.15 core and cumulative Caligo runtime into one ME3 mod."""
import argparse,hashlib,json,re,tomllib,zipfile
from pathlib import Path
from package_v0115 import package,sha

README='''Ascended Balance v0.10.16 — Caligo完整整合测试包
一个下载包、一个mod运行目录、一个启动入口；不需要旧核心或Caligo补丁。
需要本体和全部DLC、已安装ME3、Steam可用。备份存档，完整解压到全新目录。
运行ModEngine/launchmod_eldenring.bat，离线测试。不要覆盖旧目录或手动叠加参数包。
启动前PS1校验全部运行文件；ME3配置只加载ModEngine/mod，注册六护符DLL和HP模块。
如果找不到ME3，可使用已安装ME3打开ModEngine/evernight_v0116.me3。
ME3官方安装地址：https://github.com/garyttierney/me3/releases

包含v0.10.15全部核心改动和累计Caligo T1/T2/T3/Hotfix04候选：
六护符（原生4+赐福菜单额外2，INI slots=2）、基础HP×2.5、小壶战技40%、
两新职业/十礼物/心脏奖励、近战强化/8记忆槽/套装/高跳、碎星回血减半。
Caligo名义HP750000，按当前最大HP60%转阶段，非火承伤额外减少30%、异常阈值提高30%；
原火弱点、加强攻击/冰冻、3龙心脏与心脏追忆奖励、冰湖清理及道路3大弓魔像候选。
碎星回血三效果40/60/25 HP每秒，回蓝5FP每秒；重新使用追忆刷新，英文说明同步。

CaligoHpCapFix.log必须显示APPLIED或ALREADY_APPLIED，才是有效高HP测试。
HP模块解除本次进程全局524287上限，其它配置超过上限的角色也可能恢复配置HP。
签名缺失/重复将拒绝修改；不改游戏EXE文件或存档。灰段/实际血量仍需游戏验证。
原T1共享AI/材质/音频等依赖及未解决引用沿用，不能保证所有其它地区兼容。
静态/文件校验通过，未运行Windows游戏，不把候选修复记为实机成功。

测试顺序：启动读档/保存重载；六槽5/6效果与卸装；追忆回血；HP模块日志与Caligo
入场满红/真实HP/60%转阶段/声音/奖励；离开雪山再返回后，道路入口中段末端三只
加载开火、桥外停止；回归套装/心脏/高跳。使用英文，原生中文档案仍未取得。

外部测试发布由项目用户明确要求；第三方资源归各原作者，未宣称作者背书。
Caligo: DDMMDD09 https://www.nexusmods.com/eldenring/mods/8583
HP上限签名: NymicRazor / Named-Blade, Endless Cycles (Infinite NG)
https://www.nexusmods.com/eldenring/mods/5732
六护符: imCioco / Expanded Talisman Slots 1.1.6（作者DLL原件）
https://www.nexusmods.com/eldenring/mods/10481
'''
def read(p,expected,prefix=''):
 assert sha(p.read_bytes())==expected
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
  assert all(n.startswith(prefix) for n in z.namelist())
  return {n[len(prefix):]:z.read(n) for n in z.namelist()}
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--inputs',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
 core=read(args.inputs/'Ascended_Balance_v0.10.15_Integrated_Test.zip','d955452abcf28d79de0e4389ae35add1e9fd5b8987915828db4037b40e013635','Ascended_Balance_v0.10.15/')
 ext=read(args.inputs/'Caligo_v0.10.15_Private_Expansion.zip','66cd21e86883887ef592cc2b8791cc9ea46ea0c903a130424855ab921830eec3')
 final={n:b for n,b in core.items() if n.startswith('ModEngine/mod/') or n in ('ModEngine/ExpandedTalismanSlots.dll','ModEngine/ExpandedTalismanSlots.ini')}
 removed=sorted(set(core)-set(final));overlap=[];added=[]
 for n,b in ext.items():
  prefix='ModEngine/expansions/nightreign/caligo/'
  if n.startswith(prefix):
   target='ModEngine/mod/'+n[len(prefix):]
   if target in final:overlap.append({'path':target,'core_sha256':sha(final[target]),'merged_sha256':sha(b)})
   else:added.append(target)
   final[target]=b
  elif n=='ModEngine/CaligoHpCapFix.dll':final[n]=b
 profile='''profileVersion = "v1"
start_online = false
[[supports]]
game = "eldenring"
[[packages]]
id = "evernight_v0116"
path = 'mod'
[[natives]]
path = 'ExpandedTalismanSlots.dll'
[[natives]]
path = 'CaligoHpCapFix.dll'
optional = false
load_early = true
initializer = { function = "CaligoHpCapInitialize" }
'''
 assert len(tomllib.loads(profile)['packages'])==1
 final['ModEngine/evernight_v0116.me3']=profile.encode()
 checks={n[len('ModEngine/'):].replace('/','\\'):sha(b) for n,b in final.items()}
 ps="$ErrorActionPreference = 'Stop'\n$checks = @{\n"+''.join(" '"+n+"' = '"+h+"'\n" for n,h in sorted(checks.items()))+"}\nforeach ($rel in $checks.Keys) {\n $p=Join-Path $PSScriptRoot $rel\n if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw \"Missing file: $rel\" }\n if ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $checks[$rel]) { throw \"File mismatch: $rel. Extract the complete v0.10.16 ZIP into a clean directory.\" }\n}\nWrite-Host 'Complete v0.10.16 runtime verified.'\n"
 final['ModEngine/check_v0116.ps1']=ps.encode()
 bat=ext['ModEngine/launch_caligo_v0115.bat'].decode().replace('check_caligo_v0115','check_v0116').replace('caligo_v0115.me3','evernight_v0116.me3').replace('v0.10.15','v0.10.16')
 final['ModEngine/launchmod_eldenring.bat']=bat.replace('\r\n','\n').replace('\n','\r\n').encode()
 final['README.txt']=README.encode('utf-8-sig')
 changed={v['path'] for v in overlap};preserved=[n for n in core if n.startswith('ModEngine/mod/') and n not in changed]
 assert all(final[n]==core[n] for n in preserved)
 assert sum(n.endswith('/regulation.bin') for n in final)==1
 assert sum(n.endswith('.bat') for n in final)==1
 assert not any('expansions/' in n or 'modengine2/' in n or 'Caligo_Test/' in n for n in final)
 args.output.mkdir(parents=True,exist_ok=True)
 report,manifest=package(final,args.output/'Ascended_Balance_v0.10.16_Caligo_Full_Test.zip','Ascended_Balance_v0.10.16/')
 audit={'version':'v0.10.16','package':report,'core_preserved_non_overlap_runtime_files':len(preserved),'overrides_from_latest_merged_caligo':overlap,'new_caligo_runtime_paths':added,'obsolete_core_loader_paths_omitted':removed,'runtime_directory':'ModEngine/mod','single_launch':'ModEngine/launchmod_eldenring.bat','single_regulation':True,'game_test':'NOT RUN','scope':'User explicitly requested unified external test release'}
 (args.output/'package_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
 (args.output/'runtime_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 (args.output/'SHA256SUMS.txt').write_text(report['sha256']+'  '+report['filename']+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
