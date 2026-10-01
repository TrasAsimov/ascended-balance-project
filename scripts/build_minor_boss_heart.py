"""Add additive minor-boss progression to the existing manual heart refresher.

Owned 1.17.1 inputs/definitions and ARMOR_REGULATION_KEY_HEX are required.
No package creation or publication. Existing events/effects remain intact.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import sys

import zstandard as zstd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'systems/armor/scripts')]
from analyze_regulation import read_param
from field_diff import fields, decode, TYPES
from formats import bnd_entries, bnd_repack, param_patch, Emevd, dcx_pack, dcx_unpack, instruction_builder
from disable_player_debuffs import unpack

REFRESH_EVENT = 20007902
COUNTER_START = 699920
COUNTER_BITS = 8
PARENT_START = 7400000
SPELL_START = 7410000
BAYLE_PARENT = 7400200
BAYLE_CHILD = 7410200
PLAYER = 10000
POWER = ['physicsAttackPowerRate', 'magicAttackPowerRate', 'fireAttackPowerRate',
         'thunderAttackPowerRate', 'darkAttackPowerRate']
DAMAGE = ['physicsAttackRate', 'magicAttackRate', 'fireAttackRate',
          'thunderAttackRate', 'darkAttackRate']


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def load_manifest(path):
    data = json.loads(path.read_text())
    rows = data['bosses']
    assert len(rows) == 181 and sum(not b['dlc'] for b in rows) == 150
    flags = [b['flag_id'] for b in rows]
    assert len(set(flags)) == len(flags)
    excluded = {b['flag_id'] for b in data['excluded_remembrance_bosses']}
    assert len(excluded) == 25 and not excluded.intersection(flags)
    assert data['separate_remembrance_boss']['flag_id'] == 2054390800
    assert 2054390800 not in flags and 2054390800 not in excluded
    assert data['resource_per_boss'] == .002 and data['attack_per_boss'] == .001
    return data


def patch_params(raw, paramdef, count):
    parts = bnd_entries(raw)
    assert len(parts) == 194 and raw[24:32] == b'11711000'
    original = parts['SpEffectParam.param'][1]
    table = read_param(original, 'SpEffectParam')
    definitions, size = fields(paramdef)
    assert size == table['row_size'] == 912
    layout = {f[0]: f for f in definitions}

    def put(body, name, value):
        f = layout[name]
        if f[4]:
            n = int.from_bytes(body[f[2]:f[2]+f[3]], 'little')
            mask = ((1 << f[4])-1) << f[5]
            body[f[2]:f[2]+f[3]] = ((n & ~mask) | (value << f[5])).to_bytes(f[3], 'little')
        else:
            struct.pack_into('<'+TYPES[f[1]][0], body, f[2], value)

    parents, children = {}, {}
    # Existing spell companion is based on the vanilla caster talisman.
    weapon_template = table['rows'][321412]['data']
    spell_template = table['rows'][321435]['data']
    assert decode(spell_template, layout['stateInfo']) == 71
    for n in range(1, count+1):
        parent, child = PARENT_START+n, SPELL_START+n
        resource, attack = 1+.002*n, 1+.001*n
        body = bytearray(weapon_template)
        for k in ['maxHpRate', 'maxMpRate', 'maxStaminaRate']:
            put(body, k, resource)
        for k in POWER:
            put(body, k, attack)
        for k in DAMAGE:
            put(body, k, 1)
        # Explicitly exclude casting attacks from the weapon AR layer.
        put(body, 'magParamChange', 0)
        put(body, 'miracleParamChange', 0)
        put(body, 'wepParamChange', 0)
        put(body, 'spCategory', 0)
        put(body, 'iconId', -1)
        put(body, 'cycleOccurrenceSpEffectId', child)
        put(body, 'motionInterval', .06)
        for k in ['effectTargetSelf', 'effectTargetPlayer', 'effectTargetLive']:
            put(body, k, 1)
        parents[parent] = bytes(body)
        body = bytearray(spell_template)
        for k in DAMAGE:
            put(body, k, attack)
        for k in POWER+['maxHpRate', 'maxMpRate', 'maxStaminaRate']:
            put(body, k, 1)
        put(body, 'magParamChange', 1)
        put(body, 'miracleParamChange', 1)
        put(body, 'wepParamChange', 3)
        put(body, 'spCategory', 0)
        put(body, 'iconId', -1)
        put(body, 'effectEndurance', .1)
        put(body, 'cycleOccurrenceSpEffectId', -1)
        put(body, 'motionInterval', 0)
        for k in ['effectTargetSelf', 'effectTargetPlayer', 'effectTargetLive']:
            put(body, k, 1)
        children[child] = bytes(body)
    assert abs(decode(weapon_template, layout['maxHpRate'])-1.05) < 1e-6
    assert all(decode(weapon_template,layout[k]) == 1 for k in ['maxMpRate','maxStaminaRate'])
    assert all(abs(decode(weapon_template,layout[k])-1.025) < 1e-6 for k in POWER)
    assert all(abs(decode(spell_template,layout[k])-1.025) < 1e-6 for k in DAMAGE)
    bayle = bytearray(weapon_template)
    put(bayle, 'cycleOccurrenceSpEffectId', BAYLE_CHILD)
    parents[BAYLE_PARENT] = bytes(bayle)
    children[BAYLE_CHILD] = bytes(spell_template)
    expected = parents | children
    occupied = set(expected).intersection(table['rows'])
    if occupied:
        assert occupied == set(expected), 'Partial/colliding effect range'
        assert all(table['rows'][k]['data'] == v for k,v in expected.items()), 'Effect collision'
        return raw, layout, expected
    modified = param_patch(original, {}, expected, size)
    output = bnd_repack(raw, {'SpEffectParam.param': modified})
    after_parts = bnd_entries(output)
    assert all(after_parts[k][1] == v[1] for k,v in parts.items() if k != 'SpEffectParam.param')
    after = read_param(after_parts['SpEffectParam.param'][1], 'SpEffectParam')
    assert set(after['rows']) == set(table['rows']) | set(expected)
    for rid, rec in table['rows'].items():
        assert after['rows'][rid]['data'] == rec['data']
        assert after['rows'][rid]['name'] == rec['name']
    assert all(after['rows'][k]['data'] == v for k,v in expected.items())
    return output, layout, expected


def extension(manifest, emedf):
    """Use explicit little-endian scratch flags, independent of EventValue ABI.

    This is a ripple-carry counter recalculated only on manual heart use.
    Short conditional skips avoid condition-group reuse or long-jump limits.
    """
    I = instruction_builder(emedf)
    rows = manifest['bosses']
    out = [I(2004,21,PLAYER,BAYLE_PARENT), I(2004,21,PLAYER,BAYLE_CHILD),
           I(1003,1,2,0,0,manifest['separate_remembrance_boss']['flag_id']),
           I(2004,8,PLAYER,BAYLE_PARENT), I(2004,8,PLAYER,BAYLE_CHILD)]
    for n in range(1, len(rows)+1):
        out += [I(2004,21,PLAYER,PARENT_START+n), I(2004,21,PLAYER,SPELL_START+n)]
    out.append(I(2003,22,COUNTER_START,COUNTER_START+COUNTER_BITS-1,0))
    carry = []
    for bit in range(COUNTER_BITS):
        carry.append(I(2003,9,COUNTER_START+bit))
        if bit < COUNTER_BITS-1:
            carry.append(I(1003,1,2*(COUNTER_BITS-bit-1)-1,1,0,COUNTER_START+bit))
    assert len(carry) == 15 and len(rows) < 2**COUNTER_BITS
    for row in rows:
        out.append(I(1003,1,len(carry),0,0,row['flag_id']))
        out.extend(carry)
    for n in range(1, len(rows)+1):
        for bit in range(COUNTER_BITS):
            # Mismatch skips the rest of this candidate, including its restart.
            out.append(I(1003,1,COUNTER_BITS-bit-1+3,1-((n>>bit)&1),0,COUNTER_START+bit))
        out.extend([I(2004,8,PLAYER,PARENT_START+n),
                    I(2004,8,PLAYER,SPELL_START+n), I(1000,4,1)])
    out.append(I(1000,4,1))  # Zero kills: no new effect, restart original listener.
    return out


def patch_event(blob, manifest, emedf):
    ev = Emevd(dcx_unpack(blob))
    before = copy.deepcopy(ev.events)
    event = next(e for e in ev.events if e['id'] == REFRESH_EVENT)
    assert not event['params']
    extra = extension(manifest, emedf)
    if len(event['ins']) >= len(extra) and event['ins'][-len(extra):] == extra:
        return blob, extra, event['ins'][:-len(extra)]
    # Reserved project-local scratch flags must not already be referenced.
    for e in ev.events:
        for ins in e['ins']:
            for flag in range(COUNTER_START, COUNTER_START+COUNTER_BITS):
                assert struct.pack('<I', flag) not in ins[2], ('flag collision', e['id'], flag)
    assert event['ins'][-1][:2] == (1000,4)
    original_prefix = event['ins'][:-1]
    event['ins'] = original_prefix + extra
    result = dcx_pack(ev.write())
    after = Emevd(dcx_unpack(result)).events
    assert len(after) == len(before)
    for old,new in zip(before,after):
        if old['id'] != REFRESH_EVENT:
            assert old == new
        else:
            assert new['ins'][:len(original_prefix)] == original_prefix
            assert new['params'] == old['params'] and new['rest'] == old['rest']
    return result, extra, original_prefix


def pack_regulation(header, raw, key):
    packed = zstd.ZstdCompressor(compression_params=zstd.ZstdCompressionParameters.from_level(
        15, window_log=16, write_content_size=False)).compress(raw)
    h = bytearray(header)
    struct.pack_into('>II',h,28,len(raw),len(packed))
    plain = bytes(h)+packed
    plain += bytes(-len(plain)%16)
    iv = bytes(16)
    enc = Cipher(algorithms.AES(key),modes.CBC(iv)).encryptor()
    blob = iv+enc.update(plain)+enc.finalize()
    assert unpack(blob,key)[1] == raw
    return blob


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--regulation', type=Path, required=True)
    p.add_argument('--common', type=Path, required=True)
    p.add_argument('--paramdef', type=Path, required=True)
    p.add_argument('--emedf', type=Path, required=True)
    p.add_argument('--manifest', type=Path, default=ROOT/'data/minor_boss_heart.json')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    key = bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    manifest = load_manifest(args.manifest)
    source = args.regulation.read_bytes()
    common = args.common.read_bytes()
    header,raw = unpack(source,key)
    patched,layout,added = patch_params(raw,args.paramdef,len(manifest['bosses']))
    new_common,extra,prefix = patch_event(common,manifest,args.emedf)
    assert patch_params(patched,args.paramdef,len(manifest['bosses']))[0] == patched
    assert patch_event(new_common,manifest,args.emedf)[0] == new_common
    args.output.mkdir(parents=True,exist_ok=True)
    reg = pack_regulation(header,patched,key)
    (args.output/'regulation.bin').write_bytes(reg)
    (args.output/'common.emevd.dcx').write_bytes(new_common)
    audit = {'input_regulation_sha256':sha(source), 'input_common_sha256':sha(common),
             'output_regulation_sha256':sha(reg), 'output_common_sha256':sha(new_common),
             'boss_count':len(manifest['bosses']), 'excluded_remembrance_count':25,
             'resource_cap_multiplier':1.362, 'weapon_and_spell_cap_multiplier':1.181,
             'bayle_separate_remembrance':{'flag':2054390800,'parent':BAYLE_PARENT,'child':BAYLE_CHILD,
               'template_parent':321412,'template_child':321435,'hp_multiplier':1.05,'attack_and_spell_multiplier':1.025},
             'new_effects':len(added), 'effect_ranges':[PARENT_START+1,PARENT_START+181,SPELL_START+1,SPELL_START+181],
             'scratch_flags':[COUNTER_START,COUNTER_START+COUNTER_BITS-1],
             'modified_event':REFRESH_EVENT,'preserved_event_prefix_instructions':len(prefix),
             'extension_instructions':len(extra), 'preserved_param_tables':193,
             'all_existing_parameter_rows_unchanged':True,'all_other_events_unchanged':True,
             'idempotence':True,'game_validation':'not run'}
    (args.output/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(audit,ensure_ascii=False))


if __name__ == '__main__':
    main()
