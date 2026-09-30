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
                              (12, 'playerMaxMpLimit', 4),
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
            if tb == 'MenuCommonParam' and rid == 0 or tb == 'SpEffectParam' and rid == speffect_id or tb == 'ThrowParam' and rid in restored or tb == 'WeatherParam' and rid in weather:
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
