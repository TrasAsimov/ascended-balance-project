"""Package the Windows-compiled permanent-night event from the user's return."""
from pathlib import Path
import hashlib
import struct
import zipfile

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'output/Ascended_Balance_v0.10.2_Riposte_Test.zip'
EVENT=ROOT.parent/'upload/common.emevd(3).dcx'
OUT=ROOT/'output/Ascended_Balance_v0.10.3_Night_Test.zip'
DOC=ROOT/'docs/v0.10.3.md'
PREFIX='Elden_Ascended_Mod_Age of the Endless Mod/'
TARGET=PREFIX+'ModEngine/mod/event/common.emevd.dcx'
EXPECTED_EVENT_SHA='70fd6169295eada02d972e08b1384ee8322031197057649d0cf5e032f452516e'

def main():
    new=EVENT.read_bytes()
    assert hashlib.sha256(new).hexdigest()==EXPECTED_EVENT_SHA
    assert new[:4]==b'DCX\0' and new[0x28:0x2c]==b'KRAK'
    expected,packed=struct.unpack_from('>II',new,0x1c)
    assert expected==402512 and 0x4c+packed<=len(new)<=0x4c+packed+15
    assert DOC.exists()
    with zipfile.ZipFile(BASE) as src,zipfile.ZipFile(OUT,'w') as dst:
        assert src.testzip() is None and TARGET in src.namelist()
        for info in src.infolist():
            dst.writestr(info,new if info.filename==TARGET else src.read(info))
        dst.write(DOC,PREFIX+'Ascended_v0.10.3_永夜测试说明.md')
    with zipfile.ZipFile(BASE) as src,zipfile.ZipFile(OUT) as dst:
        assert dst.testzip() is None
        assert set(dst.namelist())==set(src.namelist())|{PREFIX+'Ascended_v0.10.3_永夜测试说明.md'}
        for name in src.namelist():
            assert dst.read(name)==(new if name==TARGET else src.read(name)),name
    print(OUT,OUT.stat().st_size,hashlib.sha256(OUT.read_bytes()).hexdigest())

if __name__=='__main__':main()
