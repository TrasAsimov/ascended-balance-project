"""Package reconciled PARAMs and English text as a test candidate."""

from __future__ import annotations

import copy
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT/'inputs/Ascended_优化版_v0.4_1.17.1兼容测试包.zip'
PARAM = ROOT/'output/v05_reconciled_regulation.bin'
TEXT = ROOT/'output/v05_text'
PREFIX = 'Elden_Ascended_Mod_Age of the Endless Mod/'
OUT = ROOT/'output/Ascended_优化版_v0.5_待测试包.zip'
NOTES = ROOT/'docs/v0.5.md'
ITEM_TEXT = {PREFIX+'ModEngine/mod/msg/engus/'+n+'.msgbnd.dcx':
             TEXT/(n+'.msgbnd.dcx') for n in ('item_dlc01','item_dlc02')}
MENU_TEXT = {PREFIX+'ModEngine/mod/msg/engus/'+n+'.msgbnd.dcx':
             TEXT/(n+'.msgbnd.dcx') for n in ('menu','menu_dlc01','menu_dlc02')}
REGULATION_PATHS = {
    PREFIX+'ModEngine/mod/regulation.bin',
    PREFIX+'regulation.bin',
}


def main():
    assert SOURCE.exists() and PARAM.exists() and NOTES.exists() and all(p.exists() for p in (*ITEM_TEXT.values(),*MENU_TEXT.values()))
    with zipfile.ZipFile(SOURCE) as source, zipfile.ZipFile(OUT,'w') as out:
        assert source.testzip() is None
        names = set(source.namelist())
        assert set(ITEM_TEXT) <= names and REGULATION_PATHS <= names
        for info in source.infolist():
            if info.filename.endswith('Ascended_优化版_v0.4_测试说明.md'):
                continue
            data = (PARAM.read_bytes() if info.filename in REGULATION_PATHS
                    else ITEM_TEXT[info.filename].read_bytes() if info.filename in ITEM_TEXT
                    else source.read(info))
            out.writestr(copy.copy(info),data)
        for name,path in MENU_TEXT.items():
            assert name not in names
            out.write(path,name)
        out.write(NOTES,PREFIX+'Ascended_v0.5_安装与测试说明.md')
    assert zipfile.ZipFile(OUT).testzip() is None
    print(OUT)


if __name__ == '__main__':
    main()
