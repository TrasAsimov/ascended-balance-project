"""Build the authorized six-talisman test release on the exact v0.10.13 runtime."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from integrate_six_talismans import integrate


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


INSTALL = '''Ascended Balance v0.10.14 — 六护符测试版

备份存档，完整解压到全新目录，离线启动，不混装旧版。
Steam可用时运行ModEngine/launchmod_eldenring.bat；包内ME2已登记DLL。
总六护符＝原生四槽＋额外两槽。额外槽在赐福的Expanded Talisman Slots
菜单装备；普通装备界面仍显示原生四槽。必须拥有实际护符。
ExpandedTalismanSlots.ini的slots=2表示增加两槽，不要改为6。

原生ME3用户：mod目录指向ModEngine/mod，并在实际profile的[[natives]]
登记ModEngine/ExpandedTalismanSlots.dll的真实路径；DLL与INI保持同目录。
仅设置mod目录不会加载DLL；同一次启动不要重复登记该DLL。

完整保留v0.10.13参数、事件、动作及游戏文本：新职业小战士壶碎片战技+40%、
心脏181场首领计数修复、十种自选护符、基础HP×2.5、近战强化、记忆槽8个、
莱昂提尔2～3件全战技+10%／4件+20%、护甲单件、床帘30分钟及既有修复。
职业配装只影响新建角色；心脏重复使用只刷新，死亡／重载后再次使用。

静态检查与打包读回通过，尚未游戏实测。
先测启动、读档、保存重载；再测赐福总六槽、不能装备第七个、第五／第六
护符效果与卸装解除、同族互斥、背包与重量、传送／死亡／退出重载／换角色。
同时回归套装战技、小壶、心脏与高跳。中文JSON仅为仓库合并源。

感谢imCioco：Expanded Talisman Slots 1.1.6（DLL原样保留，用户已取得集成同意）。
https://www.nexusmods.com/eldenring/mods/10481
SHA256_FILES.txt校验内部文件；Release SHA256SUMS.txt校验整包。
需本体与全部DLC。源码、开发记录及审计留在GitHub，不进入玩家ZIP。
https://github.com/TrasAsimov/ascended-balance-project
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('base-zip', 'upstream-zip', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    assert sha(a.base_zip.read_bytes()) == '826a740219061fd853f9ff35b0caa7944cec97dbb536cb2239cf3de86f79775e'
    prefix = 'Ascended_Balance_v0.10.13/'
    with zipfile.ZipFile(a.base_zip) as source:
        assert source.testzip() is None
        assert len(source.namelist()) == len(set(source.namelist()))
        assert all(n.startswith(prefix) for n in source.namelist())
        original = {n[len(prefix):]: source.read(n) for n in source.namelist() if not n.endswith('/')}
    assert len(original) == 982
    updates, integration = integrate(original, a.upstream_zip.read_bytes())
    integration.pop('package_generated')
    files = dict(original, **updates)
    files['README.txt'] = INSTALL.encode('utf-8-sig')
    files.pop('SHA256_FILES.txt')
    listing = {n: {'bytes': len(b), 'sha256': sha(b)} for n, b in sorted(files.items())}
    files['SHA256_FILES.txt'] = ''.join(v['sha256']+'  '+n+'\n' for n, v in listing.items()).encode()
    replaced = {'ModEngine/config_eldenring.toml', 'README.txt', 'SHA256_FILES.txt'}
    unchanged = [n for n in original if n not in replaced]
    assert len(unchanged) == 979
    assert all(original[n] == files[n] for n in unchanged)
    assert len(files) == 984
    assert not any(n.endswith(('.patch', '.csv', '.json', '.js', '.temp', '.log', '.zip')) for n in files)
    a.output.mkdir(parents=True, exist_ok=True)
    destination = a.output/'Ascended_Balance_v0.10.14_Six_Talismans_Test.zip'
    final_prefix = 'Ascended_Balance_v0.10.14/'
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as result:
        for n, b in sorted(files.items()):
            info = zipfile.ZipInfo(final_prefix+n, date_time=(2026, 10, 3, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            result.writestr(info, b, compresslevel=6)
    with zipfile.ZipFile(destination) as check:
        assert check.testzip() is None
        assert len(check.namelist()) == len(set(check.namelist())) == 984
        for n, b in files.items():
            assert check.read(final_prefix+n) == b
        for line in check.read(final_prefix+'SHA256_FILES.txt').decode().splitlines():
            digest, name = line.split('  ', 1)
            assert sha(check.read(final_prefix+name)) == digest
    checksum = sha(destination.read_bytes())
    (a.output/'SHA256SUMS.txt').write_text(checksum+'  '+destination.name+'\n')
    report = {'version': 'v0.10.14', 'release_tag': 'v0.10.14-six-talismans',
              'zip_name': destination.name, 'bytes': destination.stat().st_size,
              'sha256': checksum, 'package_generated': True, 'file_count': len(files),
              'unchanged_existing_files': len(unchanged),
              'replaced_existing_files': sorted(replaced),
              'added_files': sorted(set(files)-set(original)),
              'CRC_readback_internal_hashes': 'passed',
              'integration': integration, 'game_validation': 'not run'}
    (a.output/'package_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
