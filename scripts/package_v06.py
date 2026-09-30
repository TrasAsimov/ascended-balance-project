"""Build a complete v0.6 test archive from the verified v0.5 release."""
from pathlib import Path
import copy
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT.parent / 'recovered/Ascended_优化版_v0.5_待测试包.zip'
REG = ROOT / 'output/v06_regulation.bin'
NOTES = ROOT / 'docs/v0.6.md'
OUT = ROOT / 'output/Ascended_Balance_v0.6_Test.zip'
PREFIX = 'Elden_Ascended_Mod_Age of the Endless Mod/'
TARGETS = {PREFIX + 'regulation.bin', PREFIX + 'ModEngine/mod/regulation.bin'}


def main():
    assert BASE.exists() and REG.exists() and NOTES.exists()
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(BASE) as source, zipfile.ZipFile(OUT, 'w') as target:
        assert source.testzip() is None
        assert TARGETS <= set(source.namelist())
        for info in source.infolist():
            if info.filename.endswith('Ascended_v0.5_安装与测试说明.md'):
                continue
            data = REG.read_bytes() if info.filename in TARGETS else source.read(info)
            target.writestr(copy.copy(info), data)
        target.write(NOTES, PREFIX + 'Ascended_v0.6_安装与测试说明.md')
    with zipfile.ZipFile(OUT) as check:
        assert check.testzip() is None
        assert all(check.read(name) == REG.read_bytes() for name in TARGETS)
    print(OUT, OUT.stat().st_size, hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
