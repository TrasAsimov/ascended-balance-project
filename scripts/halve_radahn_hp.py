"""Apply once, or verify again, on the latest merged ER regulation; no package creation."""
import argparse, hashlib, json, os, struct, zlib
from pathlib import Path
import zstandard
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

TARGETS = {1643002: (-80, -40), 1643102: (-120, -60), 1685001: (-50, -25)}

def sha(b): return hashlib.sha256(b).hexdigest()

def unpack(blob, key):
    d = Cipher(algorithms.AES(key), modes.CBC(blob[:16])).decryptor()
    plain = d.update(blob[16:]) + d.finalize()
    assert plain[:4] == b'DCX\0'
    size, cs = struct.unpack_from('>II', plain, 28)
    codec = plain[40:44]
    if codec == b'ZSTD': raw = zstandard.ZstdDecompressor().decompress(plain[76:76+cs], max_output_size=size)
    elif codec == b'DFLT': raw = zlib.decompress(plain[76:76+cs])
    else: raise ValueError('Unsupported compression')
    assert len(raw) == size and raw[:4] == b'BND4'
    return plain[:76], raw

def locate(raw):
    for i in range(struct.unpack_from('<I', raw, 12)[0]):
        h = 64 + 36*i
        _, _, size, _, off, _, noff = struct.unpack_from('<IIQQIII', raw, h)
        end = noff
        while raw[end:end+2] != b'\0\0': end += 2
        if raw[noff:end].decode('utf-16le').split('\\')[-1] == 'SpEffectParam.param': return off, size
    raise ValueError('Missing SpEffectParam')

def run(source, output, key):
    blob = Path(source).read_bytes()
    header, raw = unpack(blob, key)
    base, size = locate(raw)
    p = raw[base:base+size]
    assert p[0x2d] & 0x84 == 0x84
    rows = {}
    for i in range(struct.unpack_from('<H', p, 10)[0]):
        rid, _, off, _ = struct.unpack_from('<iIQQ', p, 64+24*i)
        rows[rid] = off
    out = bytearray(raw)
    changes = []
    allowed = set()
    for rid, (old, new) in TARGETS.items():
        pos = base + rows[rid] + 160
        value = struct.unpack_from('<i', raw, pos)[0]
        assert value in (old, new), (rid, value)
        assert struct.unpack_from('<f', raw, base+rows[rid]+12)[0] == 1.0
        struct.pack_into('<i', out, pos, new)
        allowed.update(range(pos, pos+4))
        changes.append({'id':rid, 'field':'changeHpPoint', 'before':value, 'after':new, 'interval_seconds':1})
    assert all(i in allowed for i,(a,b) in enumerate(zip(raw,out)) if a != b)
    assert struct.unpack_from('<i', out, base+rows[501291]+168)[0] == -5
    if out == raw: result = blob
    else:
        compressed = zstandard.ZstdCompressor(level=15).compress(out) if header[40:44] == b'ZSTD' else zlib.compress(out,9)
        h = bytearray(header); struct.pack_into('>II', h, 28, len(out), len(compressed))
        pad = PKCS7(128).padder(); payload = pad.update(bytes(h)+compressed)+pad.finalize()
        iv = os.urandom(16); enc = Cipher(algorithms.AES(key),modes.CBC(iv)).encryptor()
        result = iv+enc.update(payload)+enc.finalize()
    assert unpack(result,key)[1] == bytes(out)
    Path(output).write_bytes(result)
    return {'source_sha256':sha(blob), 'output_sha256':sha(result), 'changes':changes, 'fp_per_second':5, 'all_other_decrypted_bytes_preserved':True, 'encrypted_readback':'passed', 'game_test':'not run'}

if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('source'); a.add_argument('output'); a.add_argument('--audit',required=True)
    args = a.parse_args()
    audit = run(args.source,args.output,bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX']))
    Path(args.audit).write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
