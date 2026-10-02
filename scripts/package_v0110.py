"""Package v0.10.10 using the verified runtime-only v0.10.9 archive."""
import argparse,hashlib,json,zipfile
from pathlib import Path
def sha(b):return hashlib.sha256(b).hexdigest()
INSTALL='''Ascended Balance v0.10.10 — 发布后改动整合测试版

备份存档，完整解压到全新目录，离线启动。ME3的mod目录指向ModEngine/mod。
Steam可用时沿用ModEngine/launchmod_eldenring.bat。不要混装旧版文件。
新增：基础记忆槽8个；近战强化阶梯；看门犬杖满属性满强化约5000物理AR；
吉萨刺轮约2800；大蛇矛攻击与属性补正不再随强化提高（仍可消耗强化材料）。
新职业双轻大剑/单翼架势、斗牛剑/平民服装，两者无初始骨灰，初始护符同步。
18件褪色者护甲补单件增益；莱昂提尔2～3件战技+10%、4件+20%，满套替换低档。
亚历山大碎片战技+40%，保留原有防御/异常效果；基础生命由原版2倍升至2.5倍。
普通床帘恩泽30分钟；盾牌油脂300,000秒；受击说明改为减轻受击硬直。
保留v0.10.9全部既有修复。英文说明已更新；中文JSON仅为仓库合并源。

静态检查通过，新增效果未游戏实测。新职业变化仅作用于新建角色。
先测试启动/读档/保存重载，再测强化材料与面板、职业男女出生、8槽、套装换装、
战技增伤、基础HP及道具持续时间；同时复测大盾、FP恢复、心脏与法术异常。
5000/2800是无外部增益的模型物理AR，不是实伤或最终上限。
校验运行文件见SHA256_FILES.txt；开发文档和审计仅在GitHub仓库。
https://github.com/TrasAsimov/ascended-balance-project
'''
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for f in ['base_zip','build','output']:p.add_argument('--'+f.replace('_','-'),type=Path,required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 assert sha(a.base_zip.read_bytes())=='188d077e816e79e906901f23654523801dafe77eda511b51d88e9e1d2d49dbbf'
 z=zipfile.ZipFile(a.base_zip);assert z.testzip() is None
 prefix='Ascended_Balance_v0.10.9/';files={n[len(prefix):]:z.read(n) for n in z.namelist() if not n.endswith('/')}
 assert len(files)==982 and all(n.startswith(prefix) for n in z.namelist())
 updates={'ModEngine/mod/regulation.bin':'regulation.bin','ModEngine/mod/event/common.emevd.dcx':'common.emevd.dcx',**{f'ModEngine/mod/msg/engus/item_dlc{s}.msgbnd.dcx':f'item_dlc{s}.msgbnd.dcx' for s in ['01','02']}}
 changed=[]
 for path,n in updates.items():
  blob=(a.build/n).read_bytes();assert blob!=files[path];files[path]=blob;changed.append(path)
 unchanged=[n for n in files if n not in changed+['README.txt','SHA256_FILES.txt']]
 assert len(unchanged)==976
 files['README.txt']=INSTALL.encode('utf-8-sig');files.pop('SHA256_FILES.txt')
 listing={n:{'bytes':len(b),'sha256':sha(b)} for n,b in sorted(files.items())}
 files['SHA256_FILES.txt']=''.join(v['sha256']+'  '+n+'\n' for n,v in listing.items()).encode()
 dest=a.output/'Ascended_Balance_v0.10.10_Post_Release_Integration.zip'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
  for n,b in sorted(files.items()):out.writestr('Ascended_Balance_v0.10.10/'+n,b)
 with zipfile.ZipFile(dest) as check:
  assert len(check.namelist())==len(set(check.namelist()))==982;assert check.testzip() is None
  for n,b in files.items():assert check.read('Ascended_Balance_v0.10.10/'+n)==b
 assert [n for n in files if n.endswith('regulation.bin')]==['ModEngine/mod/regulation.bin']
 checksum=sha(dest.read_bytes());(a.output/'SHA256SUMS.txt').write_text(checksum+'  '+dest.name+'\n')
 audit={'version':'v0.10.10','zip_name':dest.name,'bytes':dest.stat().st_size,'sha256':checksum,'file_count':len(files),'unchanged_runtime_files':len(unchanged),'changed_runtime_files':changed,'CRC_readback_internal_hashes':'passed','files':listing,'game_validation':'not run'}
 (a.output/'package_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in audit.items() if k!='files'}))
if __name__=='__main__':main()
