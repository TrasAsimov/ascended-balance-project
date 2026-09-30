"""Integrate the user's verified current-game jump HKS into the full v0.10.3 build."""
from pathlib import Path
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "output/Ascended_Balance_v0.10.3_Night_Test.zip"
HKS = ROOT / "output/jump_patch/ModEngine/mod/action/script/c0000.hks"
DOC = ROOT / "docs/v0.10.4.md"
OUT = ROOT / "output/Ascended_Balance_v0.10.4_Jump_Integrated.zip"
PREFIX = "Elden_Ascended_Mod_Age of the Endless Mod/"
TARGET = PREFIX + "ModEngine/mod/action/script/c0000.hks"
DOC_TARGET = PREFIX + "Ascended_v0.10.4_高跳整合说明.md"
EXPECTED_HKS_SHA = "30b1a2d3bb683169feff55c79528dbe2bb3cb96a58cca5c05d9cdb3a1e60d3d3"


def main():
    script = HKS.read_bytes()
    assert hashlib.sha256(script).hexdigest() == EXPECTED_HKS_SHA
    assert script.count(b"function Act_Jump()") == 1
    assert script.count(b"act(2001, 1.4)") == 1
    with zipfile.ZipFile(BASE) as src, zipfile.ZipFile(OUT, "w") as dst:
        assert src.testzip() is None and TARGET not in src.namelist()
        assert PREFIX + "ModEngine/mod/chr/c0000.anibnd.dcx" not in src.namelist()
        for info in src.infolist():
            dst.writestr(info, src.read(info))
        dst.write(HKS, TARGET, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        dst.write(DOC, DOC_TARGET, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(BASE) as src, zipfile.ZipFile(OUT) as dst:
        assert dst.testzip() is None
        assert set(dst.namelist()) == set(src.namelist()) | {TARGET, DOC_TARGET}
        for name in src.namelist():
            assert src.getinfo(name).CRC == dst.getinfo(name).CRC, name
            assert src.getinfo(name).file_size == dst.getinfo(name).file_size, name
        assert dst.read(TARGET) == script
    print(OUT, OUT.stat().st_size, hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
