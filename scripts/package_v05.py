"""Package a staged v0.5 candidate after all player feedback is integrated.

Do not run/publish this until missing class menu text has been resolved and
the user asks for the next test package.
"""

from __future__ import annotations

import copy
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT/'inputs/Ascended_优化版_v0.4_1.17.1兼容测试包.zip'
PARAM = ROOT/'output/v05_pending_text_regulation.bin'
PREFIX = 'Elden_Ascended_Mod_Age of the Endless Mod/'
OUT = ROOT/'output/Ascended_优化版_v0.5_待测试包.zip'
STALE_ENGLISH_TEXT = {
    PREFIX+'ModEngine/mod/msg/engus/item_dlc01.msgbnd.dcx',
    PREFIX+'ModEngine/mod/msg/engus/item_dlc02.msgbnd.dcx',
}
REGULATION_PATHS = {
    PREFIX+'ModEngine/mod/regulation.bin',
    PREFIX+'regulation.bin',
}


def main():
    assert SOURCE.exists() and PARAM.exists()
    with zipfile.ZipFile(SOURCE) as source, zipfile.ZipFile(OUT,'w') as out:
        assert source.testzip() is None
        names = set(source.namelist())
        assert STALE_ENGLISH_TEXT <= names and REGULATION_PATHS <= names
        for info in source.infolist():
            if info.filename in STALE_ENGLISH_TEXT:
                continue
            data = PARAM.read_bytes() if info.filename in REGULATION_PATHS else source.read(info)
            out.writestr(copy.copy(info),data)
    assert zipfile.ZipFile(OUT).testzip() is None
    print(OUT)


if __name__ == '__main__':
    main()
