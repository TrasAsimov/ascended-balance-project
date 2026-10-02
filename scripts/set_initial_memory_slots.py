"""Set shared player base spell/incantation memory slots to eight.

Requires matching ARMOR_PARAMDEFS and ARMOR_REGULATION_KEY_HEX. Does not
edit saves, starting equipment, Memory Stones, spells, talismans or UI.
"""
import argparse
import json
import os
from pathlib import Path
import struct
import sys
import zstandard as zstd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from disable_player_debuffs import sha, unpack
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'systems/armor/scripts'))
from analyze_regulation import read_param
from field_diff import defs, fields, decode
from formats import bnd_entries, bnd_repack, param_patch
from verify_layout import directory


def patch(raw):
    parts = bnd_entries(raw)
    assert len(parts) == 194
    name = 'PlayerCommonParam.param'
    original = parts[name][1]
    table = read_param(original, 'PlayerCommonParam')
    fs, size = fields(defs()[table['ptype']])
    assert size == 256
    before_dir, before_end = directory(original, size)
    fs = {f[0]: f for f in fs}
    f = fs['baseMagicSlotSize']
    assert f[1] == 'u8' and f[4] is None and f[3] == f[6] == 1
    row = before_dir[0][3]
    body = bytearray(row)
    body[f[2]] = 8
    updated = param_patch(original, {0: bytes(body)}, {}, size)
    expected = bytearray(original)
    count = struct.unpack_from('<H', original, 10)[0]
    record = next(struct.unpack_from('<iIQQ', original, 64+24*i)
                  for i in range(count) if struct.unpack_from('<i', original, 64+24*i)[0] == 0)
    expected[record[2]+f[2]] = 8
    assert updated == expected, 'Non-target PARAM bytes changed'
    output = bnd_repack(raw, {name: updated})
    result = bnd_entries(output)
    assert all(result[k][1] == v[1] for k, v in parts.items() if k != name)
    after = read_param(result[name][1], 'PlayerCommonParam')
    assert after['rows'].keys() == table['rows'].keys()
    after_dir, after_end = directory(updated, size)
    assert before_end == after_end and before_dir.keys() == after_dir.keys()
    for rid, r in table['rows'].items():
        assert after['rows'][rid]['name'] == r['name']
        assert before_dir[rid][:3] == after_dir[rid][:3]
        assert after_dir[rid][3] == (bytes(body) if rid == 0 else before_dir[rid][3])
    assert decode(after['rows'][0]['data'], f) == 8
    return output, {
        'table': 'PlayerCommonParam', 'row_id': 0,
        'changes': {'baseMagicSlotSize': {'before': decode(row, f), 'after': 8}},
        'unchanged_talisman_slots': decode(body, fs['baseAccSlotNum']),
        'other_param_tables_unchanged': 193,
        'validation': ['only baseMagicSlotSize byte changed in PlayerCommonParam',
                       'all 193 other PARAM payloads unchanged',
                       'all row names, directories and unrelated fields unchanged',
                       'known 256-byte row layout; opaque tail preserved; no overlap'],
        'scope': 'Shared base memory slots for all player classes; bonuses and slot costs retained',
        'game_validation': 'not run'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--expected-sha256')
    args = p.parse_args()
    assert args.input.resolve() != args.output.resolve()
    source = args.input.read_bytes()
    if args.expected_sha256: assert sha(source) == args.expected_sha256
    key = bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    header, raw = unpack(source, key)
    output, audit = patch(raw)
    assert patch(output)[0] == output, 'Not idempotent'
    packed = zstd.ZstdCompressor(compression_params=zstd.ZstdCompressionParameters.from_level(
        15, window_log=16, write_content_size=False)).compress(output)
    header = bytearray(header)
    struct.pack_into('>II', header, 28, len(output), len(packed))
    plain = bytes(header)+packed
    plain += bytes(-len(plain)%16)
    iv = bytes(16)
    enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    result = iv+enc.update(plain)+enc.finalize()
    assert unpack(result, key)[1] == output
    audit.update(input_sha256=sha(source), output_sha256=sha(result),
                 output_bytes=len(result), bnd_bytes=len(output))
    audit['validation'] += ['idempotence and encrypted round-trip passed']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == '__main__': main()
