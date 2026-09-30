"""Restore Ascended's enemy base HP and area HP scaling without other changes."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import struct

from analyze_regulation import read_bnd
from build_v05 import active_rows, encrypt_native, ROOT, WORK, OUT, VANILLA_REG
from build_v04 import decrypt_official

ASCENDED = ROOT.parent / 'work/mod.bnd'
SOURCE = WORK / 'v05.bnd'
DEST = WORK / 'v05_ascended_hp.bnd'
ENCRYPTED = OUT / 'v05_pending_hp_regulation.bin'
CHANGELOG = ROOT / 'changes/v0.5_restore_ascended_hp.csv'


def main():
    _, old = read_bnd(ASCENDED)
    _, current = read_bnd(SOURCE)
    raw = bytearray(SOURCE.read_bytes())
    edits = []
    with (ROOT/'changes/v0.2.csv').open(encoding='utf-8-sig',newline='') as f:
        records = list(csv.DictReader(f))
    for category, table, field, offset, fmt in (
        ('敌人基础血量','NpcParam','hp',36,'I'),
        ('区域敌人血量','SpEffectParam','maxHpRate',16,'f'),
    ):
        rows = active_rows(raw,table)
        candidates = [r for r in records if r['改动类别']==category]
        for rec in candidates:
            assert rec['参数表']==table and rec['字段']==field
            rid=int(rec['行ID'])
            assert rid in old[table]['rows'] and rid in rows
            earlier=old[table]['rows'][rid]['data'][offset:offset+4]
            actual=current[table]['rows'][rid]['data'][offset:offset+4]
            assert earlier!=actual, (table,rid)
            assert raw[rows[rid]+offset:rows[rid]+offset+4]==actual
            raw[rows[rid]+offset:rows[rid]+offset+4]=earlier
            edits.append((category,table,rid,field,struct.unpack('<'+fmt,actual)[0],
                          struct.unpack('<'+fmt,earlier)[0]))
    assert len(edits)==1743 and len({(x[1],x[2]) for x in edits})==1743
    edited_area_ids={x[2] for x in edits if x[1]=='SpEffectParam'}
    DEST.write_bytes(raw)
    _, checked=read_bnd(DEST)
    for table in current:
        for rid,record in current[table]['rows'].items():
            result=checked[table]['rows'][rid]['data']
            if table=='NpcParam' and rid in old[table]['rows']:
                assert result[:36]==record['data'][:36] and result[40:]==record['data'][40:]
            elif table=='SpEffectParam' and rid in edited_area_ids:
                assert result[:16]==record['data'][:16] and result[20:]==record['data'][20:]
            else:
                assert result==record['data'],(table,rid)
    with CHANGELOG.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(('类别','参数表','行ID','字段','本版原值','恢复后的 Ascended 值'));w.writerows(edits)
    dcx,_=decrypt_official(VANILLA_REG.read_bytes())
    result=encrypt_native(dcx,bytes(raw))
    assert decrypt_official(result)[1]==raw
    ENCRYPTED.write_bytes(result)
    print(f'restored {len(edits)} HP fields; SHA256 {hashlib.sha256(result).hexdigest()}')


if __name__=='__main__':
    main()
