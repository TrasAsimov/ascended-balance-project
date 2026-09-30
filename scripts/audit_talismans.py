"""Inventory every talisman and its directly referenced effect against vanilla.

Run after build_v05.py. An effect may point to additional effects; this CSV is
an inventory of direct references, not a complete gameplay damage simulation.
"""
from __future__ import annotations

import csv
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_regulation import read_bnd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / 'work'))
from field_diff import defs, fields, decode, names


def main():
    _, mod = read_bnd(ROOT / 'work/v05.bnd')
    _, vanilla = read_bnd(ROOT / 'work/v05_official.bnd')
    accessories = mod['EquipParamAccessory']['rows']
    base_accessories = vanilla['EquipParamAccessory']['rows']
    effects = mod['SpEffectParam']['rows']
    base_effects = vanilla['SpEffectParam']['rows']
    effect_fields, size = fields(defs()[mod['SpEffectParam']['ptype']])
    assert size == mod['SpEffectParam']['row_size'] == vanilla['SpEffectParam']['row_size']
    names_by_id = names('EquipParamAccessory')
    out = ROOT / 'changes/v0.5_talisman_audit.csv'
    with out.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(('护符ID', '护符名', '效果ID', '原版效果ID', '字段', '当前值',
                         '官方1.17.1值', '分类'))
        for aid, item in sorted(accessories.items()):
            eid = struct.unpack_from('<i', item['data'], 4)[0]
            base_item = base_accessories.get(aid)
            base_eid = struct.unpack_from('<i', base_item['data'], 4)[0] if base_item else None
            name = names_by_id.get(aid, '')
            if eid not in effects:
                writer.writerow((aid, name, eid, base_eid, '', '', '', '效果行缺失'))
                continue
            base = base_effects.get(base_eid) if base_eid is not None else None
            if base is None:
                writer.writerow((aid, name, eid, base_eid, '', '', '', '原版无对应效果'))
                continue
            changed = False
            for fld in effect_fields:
                a = decode(effects[eid]['data'], fld)
                b = decode(base['data'], fld)
                if a != b:
                    writer.writerow((aid, name, eid, base_eid, fld[0], a, b, '效果差异'))
                    changed = True
            if not changed:
                writer.writerow((aid, name, eid, base_eid, '', '', '', '直接效果同原版'))
    print(out)


if __name__ == '__main__':
    main()
