"""Unpack an already decrypted BND4/DCX or an Ascended-era regulation.bin.

Official 1.17.1 encrypted regulation.bin uses a different key from Ascended
1.16 and must first be decrypted with a version-compatible game tool.
"""
from pathlib import Path
import sys
import io
import struct

import zstandard as zstd

from build_v03 import decrypt


def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: unpack_regulation.py INPUT.bnd-or-dcx OUTPUT.bnd')
    source, destination = map(Path, sys.argv[1:])
    blob = source.read_bytes()
    if blob[:4] == b'BND4':
        raw = blob
    elif blob[:4] == b'DCX\0' and blob[0x28:0x2c] == b'ZSTD':
        expected, compressed = struct.unpack_from('>II', blob, 0x1c)
        assert 0x4c + compressed <= len(blob) <= 0x4c + compressed + 32
        with zstd.ZstdDecompressor().stream_reader(io.BytesIO(blob[0x4c:0x4c+compressed])) as reader:
            raw = reader.read()
        assert len(raw) == expected and raw[:4] == b'BND4'
    else:
        try:
            _, raw = decrypt(blob)
        except Exception as exc:
            raise SystemExit('无法解密；1.17.1 官方加密 regulation.bin 请先用兼容工具解密成 DCX 或 BND4。') from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    print(f'{destination}: {len(raw)} bytes')


if __name__ == '__main__':
    main()
