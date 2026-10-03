"""Merge the current core and private Caligo candidates without publishing donor assets."""
import argparse, hashlib, json, os, sys, tempfile, tomllib, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'systems/armor/scripts')]
from halve_radahn_hp import run, unpack
from build_v03 import KEY
from formats import dcx_unpack, dcx_pack, bnd_entries, bnd_patch
from fmg import fmg_read, fmg_write
from package_v0109 import compact_text

INPUTS = {
 'Ascended_Balance_v0.10.14_Six_Talismans_Test.zip': '126b9f329ab2343f72669762c1d0fbcbf767508cd9a7ad39db92b6b69ca9330f',
 'Caligo_T1_Expansion.zip': 'cf59b7fc78756ffc9b84f41b25b0ecad04e2434073979cc1d4be14966fae315b',
 'Caligo_T2_Update.zip': '39dc34f58cfea20f3b2695cc9e8c7fd038c3499a3c6f7e4d7a28284ff60e1686',
 'Caligo_T3_Balance_Golems.zip': '004b9fe5701dbe90bc889d7d97ec36835afc46f6c1ce67006ccde137ebe2b0e6',
 'Caligo_T3_Hotfix_04.zip': '1e530d074e0751184be17e918fcdf0f1f43706d2e5074f026bb0f4f578928815',
}
def sha(b): return hashlib.sha256(b).hexdigest()
def load(p):
 assert sha(p.read_bytes()) == INPUTS[p.name], p.name
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  names=z.namelist(); assert len(names)==len(set(names))
  assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
  return {n:z.read(n) for n in names if not n.endswith('/')}

def heal(blob, work, label):
 source=work/(label+'_input.bin'); output=work/(label+'_output.bin'); source.write_bytes(blob)
 report=run(source,output,KEY); result=output.read_bytes()
 again=work/(label+'_again.bin'); run(output,again,KEY); assert again.read_bytes()==result
 report['idempotence']='passed'
 return result,report

def text(blob):
 raw=dcx_unpack(blob); parts=bnd_entries(raw); entries=fmg_read(parts['GoodsCaption.fmg'][1]); old=entries[2951]
 expected='Effect: casts all base game body buffs; Restores 5 FP every second.'
 replacement='Effect: casts all base game body buffs. HP regeneration reduced by half: 40 / 60 HP per second from the respective body effects; 25 HP per second from the attack-triggered effect. Restores 5 FP every second.'
 assert expected in old or replacement in old
 entries[2951]=old.replace(expected,replacement)
 changed=compact_text(bnd_patch(raw,{'GoodsCaption.fmg':fmg_write(entries)}))
 check=bnd_entries(changed)
 for name,(_,body) in parts.items():
  if name!='GoodsCaption.fmg':assert check[name][1]==body
 before=fmg_read(parts['GoodsCaption.fmg'][1]); after=fmg_read(check['GoodsCaption.fmg'][1])
 assert set(before)==set(after) and all(before[k]==after[k] for k in before if k!=2951)
 return dcx_pack(changed)

def package(files,dest,prefix):
 files=dict(files); files.pop('SHA256_FILES.txt',None)
 manifest={n:{'bytes':len(b),'sha256':sha(b)} for n,b in sorted(files.items())}
 files['SHA256_FILES.txt']=''.join(v['sha256']+'  '+n+'\n' for n,v in manifest.items()).encode()
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for n,b in sorted(files.items()):
   i=zipfile.ZipInfo(prefix+n,(2026,10,3,0,0,0)); i.compress_type=zipfile.ZIP_DEFLATED; i.external_attr=0o100644<<16
   z.writestr(i,b,compresslevel=6)
 with zipfile.ZipFile(dest) as z:
  assert z.testzip() is None and len(z.namelist())==len(files)
  for n,b in files.items():assert z.read(prefix+n)==b
  for line in z.read(prefix+'SHA256_FILES.txt').decode().splitlines():
   digest,n=line.split('  ',1);assert sha(z.read(prefix+n))==digest
 return {'filename':dest.name,'bytes':dest.stat().st_size,'sha256':sha(dest.read_bytes()),'file_count':len(files),'CRC_all_bytes_internal_hashes':'passed'},manifest

CORE_README='''Ascended Balance v0.10.15 — 最近改动整合测试版
备份存档，完整解压到全新目录，离线测试。需要本体与全部DLC。
核心启动：ModEngine/launchmod_eldenring.bat。原生ME3仍需登记ExpandedTalismanSlots.dll。
六护符＝原生四槽＋赐福Expanded Talisman Slots菜单额外两槽；INI slots=2。
碎星追忆三条回血效果由80/120/50改为40/60/25 HP每秒；回蓝仍5FP每秒。
重新使用追忆刷新效果，记录无攻击10秒与攻击触发恢复；叠加表现待游戏确认。
保留v0.10.14其余运行内容：HP×2.5、小战士壶战技40%、初始十种护符、
两新职业小壶、心脏181场、近战强化、8记忆槽、套装与高跳。
Caligo资源仅在配套私人扩展中；不属于公开核心包。请先安装本版再覆盖新扩展，
仅使用新扩展的launch_caligo_v0115.bat，不再逐个安装T1/T2/T3/HF补丁。
静态与整包校验通过，未运行Windows游戏。英文文字包含；中文JSON不是游戏语言包。
感谢imCioco / Expanded Talisman Slots 1.1.6，作者DLL原样保留：
https://www.nexusmods.com/eldenring/mods/10481
https://github.com/TrasAsimov/ascended-balance-project
'''
PRIVATE_README='''Caligo v0.10.15 私人整合扩展（累计T1、T2、T3、Hotfix04及回血减半）
先将Ascended Balance v0.10.15完整核心解压到全新目录，再合入本包ModEngine目录。
不用旧内测目录叠装，不需要另外安装旧补丁。启动ModEngine/launch_caligo_v0115.bat。
需要已安装ME3。BAT校验全部扩展文件、v0.10.15核心参数、六护符DLL和INI。
新版入口注册六护符与CaligoHpCapFix.dll，扩展在核心之后加载。
必须核对CaligoHpCapFix.log的APPLIED或ALREADY_APPLIED；无日志或FAILED_NO_PATCH
不代表解除上限成功。HP补丁作用于本次进程的全局引擎上限，其它超过524287的
角色也可能恢复配置HP，不是Caligo单实体补丁，不改游戏EXE或存档。
Caligo静态单周目HP750000，当前最大HP60%进入二阶段（名义450000）。
保留非火承伤额外减少30%、异常阈值提高30%、原火焰弱点、攻击/冰冻加强、
三龙心脏奖励、心脏追忆计数、冰湖清理、三只长走道魔像及1300米探测候选。
回血减半同时在核心和优先加载扩展参数应用，英文说明同步。
三只魔像应在长走道内有视线时射击，离开道路停止新射击；道路范围是区域参考
推算，尚未实机确认准确边缘/起点。Caligo HP补丁签名匹配与血条也尚待游戏验证。
传送离开雪山再返回；先看入场满红血条和HP补丁日志，再测60%转阶段、道路入口
三只加载/开火、桥外停止、死亡/重载/保存和六护符。
原T1共享AI/材质/系统/音频资源与未解决引用仍继承，未宣称其它地区无影响。
仅供当前私人内测；原Caligo移植资源再发布许可未确认，不上传公开GitHub。
Caligo原作者DDMMDD09：https://www.nexusmods.com/eldenring/mods/8583
HP上限签名/补丁：NymicRazor / Named-Blade, Endless Cycles (Infinite NG)
https://www.nexusmods.com/eldenring/mods/5732
六护符：imCioco / Expanded Talisman Slots 1.1.6
https://www.nexusmods.com/eldenring/mods/10481
'''

def main():
 p=argparse.ArgumentParser(description=__doc__); p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=True)
 original=load(a.inputs/next(iter(INPUTS)));prefix='Ascended_Balance_v0.10.14/'
 assert all(n.startswith(prefix) for n in original)
 original={n[len(prefix):]:b for n,b in original.items()}; assert len(original)==984
 with tempfile.TemporaryDirectory() as tmp:
  work=Path(tmp);core=dict(original); core['ModEngine/mod/regulation.bin'],core_audit=heal(core['ModEngine/mod/regulation.bin'],work,'core')
  for part in ['01','02']:
   n='ModEngine/mod/msg/engus/item_dlc'+part+'.msgbnd.dcx';core[n]=text(core[n])
  core['README.txt']=CORE_README.encode('utf-8-sig')
  allowed={'ModEngine/mod/regulation.bin','ModEngine/mod/msg/engus/item_dlc01.msgbnd.dcx','ModEngine/mod/msg/engus/item_dlc02.msgbnd.dcx','README.txt','SHA256_FILES.txt'}
  assert all(core[n]==b for n,b in original.items() if n not in allowed)
  private={}; provenance={}; discarded=[]
  for filename in list(INPUTS)[1:]:
   candidate=load(a.inputs/filename)
   for n,b in candidate.items():
    if n.startswith('ModEngine/expansions/') or n=='ModEngine/CaligoHpCapFix.dll':private[n]=b;provenance[n]=filename
    else:discarded.append({'source':filename,'file':n})
  reg='ModEngine/expansions/nightreign/caligo/regulation.bin';private[reg],private_audit=heal(private[reg],work,'caligo')
  msg='ModEngine/expansions/nightreign/caligo/msg/engus/item_dlc02.msgbnd.dcx';private[msg]=text(private[msg])
  profile='''profileVersion = "v1"
start_online = false
[[supports]]
game = "eldenring"
[[packages]]
id = "ascended_v0115"
path = 'mod'
[[packages]]
id = "caligo_v0115"
path = 'expansions/nightreign/caligo'
load_after = [{ id = "ascended_v0115", optional = false }]
[[natives]]
path = 'ExpandedTalismanSlots.dll'
[[natives]]
path = 'CaligoHpCapFix.dll'
optional = false
load_early = true
initializer = { function = "CaligoHpCapInitialize" }
'''
  cfg=tomllib.loads(profile);assert cfg['packages'][1]['load_after'][0]['id']==cfg['packages'][0]['id'];assert len(cfg['natives'])==2
  private['ModEngine/caligo_v0115.me3']=profile.encode()
  checks={n[len('ModEngine/'):].replace('/','\\'):sha(b) for n,b in private.items() if n.startswith('ModEngine/')}
  checks.update({n[len('ModEngine/'):].replace('/','\\'):sha(core[n]) for n in ['ModEngine/mod/regulation.bin','ModEngine/ExpandedTalismanSlots.dll','ModEngine/ExpandedTalismanSlots.ini']})
  ps="$ErrorActionPreference = 'Stop'\n$checks = @{\n"+''.join("    '"+n+"' = '"+v+"'\n" for n,v in sorted(checks.items()))+"}\nforeach ($rel in $checks.Keys) {\n $p = Join-Path $PSScriptRoot $rel\n if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw \"Missing file: $rel\" }\n if ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $checks[$rel]) { throw \"File mismatch: $rel. Use a clean v0.10.15 core plus complete new expansion.\" }\n}\nWrite-Host 'v0.10.15 core and Caligo expansion verified. Nominal HP 750000; phase 60%.'\n"
  private['ModEngine/check_caligo_v0115.ps1']=ps.encode()
  with zipfile.ZipFile(a.inputs/'Caligo_T3_Hotfix_04.zip') as z:bat=z.read('ModEngine/launch_caligo_hotfix04.bat').decode()
  bat=bat.replace('hotfix04','v0115').replace('HF04','v0.10.15')
  private['ModEngine/launch_caligo_v0115.bat']=bat.replace('\r\n','\n').replace('\n','\r\n').encode()
  private['README_CALIGO.txt']=PRIVATE_README.encode('utf-8-sig')
  core_report,core_manifest=package(core,a.output/'Ascended_Balance_v0.10.15_Integrated_Test.zip','Ascended_Balance_v0.10.15/')
  private_report,private_manifest=package(private,a.output/'Caligo_v0.10.15_Private_Expansion.zip','')
 report={'version':'v0.10.15','source_core_commit':'b11ae5f41478884401abb8a635fe66f28fb63d11','input_hashes':INPUTS,'core':core_report,'private_expansion':private_report,'core_unchanged_files':len(original)-len(allowed),'core_regeneration':core_audit,'private_regeneration':private_audit,'core_changed_paths':sorted(allowed),'extension_provenance':provenance,'obsolete_launchers_and_development_files_omitted':discarded,'game_test':'NOT RUN','public_release_scope':'Core only; Caligo assets private'}
 (a.output/'package_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 (a.output/'runtime_manifest.json').write_text(json.dumps({'core':core_manifest,'private':private_manifest},ensure_ascii=False,indent=2)+'\n')
 (a.output/'SHA256SUMS.txt').write_text(core_report['sha256']+'  '+core_report['filename']+'\n')
 (a.output/'CALIGO_SHA256SUMS.txt').write_text(private_report['sha256']+'  '+private_report['filename']+'\n')
 print(json.dumps({'core':core_report,'private':private_report,'game_test':'NOT RUN'}))
if __name__=='__main__':main()
