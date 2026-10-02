"""Apply the final new-class builds AFTER update_new_class_loadouts.py.

Heavy: Leontiel's Greatsword, commoner clothing, Alexander, 121 stat points.
Light: retain two Wing Stance swords; add Alexander and Winged Sword Insignia.
Both: remove spirit ashes from origin and preview primary/secondary inventory.
Requires ARMOR_PARAMDEFS and ARMOR_REGULATION_KEY_HEX, never embeds a key.
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
HEAVY_WEAPON = 3560000
ALEXANDER = 1231
COMBO_TALISMAN = 2080
STAT_KEYS = ('baseVit', 'baseWil', 'baseEnd', 'baseStr', 'baseDex', 'baseMag', 'baseFai', 'baseLuc')
HEAVY_STATS = dict(zip(STAT_KEYS, (20, 12, 30, 13, 26, 7, 8, 5)))
HEAVY_ARMOR = dict(equip_Helm=810000, equip_Armer=810100,
                   equip_Gaunt=-1, equip_Leg=810300)


def patch(raw):
    parts = bnd_entries(raw)
    assert len(parts) == 194
    names = ('CharaInitParam', 'EquipParamWeapon', 'EquipParamAccessory',
             'EquipParamCustomWeapon', 'EquipParamGoods', 'BaseChrSelectMenuParam',
             'SwordArtsParam', 'EquipParamGem', 'SpEffectParam', 'EquipParamProtector')
    tables = {t: read_param(parts[t+'.param'][1], t) for t in names}
    definitions = defs(); layout = {}; sizes = {}
    for t in names:
        fs, size = fields(definitions[tables[t]['ptype']])
        layout[t] = {f[0]: f for f in fs}; sizes[t] = size
    def get(t, rid, key):
        return decode(tables[t]['rows'][rid]['data'], layout[t][key])
    def put(body, key, value):
        f = layout['CharaInitParam'][key]
        assert f[4] is None and f[6] == 1
        struct.pack_into('<'+TYPES[f[1]][0], body, f[2], value)
    assert get('BaseChrSelectMenuParam', 2010, 'originChrInitParam') == 3010
    assert get('BaseChrSelectMenuParam', 2010, 'chrInitParam') == 3120
    assert get('BaseChrSelectMenuParam', 2011, 'originChrInitParam') == 3011
    assert get('BaseChrSelectMenuParam', 2011, 'chrInitParam') == 3122
    assert get('EquipParamWeapon', HEAVY_WEAPON, 'wepType') == 5
    assert get('EquipParamWeapon', HEAVY_WEAPON, 'swordArtsParamId') == 1200
    assert 1200 in tables['SwordArtsParam']['rows']
    for aid in (ALEXANDER, COMBO_TALISMAN):
        assert get('EquipParamAccessory', aid, 'refId') in tables['SpEffectParam']['rows']
    assert get('EquipParamAccessory', ALEXANDER, 'refId') == 312310
    assert get('EquipParamAccessory', COMBO_TALISMAN, 'refId') == 320800
    for pid in HEAVY_ARMOR.values():
        if pid >= 0:
            assert pid in tables['EquipParamProtector']['rows']
            assert get('EquipParamProtector', pid, 'weight') > 0
    # Fail rather than silently lose the previously authorized dual-sword build.
    for rid in LIGHT_ROWS:
        for key, value in dict(equip_Wep_Right=7000, equip_Wep_Left=7001,
                               wepParamType_Right1=1, wepParamType_Left1=1).items():
            assert get('CharaInitParam', rid, key) == value, 'Run the prior loadout module first'
    for rid in (7000, 7001):
        assert get('EquipParamCustomWeapon', rid, 'baseWepId') == 67530000
        assert get('EquipParamCustomWeapon', rid, 'gemId') == 412000
        assert get('EquipParamCustomWeapon', rid, 'reinforceLv') == 0
    assert get('EquipParamGem', 412000, 'swordArtsParamId') == 4120
    budgets = {rid: sum(get('CharaInitParam', rid, k) for k in STAT_KEYS)
               for rid in range(3000, 3010)}
    assert min(budgets.values()) <= sum(HEAVY_STATS.values()) <= max(budgets.values())
    targets = {}
    for rid in LIGHT_ROWS:
        targets[rid] = dict(equip_Accessory01=ALEXANDER, equip_Accessory02=COMBO_TALISMAN)
    for rid in HEAVY_ROWS:
        targets[rid] = dict(HEAVY_STATS, equip_Wep_Right=HEAVY_WEAPON,
                            wepParamType_Right1=0, equip_Accessory01=ALEXANDER)
        targets[rid].update(HEAVY_ARMOR)
    # goodsType 7 is spirit summon goods. Check every provided inventory slot,
    # including secondary items; preserve all non-ash goods and empty slots.
    removed = []
    for rid, values in targets.items():
        for prefix, count in (('item', 10), ('secondaryItem', 6)):
            for i in range(1, count+1):
                key = f'{prefix}_{i:02}'; nk = f'{prefix}Num_{i:02}'
                gid = get('CharaInitParam', rid, key)
                if gid >= 0:
                    assert gid in tables['EquipParamGoods']['rows']
                    if get('EquipParamGoods', gid, 'goodsType') == 7:
                        removed.append({'row_id': rid, 'slot': key, 'goods_id': gid,
                                        'quantity': get('CharaInitParam', rid, nk)})
                        values.update({key: -1, nk: 0})
    changes = {}; records = []
    for rid, values in targets.items():
        original = tables['CharaInitParam']['rows'][rid]['data']
        assert len(original) == sizes['CharaInitParam']
        body = bytearray(original); diff = {}; allowed = set()
        for key, value in values.items():
            put(body, key, value)
            f = layout['CharaInitParam'][key]; allowed.update(range(f[2], f[2]+f[3]))
            before = get('CharaInitParam', rid, key)
            if before != value: diff[key] = {'before': before, 'after': value}
        assert all(i in allowed for i, (a, b) in enumerate(zip(original, body)) if a != b)
        changes[rid] = bytes(body); records.append({'row_id': rid, 'changes': diff})
    source_param = parts['CharaInitParam.param'][1]
    result_param = param_patch(source_param, changes, {}, sizes['CharaInitParam'])
    output = bnd_repack(raw, {'CharaInitParam.param': result_param})
    after = bnd_entries(output)
    assert all(after[k][1] == p[1] for k, p in parts.items() if k != 'CharaInitParam.param')
    prior, end = directory(source_param, sizes['CharaInitParam'])
    result, newend = directory(result_param, sizes['CharaInitParam'])
    assert end == newend and prior.keys() == result.keys()
    for rid, row in prior.items():
        assert result[rid][:3] == row[:3]
        assert result[rid][3] == changes.get(rid, row[3])
    cp = read_param(result_param, 'CharaInitParam')
    def final(rid, key): return decode(cp['rows'][rid]['data'], layout['CharaInitParam'][key])
    for rid, values in targets.items():
        for key, value in values.items(): assert final(rid, key) == value
        for prefix, count in (('item', 10), ('secondaryItem', 6)):
            for i in range(1, count+1):
                gid = final(rid, f'{prefix}_{i:02}')
                assert gid < 0 or get('EquipParamGoods', gid, 'goodsType') != 7
    requirements = dict(zip(('baseStr', 'baseDex', 'baseMag', 'baseFai', 'baseLuc'),
                            ('properStrength', 'properAgility', 'properMagic', 'properFaith', 'properLuck')))
    requirement_audit = {}
    for rows, weapon in ((LIGHT_ROWS, 67530000), (HEAVY_ROWS, HEAVY_WEAPON)):
        requirement_audit[weapon] = {sk: get('EquipParamWeapon', weapon, wk) for sk, wk in requirements.items()}
        for rid in rows:
            assert all(final(rid, sk) >= req for sk, req in requirement_audit[weapon].items())
    for rid in (3010, 3011):
        bag = {final(rid, f'item_{i:02}'): final(rid, f'itemNum_{i:02}') for i in range(1, 11)}
        assert all(bag.get(900+10*i) == 20 for i in range(7))
        assert bag[2001431] == 1
        assert final(rid, 'secondaryItem_01') == 115 and final(rid, 'secondaryItemNum_01') == 1
    return output, {
        'heavy_weapon': {'id': HEAVY_WEAPON, 'name': "Leontiel's Greatsword", 'skill_id': 1200},
        'heavy_stats': HEAVY_STATS, 'heavy_stat_total': sum(HEAVY_STATS.values()),
        'heavy_armor': HEAVY_ARMOR,
        'reference_stat_budgets': budgets, 'reference_stat_average': sum(budgets.values())/len(budgets),
        'light_stats': {k: final(3010, k) for k in STAT_KEYS},
        'accessories': {'heavy': [ALEXANDER], 'light': [ALEXANDER, COMBO_TALISMAN]},
        'weapon_requirements': requirement_audit, 'removed_spirit_ashes': removed,
        'row_changes': records, 'changed_param_tables': ['CharaInitParam'],
        'other_param_tables_unchanged': 193,
        'validation': ['single-hand requirements met without equipment bonuses for both classes and previews',
                       'both origins and all four previews contain no spirit ashes in either inventory',
                       'seven boluses x20, heart x1 and Memory of Grace x1 retained',
                       'two +0 light swords and Wing Stance presets retained',
                       'heavy origin and both sex previews wear commoner headband, garb and shoes; no gloves',
                       '193 other table payloads unchanged, including melee reinforcement and all shared skills',
                       'all non-target rows and fields, directory/name offsets and known-size non-overlap checked'],
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
    audit['validation'] += ['binary idempotence and encrypted round-trip passed']
    args.output.parent.mkdir(parents=True, exist_ok=True); args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result); args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: audit[k] for k in ['heavy_stats', 'heavy_stat_total', 'output_sha256', 'output_bytes']}, ensure_ascii=False))


if __name__ == '__main__': main()
