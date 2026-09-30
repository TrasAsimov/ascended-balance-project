"""Build the latest integrated test snapshot from the last complete ZIP."""
from pathlib import Path
import copy
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'output/Ascended_Balance_v0.9.2_Partial_Test.zip'
OUT = ROOT / 'output/Ascended_Balance_v0.10_Integrated_Test.zip'
PREFIX = 'Elden_Ascended_Mod_Age of the Endless Mod/'
REPLACE = {
    PREFIX + 'regulation.bin': ROOT / 'output/pending_spell_boss_bonus_regulation.bin',
    PREFIX + 'ModEngine/mod/regulation.bin': ROOT / 'output/pending_spell_boss_bonus_regulation.bin',
    PREFIX + 'ModEngine/mod/event/common.emevd.dcx': ROOT / 'work/pending_common.emevd.dcx',
    **{PREFIX + 'ModEngine/mod/msg/engus/' + s + '.msgbnd.dcx':
       ROOT / 'output/pending_remembrance_text' / (s + '.msgbnd.dcx')
       for s in ('item_dlc01', 'item_dlc02')},
}
OLD_DOC = PREFIX + 'Ascended_v0.9.2_部分成果安装与测试说明.md'
NEW_DOC = PREFIX + 'Ascended_v0.10_集成测试说明.md'
REPORTS = {
    PREFIX + '审查清单/v0.5_至今有效改动.md': ROOT / 'docs/from_v05_to_current.md',
    PREFIX + '审查清单/官方原版_当前参数对比.md': ROOT / 'docs/vanilla_to_current.md',
}

def main():
    assert all(p.exists() for p in (BASE, *REPLACE.values(), *REPORTS.values(), ROOT/'docs/v0.10.md'))
    with zipfile.ZipFile(BASE) as src, zipfile.ZipFile(OUT, 'w') as dst:
        assert src.testzip() is None
        assert set(REPLACE) | {OLD_DOC} <= set(src.namelist())
        for info in src.infolist():
            if info.filename == OLD_DOC:
                continue
            dst.writestr(copy.copy(info), REPLACE[info.filename].read_bytes()
                         if info.filename in REPLACE else src.read(info))
        dst.write(ROOT/'docs/v0.10.md', NEW_DOC)
        for target, source in REPORTS.items():
            dst.write(source, target)
    with zipfile.ZipFile(OUT) as check, zipfile.ZipFile(BASE) as original:
        assert check.testzip() is None
        assert set(check.namelist()) == (set(original.namelist())-{OLD_DOC}) | {NEW_DOC} | set(REPORTS)
        for name, path in REPLACE.items():
            assert check.read(name) == path.read_bytes(), name
        for info in original.infolist():
            if info.filename not in REPLACE and info.filename != OLD_DOC:
                assert check.read(info.filename) == original.read(info), info.filename
    print(OUT, OUT.stat().st_size, hashlib.sha256(OUT.read_bytes()).hexdigest())

if __name__ == '__main__':
    main()
