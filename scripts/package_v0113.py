"""Package verified starter/heart fixes on the runtime-only v0.10.12 ZIP."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


INSTALL = '''Ascended Balance v0.10.13 — 新职业护符与心脏奖励修复

备份存档，完整解压到全新目录，离线启动，不混装旧版。
ME3的mod目录指向ModEngine/mod；Steam可用时运行ModEngine/launchmod_eldenring.bat。

两个新职业固定携带小战士壶碎片，沿用战技伤害+40%；男女预览同步。
轻职业仍为双轻大剑/单翼架势/翼剑徽章；重职业仍为斗牛剑/平民服装。
职业配装只影响新建角色；无初始骨灰和返回赐福道具，自选护符保留。

Empowered Soul心脏小首领计数修复，改用已分配旗标。
登记181场首领战（本体150/DLC31）：每场HP/FP/精力上限各+0.2%，
武器攻击力及魔法/祷告伤害各+0.1%，本组加算；同场多名首领计一场。
21组普通追忆及贝勒保留独立奖励，四种特殊追忆保留各自效果。
本周目已击败的登记首领可以直接计入；使用后刷新，不重复叠加、不消耗。
死亡/重载后再次使用。单场提升很小，整数面板可能暂时没有显示变化。
英文心脏说明写明范围、数值、计数和刷新规则。

保留v0.10.12全部其它改动：8槽、十种自选护符、基础HP×2.5、近战强化、
莱昂提尔10/20%战技套装、护甲单件、床帘30分钟、盾牌油脂300000秒及既有修复。
静态/事件模拟检查通过，未游戏实测。中文JSON仅为仓库合并源。
先验证启动/读档/保存重载，再测新职业男女护符、心脏使用前后资源及同招伤害，
重复使用、继续击败野外/地牢首领、死亡重载，以及原追忆/贝勒奖励。

SHA256_FILES.txt校验内部文件；Release SHA256SUMS.txt校验整包。
源码、开发记录和审计留在GitHub，不进入玩家ZIP。需本体与全部DLC。
https://github.com/TrasAsimov/ascended-balance-project
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('base-zip','build','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    assert sha(a.base_zip.read_bytes()) == 'cb66fb46977c51741847acd4f3bf75fe2ee0ec7f74ac009f492a740dadadcd1a'
    prefix = 'Ascended_Balance_v0.10.12/'
    with zipfile.ZipFile(a.base_zip) as source:
        assert source.testzip() is None
        assert all(n.startswith(prefix) for n in source.namelist())
        files = {n[len(prefix):]:source.read(n) for n in source.namelist() if not n.endswith('/')}
    assert len(files) == 982
    updates = {
        'ModEngine/mod/regulation.bin':'regulation.bin',
        'ModEngine/mod/event/common.emevd.dcx':'common.emevd.dcx',
        'ModEngine/mod/msg/engus/item_dlc01.msgbnd.dcx':'engus_item_dlc01.msgbnd.dcx',
        'ModEngine/mod/msg/engus/item_dlc02.msgbnd.dcx':'engus_item_dlc02.msgbnd.dcx'}
    changed = []
    for name, local in updates.items():
        blob = (a.build/local).read_bytes()
        assert blob != files[name]
        files[name] = blob
        changed.append(name)
    unchanged = [n for n in files if n not in changed+['README.txt','SHA256_FILES.txt']]
    assert len(unchanged) == 976
    files['README.txt'] = INSTALL.encode('utf-8-sig')
    files.pop('SHA256_FILES.txt')
    listing = {n:{'bytes':len(b),'sha256':sha(b)} for n,b in sorted(files.items())}
    files['SHA256_FILES.txt'] = ''.join(v['sha256']+'  '+n+'\n' for n,v in listing.items()).encode()
    assert [n for n in files if n.endswith('regulation.bin')] == ['ModEngine/mod/regulation.bin']
    assert not any(n.endswith(('.patch','.csv','.json','.js','.temp','.log','.zip')) for n in files)
    destination = a.output/'Ascended_Balance_v0.10.13_Starter_Heart_Fix.zip'
    final_prefix = 'Ascended_Balance_v0.10.13/'
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as result:
        for n,b in sorted(files.items()):
            result.writestr(final_prefix+n,b)
    with zipfile.ZipFile(destination) as check:
        assert check.testzip() is None
        assert len(check.namelist()) == len(set(check.namelist())) == 982
        for n,b in files.items():
            assert check.read(final_prefix+n) == b
        for line in check.read(final_prefix+'SHA256_FILES.txt').decode().splitlines():
            digest,name = line.split('  ',1)
            assert sha(check.read(final_prefix+name)) == digest
    checksum = sha(destination.read_bytes())
    (a.output/'SHA256SUMS.txt').write_text(checksum+'  '+destination.name+'\n')
    report = {'version':'v0.10.13','zip_name':destination.name,
        'bytes':destination.stat().st_size,'sha256':checksum,'file_count':982,
        'unchanged_runtime_files':len(unchanged),'changed_runtime_files':changed,
        'CRC_readback_internal_hashes':'passed','files':listing,'game_validation':'not run'}
    (a.output/'package_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'files'}))


if __name__ == '__main__':
    main()
