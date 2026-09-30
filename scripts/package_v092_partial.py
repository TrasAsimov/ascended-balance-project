"""Package finished parameter/text changes without the uncompiled event draft."""
from pathlib import Path
import copy
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'output/Ascended_Balance_v0.9.1_Test.zip'
REG = ROOT / 'output/pending_torrent_regulation.bin'
DOC = ROOT / 'docs/v0.9.2-partial.md'
TEXT = ROOT / 'output/pending_remembrance_text'
OUT = ROOT / 'output/Ascended_Balance_v0.9.2_Partial_Test.zip'
P = 'Elden_Ascended_Mod_Age of the Endless Mod/'
REGS = {P+'regulation.bin', P+'ModEngine/mod/regulation.bin'}
MSGS = {P+'ModEngine/mod/msg/engus/'+v+'.msgbnd.dcx': TEXT/(v+'.msgbnd.dcx')
        for v in ('item_dlc01', 'item_dlc02')}
OLD_DOC = P+'Ascended_v0.9.1_安装与测试说明.md'
NEW_DOC = P+'Ascended_v0.9.2_部分成果安装与测试说明.md'
CHANGE = P+'审查清单/pending_remembrance_params.csv'

def main():
    assert all(x.exists() for x in (BASE, REG, DOC, *MSGS.values()))
    with zipfile.ZipFile(BASE) as src, zipfile.ZipFile(OUT, 'w') as dest:
        assert src.testzip() is None
        assert REGS | MSGS.keys() | {OLD_DOC} <= set(src.namelist())
        for info in src.infolist():
            if info.filename == OLD_DOC:
                continue
            data = (REG.read_bytes() if info.filename in REGS else
                    MSGS[info.filename].read_bytes() if info.filename in MSGS else
                    src.read(info))
            dest.writestr(copy.copy(info), data)
        dest.write(DOC, NEW_DOC)
        dest.write(ROOT/'changes/pending_remembrance_params.csv', CHANGE)
    with zipfile.ZipFile(BASE) as before, zipfile.ZipFile(OUT) as after:
        assert after.testzip() is None
        assert set(after.namelist()) == (set(before.namelist())-{OLD_DOC}) | {NEW_DOC, CHANGE}
        for name in set(before.namelist()) - {OLD_DOC} - REGS - MSGS.keys():
            assert before.read(name) == after.read(name), name
        assert all(after.read(name) == REG.read_bytes() for name in REGS)
        assert all(after.read(dst) == src.read_bytes() for dst, src in MSGS.items())
        assert not any('pending_common' in name for name in after.namelist())
    print(OUT, OUT.stat().st_size, hashlib.sha256(OUT.read_bytes()).hexdigest())

if __name__ == '__main__':
    main()
