"""Stage 21 normal remembrance attack-power multipliers at 1.025."""
from pathlib import Path
import csv
import struct
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent/'work'))
from field_diff import decode, defs, fields
from analyze_regulation import read_bnd
from build_v04 import decrypt_official
from build_v05 import active_rows, encrypt_native
from build_pending_remembrance_params import DLC_IDS, NORMAL_BASE_IDS, SPECIAL_BASE_IDS

SRC = ROOT/'work/pending_weapon_audit_fix.bnd'
OUT = ROOT/'work/pending_remembrance_attack.bnd'
REG = ROOT/'output/pending_remembrance_attack_regulation.bin'
ATTACK_FIELDS = ('physicsAttackPowerRate', 'magicAttackPowerRate',
                 'fireAttackPowerRate', 'thunderAttackPowerRate', 'darkAttackPowerRate')
SPECIAL_EFFECTS = (3720, 3721, 3724, 3729)

def main():
    _, before = read_bnd(SRC)
    raw = bytearray(SRC.read_bytes())
    goods = before['EquipParamGoods']['rows']
    effects = before['SpEffectParam']['rows']
    gf = {x[0]:x for x in fields(defs()[before['EquipParamGoods']['ptype']])[0]}
    sf = {x[0]:x for x in fields(defs()[before['SpEffectParam']['ptype']])[0]}
    offsets = active_rows(raw, 'SpEffectParam')
    normal_goods = NORMAL_BASE_IDS + DLC_IDS
    assert len(normal_goods) == len(set(normal_goods)) == 21
    assert tuple(decode(goods[rid]['data'], gf['refId_default']) for rid in SPECIAL_BASE_IDS) == SPECIAL_EFFECTS
    linked = {rid:decode(goods[rid]['data'], gf['refId_default']) for rid in normal_goods}
    assert len(set(linked.values())) == 21
    assert set(linked.values()) == set(range(321412,321422))|set(range(321424,321435))
    log = []
    for good,eid in linked.items():
        row = effects[eid]['data']
        assert decode(row,sf['maxHpRate']) == 1.05
        assert decode(row,sf['maxMpRate']) == decode(row,sf['maxStaminaRate']) == 1.0
        for name in ATTACK_FIELDS:
            field = sf[name]
            assert field[1] == 'f32' and field[4] is None
            old = decode(row,field)
            assert old == 1.05, (good,eid,name,old)
            struct.pack_into('<f',raw,offsets[eid]+field[2],1.025)
            log.append((good,eid,name,old,1.025))
    OUT.write_bytes(raw)
    version, after = read_bnd(OUT)
    assert version == '11711000'
    for table in before:
        for rid,rec in before[table]['rows'].items():
            if table == 'SpEffectParam' and rid in linked.values():
                expected = bytearray(rec['data'])
                for name in ATTACK_FIELDS:
                    struct.pack_into('<f',expected,sf[name][2],1.025)
                assert after[table]['rows'][rid]['data'] == expected
            else:
                assert after[table]['rows'][rid]['data'] == rec['data'], (table,rid)
    for good,eid in linked.items():
        row = after['SpEffectParam']['rows'][eid]['data']
        assert abs(decode(row,sf['maxHpRate'])-1.05)<1e-6
        assert all(abs(decode(row,sf[name])-1.025)<1e-6 for name in ATTACK_FIELDS)
    template,_ = decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
    encrypted = encrypt_native(template,bytes(raw))
    assert decrypt_official(encrypted)[1] == bytes(raw)
    REG.write_bytes(encrypted)
    with (ROOT/'changes/pending_remembrance_attack.csv').open('w',encoding='utf-8-sig',newline='') as fh:
        writer=csv.writer(fh)
        writer.writerow(('追忆道具ID','效果ID','攻击力字段','旧倍率','新倍率'))
        writer.writerows(log)
    print('normal remembrances:',len(linked),'attack fields:',len(log),
          'special untouched:',SPECIAL_BASE_IDS)

if __name__ == '__main__':
    main()
