"""Keep Ascended talisman identities while reconciling known effect mismatches.

Source is v0.5 with the author's enemy HP restored. English descriptions are
patched separately by build_v05_messages.py from the author's DLC02 FMGs.
"""
from pathlib import Path
import csv
import struct
import sys

from analyze_regulation import read_bnd
from build_v05 import active_rows, encrypt_native, ROOT, WORK, OUT, VANILLA_REG
from build_v04 import decrypt_official

sys.path.insert(0, str(ROOT.parent/'work'))
from field_diff import defs, fields, decode

SOURCE=WORK/'v05_ascended_hp.bnd'
TARGET=WORK/'v05_reconciled.bnd'
ENCRYPTED=OUT/'v05_reconciled_regulation.bin'


def main():
    _, tables=read_bnd(SOURCE)
    data=bytearray(SOURCE.read_bytes())
    entries=tables['EquipParamAccessory']['rows']
    effects=tables['SpEffectParam']['rows']
    offsets=active_rows(data,'SpEffectParam')
    fs,size=fields(defs()[tables['SpEffectParam']['ptype']])
    field_by_name={f[0]:f for f in fs}
    changes=[]
    def update(item_id,name,field,new,reason):
        effect_id=struct.unpack_from('<i',entries[item_id]['data'],4)[0]
        f=field_by_name[field]
        typ=f[1];offset=f[2]
        assert f[4] is None and f[6]==1
        before=decode(data[offsets[effect_id]:offsets[effect_id]+size],f)
        fmt={'f32':'f','s32':'i'}[typ]
        if isinstance(new,float):assert typ=='f32'
        assert before!=new,(item_id,field)
        struct.pack_into('<'+fmt,data,offsets[effect_id]+offset,new)
        changes.append((item_id,name,effect_id,field,before,new,reason))
    # The author's Magic Talisman is the former Lance Talisman and claims
    # +300% spell damage. Its five attack-power coefficients were 5.0 (+400%).
    for field in ('physicsAttackPowerRate','magicAttackPowerRate',
                  'fireAttackPowerRate','thunderAttackPowerRate','darkAttackPowerRate'):
        update(2140,'Magic Talisman',field,4.0,'说明目标为 +300%，倍率对应 4.0')
    # Bull-Goat's caption promises poise +25%; the v0.2 data had cleared
    # the original 0.75 incoming poise-damage factor.
    update(1210,"Bull-Goat's Talisman",'toughnessDamageCutRate',0.75,
           '恢复护符实际韧性提升')
    # Greatshield's Ascended damage-cut values of 1.2 increase incoming
    # damage even when not guarding. Keep the guard identity and describe
    # its actual stamina effect, without claiming unconditional protection.
    for field in ('slashDamageCutRate','blowDamageCutRate','thrustDamageCutRate',
                  'neutralDamageCutRate','magicDamageCutRate','fireDamageCutRate',
                  'thunderDamageCutRate','darkDamageCutRate'):
        update(4100,'Greatshield Talisman',field,1.0,
               '移除全时生效的额外受伤，保留护盾定位')
    update(4100,'Greatshield Talisman','guardStaminaCutRate',0.9,
           '格挡精力消耗降低 10%')
    update(6010,'Concealing Veil','sightSearchEnemyRate',1.0,
           '移除提高敌人视觉察觉率的异常值')
    update(6010,'Concealing Veil','hearingSearchEnemyRate',1.0,
           '移除提高敌人听觉察觉率的异常值')
    TARGET.write_bytes(data)
    _,check=read_bnd(TARGET)
    edited={x[2] for x in changes}
    for rid,rec in effects.items():
        if rid not in edited:
            assert check['SpEffectParam']['rows'][rid]['data']==rec['data']
    for table in tables:
        if table!='SpEffectParam':
            assert check[table]['rows']==tables[table]['rows']
    dcx,_=decrypt_official(VANILLA_REG.read_bytes())
    binary=encrypt_native(dcx,bytes(data))
    assert decrypt_official(binary)[1]==data
    ENCRYPTED.write_bytes(binary)
    with (ROOT/'changes/v0.5_talisman_reconciliation.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(('护符ID','护符名','效果ID','字段','改前','改后','理由'));w.writerows(changes)
    print('edited fields',len(changes),'effects',len(edited),'regulation bytes',len(binary))


if __name__=='__main__':
    main()
