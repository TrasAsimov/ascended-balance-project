"""Stage spell-only damage companions for normal remembrance bonuses.

Each permanent remembrance effect emits a short-lived spell-only effect,
following the vanilla Erdtree's Favor / Primal Glintstone Blade parent-child
pattern. Gameplay still needs controlled damage tests before release.
"""
from __future__ import annotations

from pathlib import Path
import csv
import struct
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / 'work'))
from analyze_regulation import read_bnd
from field_diff import decode, defs, fields
from build_v03 import binder_headers
from build_v04 import decrypt_official
from build_v05 import encrypt_native

SOURCE = ROOT / 'work/pending_heart_marker.bnd'
OUT = ROOT / 'work/pending_spell_boss_bonus.bnd'
REG = ROOT / 'output/pending_spell_boss_bonus_regulation.bin'
NORMAL = tuple(range(321412, 321422)) + tuple(range(321424, 321435))
CHILD = {eid: 321435 + i for i, eid in enumerate(NORMAL)}
RATES = ('physicsAttackRate', 'magicAttackRate', 'fireAttackRate',
         'thunderAttackRate', 'darkAttackRate')


def rewrite_param(source: bytes, old, vanilla):
    """Insert sorted 64-bit PARAM row pointers and append their row data."""
    f = {x[0]: x for x in fields(defs()[old['ptype']])[0]}
    assert old['flags'] & 0x84 == 0x84 and source[0x2e] & 4
    count = struct.unpack_from('<H', source, 0xA)[0]
    assert count == old['declared_rows']
    delta = 24 * len(NORMAL)
    table_end = 0x40 + count * 24
    assert struct.unpack_from('<Q', source, 0x30)[0] == table_end
    entries = [struct.unpack_from('<iIQQ', source, 0x40 + i * 24) for i in range(count)]
    assert len({e[0] for e in entries}) == count
    assert [e[0] for e in entries] == sorted(e[0] for e in entries)
    assert not set(CHILD.values()) & set(old['rows'])

    # Patch only the existing 21 parent rows, before shifting the row directory.
    raw = bytearray(source)
    log = []
    offsets = {rid:off for rid,_,off,_ in entries}
    for eid, child in CHILD.items():
        row = old['rows'][eid]['data']
        assert decode(row,f['cycleOccurrenceSpEffectId']) == -1
        assert decode(row,f['motionInterval']) == 0.0
        struct.pack_into('<i', raw, offsets[eid]+f['cycleOccurrenceSpEffectId'][2], child)
        struct.pack_into('<f', raw, offsets[eid]+f['motionInterval'][2], 0.06)
        log.append((eid,child))

    # Vanilla Graven-School is known to affect sorceries only. Its self-only
    # wepParamChange=3 and magic flag provide the selective spell template.
    template = vanilla['rows'][330000]['data']
    assert len(template) == old['row_size']
    assert decode(template,f['wepParamChange']) == 3
    assert decode(template,f['magParamChange']) == 1
    assert decode(template,f['miracleParamChange']) == 0
    children = {}
    for eid,child in CHILD.items():
        row = bytearray(template)
        struct.pack_into('<i',row,f['iconId'][2],-1)
        struct.pack_into('<f',row,f['effectEndurance'][2],0.1)
        for field in RATES:
            struct.pack_into('<f',row,f[field][2],1.025)
        bit=f['miracleParamChange']
        assert bit[1]=='u8' and bit[4]==1
        row[bit[2]] |= 1 << bit[5]
        assert decode(row,f['maxHpRate']) == 1.0
        assert decode(row,f['physicsAttackPowerRate']) == 1.0
        assert decode(row,f['magParamChange']) == decode(row,f['miracleParamChange']) == 1
        children[child]=bytes(row)

    # Existing offsets point inside this member; its pointer array grows by
    # delta bytes. New data lives after all existing strings and row data.
    result = bytearray(raw[:0x40])
    struct.pack_into('<I', result, 0x0, struct.unpack_from('<I',raw,0x0)[0]+delta)
    struct.pack_into('<H', result, 0xA, count+len(children))
    struct.pack_into('<Q', result, 0x10, struct.unpack_from('<Q',raw,0x10)[0]+delta)
    struct.pack_into('<Q', result, 0x30, table_end+delta)
    new_entries = [(rid,pad,off+delta if off else 0,name+delta if name else 0)
                   for rid,pad,off,name in entries]
    for child in children:
        new_entries.append((child,0,len(raw)+delta+(child-321435)*old['row_size'],0))
    new_entries.sort(key=lambda e:e[0])
    for item in new_entries:
        result.extend(struct.pack('<iIQQ',*item))
    assert len(result) == table_end+delta
    result.extend(raw[table_end:])
    for child in sorted(children):result.extend(children[child])
    assert len(result) == len(source)+delta+len(children)*old['row_size']
    return bytes(result),log,children,f


def main():
    raw=SOURCE.read_bytes()
    version,before=read_bnd(SOURCE)
    assert version=='11711000'
    _,van=read_bnd(ROOT/'work/vanilla_117.bnd')
    headers=binder_headers(raw)
    _,sp_off,sp_size=headers['SpEffectParam']
    member,log,children,f = rewrite_param(
        raw[sp_off:sp_off+sp_size],
        before['SpEffectParam'],van['SpEffectParam'])
    first=min(info[1] for info in headers.values())
    result=bytearray(raw[:first])
    count=struct.unpack_from('<I',raw,12)[0]
    assert count==len(before)==194
    for i in range(count):
        head=0x40+i*36
        _,_,size,uncompressed,old_off,_,_=struct.unpack_from('<IIQQIII',raw,head)
        assert size==uncompressed
        while len(result)%16:result.append(0)
        new_off=len(result)
        old_member=raw[old_off:old_off+size]
        # Use binder entry identity; other param byte blobs are copied exactly.
        if head==headers['SpEffectParam'][0]:
            result.extend(member)
            new_size=len(member)
        else:
            result.extend(old_member)
            new_size=size
        struct.pack_into('<QQI',result,head+8,new_size,new_size,new_off)
    OUT.write_bytes(result)
    mv,after=read_bnd(OUT)
    assert mv==version
    assert set(after)==set(before)
    assert set(after['SpEffectParam']['rows'])-set(before['SpEffectParam']['rows'])==set(children)
    for table in before:
        for rid,rec in before[table]['rows'].items():
            got=after[table]['rows'][rid]['data']
            if table=='SpEffectParam' and rid in CHILD:
                expected=bytearray(rec['data'])
                struct.pack_into('<i',expected,f['cycleOccurrenceSpEffectId'][2],CHILD[rid])
                struct.pack_into('<f',expected,f['motionInterval'][2],0.06)
                assert got==expected,(table,rid)
            else:assert got==rec['data'],(table,rid)
    for eid,child in log:
        assert after['SpEffectParam']['rows'][child]['data']==children[child]
    template,_=decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
    encrypted=encrypt_native(template,bytes(result))
    assert decrypt_official(encrypted)[1]==bytes(result)
    REG.write_bytes(encrypted)
    with (ROOT/'changes/pending_spell_boss_bonus.csv').open('w',encoding='utf-8-sig',newline='') as fh:
        w=csv.writer(fh);w.writerow(('追忆效果ID','法术专用子效果ID','倍率','状态'))
        w.writerows((eid,child,1.025,'待游戏验证') for eid,child in log)
    print('staged',len(log),'normal remembrances with spell-only child effects')

if __name__=='__main__':main()
