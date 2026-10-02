"""Enable compatible colossal-weapon Ashes of War on Watchdog's Staff.

Apply after integration. Requires owned matching ARMOR_PARAMDEFS and
ARMOR_REGULATION_KEY_HEX. Preserves Standard affinity, default skill,
custom starting weapons, somber reinforcement and damage balance.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import struct
import sys
import zstandard as zstd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from disable_player_debuffs import sha, unpack
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'systems/armor/scripts'))
from analyze_regulation import read_param
from field_diff import decode, defs, fields
from formats import bnd_entries, bnd_repack, param_patch

WEAPON_ID = 23010000


def patch(raw):
    parts = bnd_entries(raw)
    assert len(parts) == 194
    name = 'EquipParamWeapon.param'
    original = parts[name][1]
    table = read_param(original, 'EquipParamWeapon')
    layout, size = fields(defs()[table['ptype']])
    assert size == table['row_size']
    layout = {f[0]: f for f in layout}
    row = table['rows'][WEAPON_ID]['data']
    assert decode(row, layout['wepType']) == 41
    # Only enable installation. This somber weapon has no affinity rows.
    f = layout['gemMountType']
    assert f[1] == 'u8' and f[4] is None and f[3] == f[6] == 1
    body = bytearray(row)
    body[f[2]] = 2
    updated = param_patch(original, {WEAPON_ID: bytes(body)}, {}, size)
    count = struct.unpack_from('<H', original, 10)[0]
    offsets = {struct.unpack_from('<iIQQ', original, 64+24*i)[0]:
               struct.unpack_from('<iIQQ', original, 64+24*i)[2] for i in range(count)}
    expected = bytearray(original)
    expected[offsets[WEAPON_ID]+f[2]] = 2
    assert updated == expected, 'Non-target PARAM bytes changed'
    output = bnd_repack(raw, {name: updated})
    result = bnd_entries(output)
    assert all(result[k][1] == v[1] for k, v in parts.items() if k != name)
    after = read_param(result[name][1], 'EquipParamWeapon')
    assert after['rows'].keys() == table['rows'].keys()
    for rid, record in table['rows'].items():
        target = after['rows'][rid]
        assert target['name'] == record['name']
        assert target['data'] == (bytes(body) if rid == WEAPON_ID else record['data'])
    for key, spec in layout.items():
        if key != 'gemMountType': assert decode(body, spec) == decode(row, spec), key
    gems = read_param(parts['EquipParamGem.param'][1], 'EquipParamGem')
    gf = {f[0]: f for f in fields(defs()[gems['ptype']])[0]}
    eligible = sorted(rid for rid, record in gems['rows'].items()
                      if decode(record['data'], gf['canMountWep_AxhammerLarge']) == 1)
    assert 10000 in eligible and 30900 not in eligible
    end = struct.unpack_from('<Q', output, 0x28)[0]
    for h, payload in result.values():
        off = struct.unpack_from('<I', output, h+24)[0]
        assert off == (end+15)//16*16 and not any(output[end:off])
        end = off+len(payload)
    assert end == len(output), 'Abandoned binder payload'
    return output, {
        'weapon_id': WEAPON_ID,
        'changes': {'gemMountType': {'before': decode(row, f), 'after': 2}},
        'preserved_fields': {k: decode(body, layout[k]) for k in
            ['swordArtsParamId', 'disableGemAttr', 'reinforceTypeId', 'materialSetId', 'wepType']},
        'eligible_colossal_gem_rows': eligible,
        'other_weapon_rows_unchanged': len(table['rows'])-1,
        'other_param_members_unchanged': len(parts)-1,
        'validation': ['only gemMountType byte changed in entire weapon PARAM',
                       'all names, directories, other weapon rows and 193 tables unchanged',
                       'all other target fields and shared Ash compatibility unchanged',
                       'compact binder has aligned live payloads only'],
        'scope': 'Compatible colossal-weapon Ashes; Standard affinity; somber upgrades retained',
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
    plain += bytes(-len(plain) % 16)
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
    print(json.dumps({k: audit[k] for k in ['weapon_id', 'changes', 'output_sha256', 'output_bytes']}))


if __name__ == '__main__': main()
