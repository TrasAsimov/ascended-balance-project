"""Disable Ascended's extra attack debuffs for players after final integration.

Requires owned matching PARAM definitions and ARMOR_REGULATION_KEY_HEX.
Enemy attack status buildup, triggers, and burst damage are preserved.
Shared legacy rows lose only the explicitly listed extra penalty fields.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys

import zstandard as zstd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'systems/armor/scripts'))
from analyze_regulation import read_param
from field_diff import fields, decode, TYPES
from formats import bnd_entries, bnd_repack, param_patch

# Explicit audited legacy rows; do not infer all debuffs from negative values.
# Negative changeMpPoint/changeMpRate values restore FP rather than drain it.
ATTRIBUTES = ['addLifeForceStatus', 'addWillpowerStatus', 'addEndureStatus',
              'addVitalityStatus', 'addStrengthStatus', 'addDexterityStatus',
              'addMagicStatus', 'addFaithStatus', 'addLuckStatus']
PENALTIES = {
    6202049: {'changeHpPoint': 0, 'changeMpRate': 0, 'staminaRecoverChangeSpeed': 0},
    6202051: {'changeHpRate': 0, 'changeHpPoint': 0, 'changeMpPoint': 0,
              'staminaRecoverChangeSpeed': 0},
    6202053: {'maxStaminaRate': 1, 'staminaRecoverChangeSpeed': 0},
    6202055: {'staminaRecoverChangeSpeed': 0, 'fallDamageRate': 1},
    6202056: {'staminaRecoverChangeSpeed': 0, 'hpRecoverRate': 1},
    6202057: {**dict.fromkeys(ATTRIBUTES, 0), 'staminaRecoverChangeSpeed': 0},
    6202062: dict.fromkeys(ATTRIBUTES, 0),
    6202067: {**dict.fromkeys(ATTRIBUTES, 0), 'staminaRecoverChangeSpeed': 0},
    6202092: {**dict.fromkeys(ATTRIBUTES, 0), 'staminaRecoverChangeSpeed': 0},
    6202100: {'fireDamageCutRate': 1},
    6202101: {'thunderDamageCutRate': 1},
    620205411: {'maxMpRate': 1, 'staminaRecoverChangeSpeed': 0},
}
# 6202050 is an attack-triggered madness burst, not periodic drain: retain it.
# 6202052 already excludes players and the player horse: retain it.
# 6202054 is an attack-buff chain rather than a harmful debuff: retain it.


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def unpack(blob, key):
    assert len(blob) > 16 and (len(blob) - 16) % 16 == 0
    dec = Cipher(algorithms.AES(key), modes.CBC(blob[:16])).decryptor()
    plain = dec.update(blob[16:]) + dec.finalize()
    assert plain[:4] == b'DCX\0' and plain[40:44] == b'ZSTD'
    size, compressed = struct.unpack_from('>II', plain, 28)
    end = 76 + compressed
    assert end <= len(plain) and not any(plain[end:])
    with zstd.ZstdDecompressor().stream_reader(io.BytesIO(plain[76:end])) as reader:
        raw = reader.read()
    assert len(raw) == size and raw[:4] == b'BND4'
    return plain[:76], raw


def patch(raw, paramdef):
    parts = bnd_entries(raw)
    assert len(parts) == 194
    original = parts['SpEffectParam.param'][1]
    table = read_param(original, 'SpEffectParam')
    definitions, size = fields(paramdef)
    assert size == 912 == table['row_size']
    layout = {f[0]: f for f in definitions}
    changes, records = {}, []
    for rid, values in PENALTIES.items():
        row = table['rows'][rid]['data']
        body = bytearray(row)
        before = {}
        for name, target in values.items():
            f = layout[name]
            assert not f[4] and f[6] == 1
            before[name] = decode(row, f)
            struct.pack_into('<' + TYPES[f[1]][0], body, f[2], target)
        if body != row:
            changes[rid] = bytes(body)
        records.append({'id': rid, 'before': before,
                        'after': {k: decode(body, layout[k]) for k in before},
                        'changed': body != row})
    output = bnd_repack(raw, {'SpEffectParam.param': param_patch(original, changes, {}, size)})
    after = bnd_entries(output)
    assert all(after[k][1] == v[1] for k, v in parts.items() if k != 'SpEffectParam.param')
    parsed = read_param(after['SpEffectParam.param'][1], 'SpEffectParam')
    assert parsed['rows'].keys() == table['rows'].keys()
    actual = set()
    for rid, row in table['rows'].items():
        new = parsed['rows'][rid]['data']
        old = row['data']
        assert parsed['rows'][rid]['name'] == row['name']
        if new != old:
            actual.add(rid)
            assert rid in PENALTIES
            allowed = {pos for k in PENALTIES[rid]
                       for pos in range(layout[k][2], layout[k][2] + layout[k][3])}
            for pos, (a, b) in enumerate(zip(old, new)):
                assert a == b or pos in allowed, (rid, pos)
        if rid in PENALTIES:
            for k, value in PENALTIES[rid].items():
                assert decode(new, layout[k]) == value
        # Independent guard against accidentally suppressing status attacks.
        for f in definitions:
            k = f[0]
            if ('effectTarget' in k or k in ['poizonAttackPower', 'diseaseAttackPower',
                    'bloodAttackPower', 'freezeAttackPower', 'sleepAttackPower',
                    'madnessAttackPower', 'curseAttackPower', 'stateInfo',
                    'effectEndurance', 'motionInterval', 'spCategory', 'saveCategory',
                    'replaceSpEffectId', 'cycleOccurrenceSpEffectId', 'atkOccurrenceSpEffectId']):
                assert decode(new, f) == decode(old, f), (rid, k)
    assert actual == changes.keys()
    return output, records, len(parsed['rows']) - len(actual)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--paramdef', type=Path, required=True)
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--expected-sha256')
    args = p.parse_args()
    assert args.input.resolve() != args.output.resolve(), 'Use a separate output file'
    key = bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    source = args.input.read_bytes()
    if args.expected_sha256:
        assert sha(source) == args.expected_sha256, 'Unexpected integration input'
    header, raw = unpack(source, key)
    patched, records, unchanged = patch(raw, args.paramdef)
    assert patch(patched, args.paramdef)[0] == patched, 'Patch must be idempotent'
    packed = zstd.ZstdCompressor(compression_params=zstd.ZstdCompressionParameters.from_level(
        15, window_log=16, write_content_size=False)).compress(patched)
    h = bytearray(header)
    struct.pack_into('>II', h, 28, len(patched), len(packed))
    plain = bytes(h) + packed
    plain += bytes(-len(plain) % 16)
    iv = bytes(16)
    enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    result = iv + enc.update(plain) + enc.finalize()
    assert unpack(result, key)[1] == patched
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    audit = {
        'status': 'static checks passed; game validation not run',
        'input_sha256': sha(source), 'output_sha256': sha(result),
        'output_bytes': len(result), 'param_version': patched[24:32].decode(),
        'scope': 'remove extra penalty fields while preserving enemy attack statuses',
        'rows': records, 'changed_rows': sum(r['changed'] for r in records),
        'unchanged_tables': 193, 'unchanged_speffect_rows': unchanged,
        'validation': ['all other PARAM member bytes identical',
                       'only the declared extra penalty fields changed',
                       'all existing row IDs/names retained',
                       'all target flags, status buildup, triggers and chains unchanged',
                       'madness burst row 6202050 unchanged',
                       'normal status rows, all armor, rewards, core talismans unchanged',
                       'compact BND, idempotence, encrypted round-trip passed'],
        'game_validation': {'startup': 'not run', 'save_and_reload': 'not run',
                            'debuff_immunity': 'not run'},
    }
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: audit[k] for k in ['output_sha256', 'output_bytes', 'changed_rows',
                                          'unchanged_tables', 'unchanged_speffect_rows']}))


if __name__ == '__main__':
    main()
