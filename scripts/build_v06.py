"""Rebalance player display and repair missing vanilla critical throws.

Starts from the exact v0.5 release regulation and keeps all unrelated bytes.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import struct
import sys

from analyze_regulation import read_bnd
from build_v04 import decrypt_official
from build_v05 import active_rows, encrypt_native

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / 'work'))
from field_diff import defs, fields, decode

SOURCE = ROOT / 'work/v05_reconciled.bnd'
VANILLA = ROOT / 'work/vanilla_117.bnd'
VANILLA_REG = ROOT.parent / 'upload/regulation.bin'
OUT = ROOT / 'output'


def main():
    OUT.mkdir(exist_ok=True)
    _, mod = read_bnd(SOURCE)
    _, vanilla = read_bnd(VANILLA)
    data = bytearray(SOURCE.read_bytes())
    changes = []

    # The renderer uses resource / menu-limit to calculate gauge width.
    # v0.5 already doubled the official limits; the tester still saw bars
    # spanning three quarters of a 2048px screen. These further increases
    # leave the underlying HP/FP/SP resource values unchanged.
    menu = active_rows(data, 'MenuCommonParam')[0]
    for pos, name, factor in ((8, 'playerMaxHpLimit', 4),
                              (12, 'playerMaxMpLimit', 2),
                              (16, 'playerMaxSpLimit', 2)):
        old = struct.unpack_from('<i', data, menu + pos)[0]
        assert old in (7130, 1650, 960)
        new = old * factor
        assert 0 < new < 99999
        struct.pack_into('<i', data, menu + pos, new)
        changes.append(('MenuCommonParam', 0, name, old, new,
                        '只改变状态条显示尺度，不改变资源数值'))

    speffect_id = 6202065
    fs, size = fields(defs()[mod['SpEffectParam']['ptype']])
    hp = next(f for f in fs if f[0] == 'maxHpRate')
    assert size == mod['SpEffectParam']['row_size'] == vanilla['SpEffectParam']['row_size']
    pos = active_rows(data, 'SpEffectParam')[speffect_id] + hp[2]
    old = struct.unpack_from('<f', data, pos)[0]
    assert old == 1.5
    struct.pack_into('<f', data, pos, 2.0)
    changes.append(('SpEffectParam', speffect_id, 'maxHpRate', old, 2.0,
                    '玩家基础生命倍率调整为 2 倍'))

    def put_field(table, rid, name, value, reason, expected=None):
        spec, row_size = fields(defs()[mod[table]['ptype']])
        assert row_size == mod[table]['row_size']
        field = next(f for f in spec if f[0] == name)
        assert field[6] == 1
        pos = active_rows(data, table)[rid] + field[2]
        old = decode(mod[table]['rows'][rid]['data'], field)
        if expected is not None:
            assert old == expected, (table, rid, name, old, expected)
        if field[4] is not None:
            assert field[3] == 1 and 0 <= value < (1 << field[4])
            mask = ((1 << field[4]) - 1) << field[5]
            data[pos] = (data[pos] & ~mask) | (value << field[5])
        else:
            fmt = {'f32': 'f', 's32': 'i', 'u32': 'I', 'u16': 'H', 'u8': 'B'}[field[1]]
            assert struct.calcsize(fmt) == field[3]
            struct.pack_into('<' + fmt, data, pos, value)
        changes.append((table, rid, name, old, value, reason))

    # Ascended's fivefold always-on MP effect combines with a doubled Mind
    # curve. Keep meaningful room for repeat casts without 10k+ FP pools.
    put_field('SpEffectParam', speffect_id, 'maxMpRate', 1.0,
              '取消玩家常驻五倍 FP；以等级曲线给法术和战技保留可用次数', 5.0)
    for name, old, new in [('stageMaxGrowVal2', 500.0, 450.0),
                           ('stageMaxGrowVal3', 700.0, 550.0),
                           ('stageMaxGrowVal4', 900.0, 650.0)]:
        put_field('CalcCorrectGraph', 101, name, new,
                  '收敛高等级集中力的 FP 成长，99 级目标基值约 650', old)

    # The first Carian Slicer hit was doubled in Ascended; follow-up hitboxes
    # retained official correction, causing an abrupt damage collapse.
    for rid in (44401, 44405, 44406, 44407, 44408):
        put_field('AtkParam_Pc', rid, 'atkMagCorrection', 200,
                  '卡利亚迅剑后续判定与首段魔力补正一致', 100)

    # Tune the main breath hitboxes individually: base breath ~1.5x official,
    # named variants ~1.5x official. Preserve status and repeat-hit timing.
    breath = {
        70000: ('atkFire', 216), 70010: ('atkFire', 254),
        70100: ('atkFire', 335), 70110: ('atkFire', 473),
        70200: ('atkMag', 203), 70210: ('atkMag', 237),
        70300: ('atkPhys', 197), 70310: ('atkPhys', 233),
        70400: ('atkMag', 239), 70410: ('atkMag', 282),
        210702000: ('atkMag', 252),
    }
    for rid, (name, value) in breath.items():
        put_field('AtkParam_Pc', rid, name, value,
                  '龙飨吐息主判定相对原版约 1.5 倍，保留持续命中和异常状态')
    for rid, name, value in ((70600, 'atkPhys', 494),
                             (70800, 'atkPhys', 785),
                             (70900, 'atkPhys', 400)):
        put_field('AtkParam_Pc', rid, name, value,
                  '龙爪／龙咬／龙吼主要攻击约 1.25 倍原版')

    # In v0.5 the SwordArtsParam and attack rows were restored, but these
    # unique weapons retained overwritten weapon-side effects and gem flags.
    for rid in (3140000, 8100000, 23100000):
        for name in ('spEffectBehaviorId0', 'residentSpEffectId',
                     'residentSpEffectId1', 'disableGemAttr', 'gemMountType'):
            field = next(f for f in fields(defs()[mod['EquipParamWeapon']['ptype']])[0]
                         if f[0] == name)
            original = decode(vanilla['EquipParamWeapon']['rows'][rid]['data'], field)
            previous = decode(mod['EquipParamWeapon']['rows'][rid]['data'], field)
            if previous != original:
                put_field('EquipParamWeapon', rid, name, original,
                          '恢复武器自带战技关联的原版效果与固定战灰限制', previous)
    for name in ('correctStrength', 'correctAgility'):
        put_field('EquipParamWeapon', 23100000, name, 42.0,
                  '恢复基萨刺轮被清零的力量和灵巧补正', 0.0)

    # The compact migration copied 1.16's empty DLC throw records over
    # 1.17.1's executable records. Restore only rows with a missing attacker
    # animation, never add a finisher to an enemy absent from official data.
    throw = mod['ThrowParam']['rows']
    base_throw = vanilla['ThrowParam']['rows']
    fs, size = fields(defs()[mod['ThrowParam']['ptype']])
    atk = next(f for f in fs if f[0] == 'atkAnimId')
    assert size == mod['ThrowParam']['row_size'] == vanilla['ThrowParam']['row_size']
    offsets = active_rows(data, 'ThrowParam')
    restored = []
    for rid, row in throw.items():
        original = base_throw.get(rid)
        if original is None:
            continue
        old, new = decode(row['data'], atk), decode(original['data'], atk)
        if old == 0 and new > 0:
            data[offsets[rid]:offsets[rid] + size] = original['data']
            restored.append(rid)
            changes.append(('ThrowParam', rid, 'whole_official_row',
                            'missing attacker animation', 'official 1.17.1 row',
                            '恢复原版已有的处决配对和动作，不给原版不可处决的敌人新增定义'))
    assert sorted(restored) == sorted((10201020, 13356000, 13357000,
                                      13360000, 14211000, 14212000,
                                      14212001, 14213000, 14213001,
                                      14219000, 14250000, 14250001))

    # Ascended points every ordinary weather record at heavy fog (51).
    # Use the existing ordinary fog (50) light profile to soften the extreme
    # darkness; preserve the weather event files and all other parameters.
    fs, size = fields(defs()[mod['WeatherParam']['ptype']])
    gparam = next(f for f in fs if f[0] == 'GparamId')
    assert size == mod['WeatherParam']['row_size'] == vanilla['WeatherParam']['row_size']
    offsets = active_rows(data, 'WeatherParam')
    weather = []
    for rid, row in mod['WeatherParam']['rows'].items():
        base = vanilla['WeatherParam']['rows'].get(rid)
        if not base:
            continue
        old, vanilla_id = decode(row['data'], gparam), decode(base['data'], gparam)
        if old == 51 and vanilla_id != 51:
            struct.pack_into('<I', data, offsets[rid] + gparam[2], 50)
            weather.append(rid)
            changes.append(('WeatherParam', rid, 'GparamId', old, 50,
                            '用普通雾天气光照配置替代全局强制浓雾；保持事件和夜晚机制'))
    assert len(weather) == 15

    raw = bytes(data)
    target = ROOT / 'work/v06.bnd'
    target.write_bytes(raw)
    version, check = read_bnd(target)
    assert version == '11711000' and len(check) == 194
    for tb in mod:
        for rid, rec in mod[tb]['rows'].items():
            if (tb == 'MenuCommonParam' and rid == 0 or
                tb == 'SpEffectParam' and rid == speffect_id or
                tb == 'CalcCorrectGraph' and rid == 101 or
                tb == 'EquipParamWeapon' and rid in (3140000, 8100000, 23100000) or
                tb == 'AtkParam_Pc' and rid in (*breath.keys(), 44401, 44405, 44406, 44407, 44408, 70600, 70800, 70900) or
                tb == 'ThrowParam' and rid in restored or
                tb == 'WeatherParam' and rid in weather):
                continue
            assert check[tb]['rows'][rid]['data'] == rec['data'], (tb, rid)
    for rid in restored:
        assert check['ThrowParam']['rows'][rid]['data'] == base_throw[rid]['data']

    template, _ = decrypt_official(VANILLA_REG.read_bytes())
    binary = encrypt_native(template, raw)
    assert decrypt_official(binary)[1] == raw
    (OUT / 'v06_regulation.bin').write_bytes(binary)
    (ROOT / 'changes').mkdir(exist_ok=True)
    with (ROOT / 'changes/v0.6_changes.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(('参数表', '行ID', '字段', 'v0.5', 'v0.6', '原因'))
        writer.writerows(changes)
    summary = {'version': 'v0.6-test', 'restored_throw_ids': restored,
               'softened_weather_ids': weather, 'field_changes': len(changes),
               'regulation_sha256': hashlib.sha256(binary).hexdigest()}
    (OUT / 'v06_manifest.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
