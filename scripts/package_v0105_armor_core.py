"""Package validated armor/core handoff over the exact v0.10.4 complete release."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'output/Ascended_Balance_v0.10.4_Jump_Integrated.zip'
OUT = ROOT / 'output/Ascended_Balance_v0.10.5_Armor_Core_Integrated.zip'
PREFIX = 'Elden_Ascended_Mod_Age of the Endless Mod/'
BASE_SHA = '007b4f0b8dff4d6bab6ad7bcec25ba28386df839c9f589849df23efcfad70136'
HANDOFF = ROOT / 'inputs/handoff'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    assert sha(BASE.read_bytes()) == BASE_SHA, 'Invalid base package'
    approved = json.loads((ROOT / 'changes/armor_core_integration_20261001.json').read_text())
    replacements = {}
    for path, expected in approved['output_files'].items():
        name = path.rsplit('/', 1)[-1]
        if '/engus/' in path:
            name = 'engus_' + name
        data = (HANDOFF / ('Armor_Core_20261001_' + name)).read_bytes()
        assert sha(data) == expected, path
        replacements[PREFIX + path] = data
    extras = {
        PREFIX + 'Ascended_v0.10.5_安装与测试说明.md': (ROOT / 'docs/v0.10.5.md').read_bytes(),
        PREFIX + 'Armor_Core/armor_core_integration_20261001.md': (ROOT / 'docs/armor_core_integration_20261001.md').read_bytes(),
        PREFIX + 'Armor_Core/description_zh.json': (HANDOFF / 'Armor_Core_20261001_description_zh.json').read_bytes(),
        PREFIX + 'Armor_Core/integration_manifest.json': (ROOT / 'changes/armor_core_integration_20261001.json').read_bytes(),
        PREFIX + 'README.md': (ROOT / 'README.md').read_bytes(),
        PREFIX + 'README.zh-CN.md': (ROOT / 'README.zh-CN.md').read_bytes(),
        PREFIX + 'CHANGELOG.md': (ROOT / 'CHANGELOG.md').read_bytes(),
    }
    with zipfile.ZipFile(BASE) as src, zipfile.ZipFile(OUT, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as dst:
        names = src.namelist()
        assert len(names) == len(set(names))
        assert src.testzip() is None
        assert set(replacements) <= set(names)
        assert not set(extras) & set(names)
        for info in src.infolist():
            dst.writestr(info, replacements.get(info.filename, src.read(info)))
        for name, data in extras.items():
            dst.writestr(name, data)
    with zipfile.ZipFile(BASE) as src, zipfile.ZipFile(OUT) as dst:
        assert dst.testzip() is None
        assert len(dst.namelist()) == len(set(dst.namelist()))
        assert set(dst.namelist()) == set(src.namelist()) | set(extras)
        for name in src.namelist():
            assert dst.read(name) == replacements.get(name, src.read(name)), name
        for name, data in extras.items():
            assert dst.read(name) == data
        hks = PREFIX + 'ModEngine/mod/action/script/c0000.hks'
        assert sha(dst.read(hks)) == '30b1a2d3bb683169feff55c79528dbe2bb3cb96a58cca5c05d9cdb3a1e60d3d3'
        manifest = {'version': 'v0.10.5', 'base_sha256': BASE_SHA,
                    'source_implementation_commit': 'ee2419f13dec848c0a8d648edc95e759fa44346d',
                    'package': OUT.name, 'package_sha256': sha(OUT.read_bytes()),
                    'package_size': OUT.stat().st_size, 'package_members': len(dst.namelist()),
                    'replaced_files': approved['output_files'], 'added_files': [n.removeprefix(PREFIX) for n in extras],
                    'unchanged_base_members': len(src.namelist()) - len(replacements),
                    'zip_crc': 'passed', 'all_inherited_bytes': 'passed', 'game_test': 'not run'}
    (ROOT / 'changes/v0.10.5_package_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    (OUT.parent / 'SHA256SUMS.txt').write_text(manifest['package_sha256'] + '  ' + OUT.name + '\n')
    print(json.dumps(manifest, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
