"""Remove weapon-equipped global buffs and anomalous weapon passives.

The result is staged for game testing. Only known weapon-side effects and the
Vigor graph are edited; boss and event files remain untouched.
"""
from __future__ import annotations

import csv
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / 'work'))
from field_diff import decode, defs, fields, names
from analyze_regulation import read_bnd
from build_v04 import decrypt_official
from build_v05 import active_rows, encrypt_native

SRC = ROOT/'work/pending_torrent.bnd'
OFFICIAL = ROOT/'work/vanilla_117.bnd'
OUT = ROOT/'work/pending_weapon_audit_fix.bnd'
REG = ROOT/'output/pending_weapon_audit_fix_regulation.bin'
LOG = ROOT/'changes/pending_weapon_audit_fix.csv'
SLOTS = ('residentSpEffectId', 'residentSpEffectId1', 'residentSpEffectId2')
BEHAVIOR = ('spEffectBehaviorId0', 'spEffectBehaviorId1', 'spEffectBehaviorId2')
FLAT = ('physicsAttackPower', 'magicAttackPower', 'fireAttackPower',
        'thunderAttackPower', 'darkAttackPower', 'slashAttackPower',
        'blowAttackPower', 'thrustAttackPower', 'neutralAttackPower')
SCALE = ('correctStrength', 'correctAgility', 'correctMagic',
         'correctFaith', 'correctLuck')

def main():
    _, mod = read_bnd(SRC)
    _, vanilla = read_bnd(OFFICIAL)
    raw = bytearray(SRC.read_bytes())
    wf = {f[0]: f for f in fields(defs()[mod['EquipParamWeapon']['ptype']])[0]}
    ef = {f[0]: f for f in fields(defs()[mod['SpEffectParam']['ptype']])[0]}
    gf = {f[0]: f for f in fields(defs()[mod['CalcCorrectGraph']['ptype']])[0]}
    wo = active_rows(raw, 'EquipParamWeapon')
    eo = active_rows(raw, 'SpEffectParam')
    go = active_rows(raw, 'CalcCorrectGraph')
    weapon = mod['EquipParamWeapon']['rows']
    standard = vanilla['EquipParamWeapon']['rows']
    effects = mod['SpEffectParam']['rows']
    wn = names('EquipParamWeapon')
    edits = []

    def put(table, rid, field, value, why):
        fs, offsets = ((wf, wo) if table == 'EquipParamWeapon' else
                       (ef, eo) if table == 'SpEffectParam' else (gf, go))
        spec = fs[field]
        assert spec[4] is None and spec[6] == 1
        old = decode(mod[table]['rows'][rid]['data'], spec)
        if old == value:
            return
        fmt = {'f32': 'f', 's32': 'i', 'u32': 'I', 'u16': 'H', 'u8': 'B'}[spec[1]]
        struct.pack_into('<'+fmt, raw, offsets[rid]+spec[2], value)
        edits.append((table, rid, wn.get(rid, '') if table == 'EquipParamWeapon' else '',
                      field, old, value, why))

    # This Ascended effect is equipped on 2,593 weapon rows, but not on
    # Watchdog's Staff. It doubles HP and adds +150 to every damage channel.
    # Keep its unrelated fields and neutralize those resource/damage fields.
    assert decode(effects[6202065]['data'], ef['maxHpRate']) == 2.0
    put('SpEffectParam', 6202065, 'maxHpRate', 1.0,
        '移除依赖手持武器的生命倍率，改由生命成长曲线承担')
    for field in FLAT:
        assert decode(effects[6202065]['data'], ef[field]) == 150
        put('SpEffectParam', 6202065, field, 0,
            '移除所有武器共同获得的全属性固定攻击力')

    # A genuine 2x official Vigor curve applies even when empty handed and
    # while switching to a staff. Restore official shape, double HP values.
    official_graph = vanilla['CalcCorrectGraph']['rows'][100]['data']
    for f in gf.values():
        original = decode(official_graph, f)
        if f[0].startswith('stageMaxGrowVal') and f[0][-1].isdigit():
            put('CalcCorrectGraph', 100, f[0], 2.0*original, '玩家生命成长为原版的两倍')
        elif f[0] in ('stageMaxVal1', 'stageMaxVal2', 'stageMaxVal3',
                     'adjPt_maxGrowVal2', 'adjPt_maxGrowVal3'):
            put('CalcCorrectGraph', 100, f[0], original, '恢复原版生命曲线形状')

    # Resident effects with unconditional flat attack/HP were substituted for
    # native passives across many ordinary weapons, including elemental +50.
    # Restore only altered slots with this symptom. Preserve unchanged native
    # effects and the now-neutral 6202065 slot.
    def anomalous(eid):
        row = effects.get(eid)
        return bool(row and (decode(row['data'], ef['maxHpRate']) != 1.0 or
                             any(decode(row['data'], ef[k]) for k in FLAT)))

    for rid, row in weapon.items():
        original = standard.get(rid)
        for slot in SLOTS:
            eid = decode(row['data'], wf[slot])
            if eid == 6202065 or not anomalous(eid):
                continue
            vanilla_eid = decode(original['data'], wf[slot]) if original else -1
            if eid != vanilla_eid:
                put('EquipParamWeapon', rid, slot, vanilla_eid,
                    '恢复原版常驻效果；移除额外生命或无条件属性攻击')
        if not original:
            continue
        for slot in BEHAVIOR:
            vanilla_eid = decode(original['data'], wf[slot])
            put('EquipParamWeapon', rid, slot, vanilla_eid,
                '恢复原版武器固有异常状态与行为效果')

        # The Ascended 200-point correction makes a number of ordinary melee
        # weapons several times stronger than their official counterparts.
        # Cap extreme coefficients to 150% of official, without touching
        # staffs and seals (spell scaling must be balanced separately).
        kind = decode(row['data'], wf['wepType'])
        if kind in (57, 61):
            continue
        for field in SCALE:
            before = decode(row['data'], wf[field])
            base = decode(original['data'], wf[field])
            if base > 0 and before > base*1.5:
                put('EquipParamWeapon', rid, field, float(round(base*1.5, 2)),
                    '近战武器过高属性补正上限：原版的 1.5 倍')

    OUT.write_bytes(raw)
    _, check = read_bnd(OUT)
    changed = {(table, rid) for table, rid, *_ in edits}
    for table, rows in mod.items():
        for rid, row in rows['rows'].items():
            if (table, rid) not in changed:
                assert check[table]['rows'][rid]['data'] == row['data'], (table, rid)
    assert decode(check['SpEffectParam']['rows'][6202065]['data'], ef['maxHpRate']) == 1.0
    assert all(decode(check['SpEffectParam']['rows'][6202065]['data'], ef[k]) == 0 for k in FLAT)
    for rid, row in check['EquipParamWeapon']['rows'].items():
        for slot in SLOTS:
            eid = decode(row['data'], wf[slot])
            if eid in check['SpEffectParam']['rows']:
                assert decode(check['SpEffectParam']['rows'][eid]['data'], ef['maxHpRate']) == 1.0, (rid, slot, eid)
    template, _ = decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
    encrypted = encrypt_native(template, bytes(raw))
    assert decrypt_official(encrypted)[1] == bytes(raw)
    REG.write_bytes(encrypted)
    with LOG.open('w', newline='', encoding='utf-8-sig') as fh:
        writer = csv.writer(fh)
        writer.writerow(('参数表', '行ID', '武器英文名', '字段', '修改前', '修改后', '原因'))
        writer.writerows(edits)
    from collections import Counter
    print('weapon audit edits:', len(edits), Counter(e[0] for e in edits),
          'changed weapon rows:', len({e[1] for e in edits if e[0] == 'EquipParamWeapon'}))

if __name__ == '__main__':
    main()
