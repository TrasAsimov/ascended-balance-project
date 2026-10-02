"""Dual light greatswords with Wing Stance; equal starter goods for new classes.

Uses custom weapon presets, preserving shared weapon/skill parameters.
Requires ARMOR_PARAMDEFS and ARMOR_REGULATION_KEY_HEX.
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
from field_diff import defs, fields, decode, TYPES
from formats import bnd_entries, bnd_repack, param_patch
from verify_layout import directory

LIGHT_ROWS = (3010, 3120, 3121)
HEAVY_ROWS = (3011, 3122, 3123)
PRESETS = (7000, 7001)
LIGHT_WEAPON = 67530000
WING_GEM = 412000
WING_SKILL = 4120
REFERENCE_CLASS = 3000


def patch(raw):
    parts = bnd_entries(raw)
    assert len(parts) == 194
    names = ['CharaInitParam', 'EquipParamCustomWeapon', 'EquipParamWeapon', 'EquipParamGem',
             'BaseChrSelectMenuParam', 'SwordArtsParam', 'EquipParamGoods']
    tables = {t: read_param(parts[t+'.param'][1], t) for t in names}
    definitions = defs()
    layout = {}; sizes = {}
    for t in names:
        fs, size = fields(definitions[tables[t]['ptype']])
        layout[t] = {f[0]: f for f in fs}; sizes[t] = size
    def get(t, rid, key):
        return decode(tables[t]['rows'][rid]['data'], layout[t][key])
    def put(body, t, key, value):
        f = layout[t][key]
        assert f[4] is None and f[6] == 1
        struct.pack_into('<'+TYPES[f[1]][0], body, f[2], value)
    assert get('BaseChrSelectMenuParam', 2010, 'originChrInitParam') == 3010
    assert get('BaseChrSelectMenuParam', 2010, 'chrInitParam') == 3120
    assert get('BaseChrSelectMenuParam', 2011, 'originChrInitParam') == 3011
    assert get('BaseChrSelectMenuParam', 2011, 'chrInitParam') == 3122
    assert get('EquipParamWeapon', LIGHT_WEAPON, 'wepType') == 93
    assert get('EquipParamGem', WING_GEM, 'swordArtsParamId') == WING_SKILL
    assert WING_SKILL in tables['SwordArtsParam']['rows']
    assert get('EquipParamGem', WING_GEM, 'configurableWepAttr00') == 1
    # Match the full actual Vagabond starting bag, including one spirit ash
    # and one reusable heart. The ten older origins all share 20 of each bolus.
    goods = {key: get('CharaInitParam', REFERENCE_CLASS, key)
             for i in range(1, 11) for key in [f'item_{i:02}', f'itemNum_{i:02}']}
    bag = [(goods[f'item_{i:02}'], goods[f'itemNum_{i:02}']) for i in range(1, 11)]
    assert bag[:7] == [(900+10*i, 20) for i in range(7)]
    assert bag[7:9] == [(203000, 1), (2001431, 1)]
    for rid in range(3000, 3010):
        counts = {get('CharaInitParam', rid, f'item_{i:02}'): get('CharaInitParam', rid, f'itemNum_{i:02}')
                  for i in range(1, 11)}
        assert all(counts.get(900+10*i) == 20 for i in range(7))
    for i, count in bag:
        if i != -1: assert i in tables['EquipParamGoods']['rows'] and 0 < count <= get('EquipParamGoods', i, 'maxNum')
    expected_presets = {}
    for rid in PRESETS:
        body = bytearray(tables['EquipParamCustomWeapon']['rows'][100]['data'][:sizes['EquipParamCustomWeapon']])
        put(body, 'EquipParamCustomWeapon', 'baseWepId', LIGHT_WEAPON)
        put(body, 'EquipParamCustomWeapon', 'gemId', WING_GEM)
        put(body, 'EquipParamCustomWeapon', 'reinforceLv', 0)
        expected_presets[rid] = bytes(body)
        if rid in tables['EquipParamCustomWeapon']['rows']:
            assert tables['EquipParamCustomWeapon']['rows'][rid]['data'] == body, ('Preset ID collision', rid)
    additions = {rid: body for rid, body in expected_presets.items()
                 if rid not in tables['EquipParamCustomWeapon']['rows']}
    target_fields = {rid: dict(goods) for rid in [3010, 3011]}
    for rid in LIGHT_ROWS:
        target_fields.setdefault(rid, {}).update(equip_Wep_Right=PRESETS[0], equip_Wep_Left=PRESETS[1],
                                                 wepParamType_Right1=1, wepParamType_Left1=1)
    changes = {}; records = []
    for rid, values in target_fields.items():
        row = tables['CharaInitParam']['rows'][rid]['data']
        assert len(row) == sizes['CharaInitParam']
        body = bytearray(row)
        diff = {}
        for key, value in values.items():
            put(body, 'CharaInitParam', key, value)
            if get('CharaInitParam', rid, key) != value:
                diff[key] = {'before': get('CharaInitParam', rid, key), 'after': value}
        changes[rid] = bytes(body)
        records.append({'row_id': rid, 'changes': diff})
    updates = {
        'CharaInitParam.param': param_patch(parts['CharaInitParam.param'][1], changes, {}, sizes['CharaInitParam']),
        'EquipParamCustomWeapon.param': param_patch(parts['EquipParamCustomWeapon.param'][1], {}, additions, sizes['EquipParamCustomWeapon'])}
    output = bnd_repack(raw, updates)
    after = bnd_entries(output)
    assert all(after[k][1] == v[1] for k, v in parts.items() if k not in updates)
    for t in ['CharaInitParam', 'EquipParamCustomWeapon']:
        prior, end = directory(parts[t+'.param'][1], sizes[t])
        result, newend = directory(after[t+'.param'][1], sizes[t])
        delta = 24*len(additions) if t == 'EquipParamCustomWeapon' else 0
        assert newend == end+delta
        assert result.keys()-prior.keys() == (additions.keys() if t == 'EquipParamCustomWeapon' else set())
        for rid, (pad, off, name, body) in prior.items():
            a = result[rid]
            assert a[:3] == (pad, off+delta, name+delta if name else 0)
            assert a[3] == (changes.get(rid, body) if t == 'CharaInitParam' else body)
        for rid, body in additions.items():
            if t == 'EquipParamCustomWeapon': assert result[rid][3] == body
    cp = read_param(after['CharaInitParam.param'][1], 'CharaInitParam')
    for rid, values in target_fields.items():
        for key, value in values.items(): assert decode(cp['rows'][rid]['data'], layout['CharaInitParam'][key]) == value
    for rid in HEAVY_ROWS:
        for key in layout['CharaInitParam']:
            if 'Wep' in key or key.startswith('wepParamType'):
                assert decode(cp['rows'][rid]['data'], layout['CharaInitParam'][key]) == get('CharaInitParam', rid, key)
    return output, {
        'light_origin': 3010, 'heavy_origin': 3011, 'light_preview_rows': [3120, 3121],
        'light_weapon': LIGHT_WEAPON, 'wing_gem': WING_GEM, 'wing_skill': WING_SKILL,
        'custom_preset_ids': list(PRESETS), 'new_preset_rows': len(additions),
        'reference_goods_origin': REFERENCE_CLASS, 'starting_goods': bag,
        'row_changes': records, 'other_param_tables_unchanged': 192,
        'validation': ['all shared weapon, Ash, skill and 192 other table payloads unchanged',
                       'two actual origin bags exactly match reference origin',
                       'both light preview templates and actual origin use two +0 Wing Stance presets',
                       'all heavy weapon slots/types unchanged',
                       'other rows, directory/name offsets and known-size non-overlap checked'],
        'game_validation': 'not run'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--audit', type=Path, required=True); p.add_argument('--expected-sha256')
    args = p.parse_args(); assert args.input.resolve() != args.output.resolve()
    source = args.input.read_bytes()
    if args.expected_sha256: assert sha(source) == args.expected_sha256
    key = bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    header, raw = unpack(source, key); output, audit = patch(raw)
    assert patch(output)[0] == output, 'Not idempotent'
    packed = zstd.ZstdCompressor(compression_params=zstd.ZstdCompressionParameters.from_level(
        15, window_log=16, write_content_size=False)).compress(output)
    header = bytearray(header); struct.pack_into('>II', header, 28, len(output), len(packed))
    plain = bytes(header)+packed; plain += bytes(-len(plain)%16); iv = bytes(16)
    enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    result = iv+enc.update(plain)+enc.finalize(); assert unpack(result, key)[1] == output
    audit.update(input_sha256=sha(source), output_sha256=sha(result), output_bytes=len(result), bnd_bytes=len(output))
    audit['validation'] += ['idempotence and encrypted round-trip passed']
    args.output.parent.mkdir(parents=True, exist_ok=True); args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result); args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: audit[k] for k in ['new_preset_rows', 'starting_goods', 'output_sha256', 'output_bytes']}, ensure_ascii=False))


if __name__ == '__main__': main()
