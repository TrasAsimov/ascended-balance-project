"""Restore vanilla riposte contact dimensions on every vanilla-ripostable NPC.

The official ThrowParam type-20 defender pairing is the eligibility rule. For
Ascended-only NPC rows, borrow the closest official row of the same model and
behavior variation; retain all other Ascended NPC fields and animation files.
"""
from pathlib import Path
import csv
import hashlib
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / 'work'))
from analyze_regulation import read_bnd
from field_diff import defs, fields, decode, names
from build_v04 import decrypt_official
from build_v05 import active_rows, encrypt_native

SOURCE = ROOT / 'work/v0101_starter_heart.bnd'
VANILLA = ROOT / 'work/vanilla_117.bnd'
BUILT = ROOT / 'work/v0102_riposte.bnd'
REG = ROOT / 'output/v0102_riposte_regulation.bin'
AUDIT = ROOT / 'changes/v0.10.2_all_npc_riposte_audit.csv'
ZIP_IN = ROOT / 'output/Ascended_Balance_v0.10.1_Starter_Heart_Test.zip'
ZIP_OUT = ROOT / 'output/Ascended_Balance_v0.10.2_Riposte_Test.zip'

def main():
    version, mod = read_bnd(SOURCE)
    _, vanilla = read_bnd(VANILLA)
    assert version == '11711000'
    nf = {f[0]:f for f in fields(defs()[mod['NpcParam']['ptype']])[0]}
    tf = {f[0]:f for f in fields(defs()[vanilla['ThrowParam']['ptype']])[0]}
    eligible = {decode(row['data'], tf['DefChrId']) for row in vanilla['ThrowParam']['rows'].values()
                if decode(row['data'], tf['throwType']) == 20}
    eligible.discard(0)
    raw = bytearray(SOURCE.read_bytes())
    offsets = active_rows(raw, 'NpcParam')
    official_by_model = {}
    for rid in vanilla['NpcParam']['rows']:
        official_by_model.setdefault(rid // 10000, []).append(rid)
    records = []
    npc_names = names('NpcParam')
    changed = set()
    missing = set()
    for rid, row in sorted(mod['NpcParam']['rows'].items()):
        model = rid // 10000
        original = vanilla['NpcParam']['rows'].get(rid)
        source_id = rid if original else None
        if model in eligible and original is None:
            candidates = official_by_model.get(model, [])
            same_behavior = [c for c in candidates if decode(vanilla['NpcParam']['rows'][c]['data'],nf['behaviorVariationId']) == decode(row['data'],nf['behaviorVariationId'])]
            pool = same_behavior or candidates
            if pool:
                source_id = min(pool, key=lambda c:(abs(c-rid),c))
                original = vanilla['NpcParam']['rows'][source_id]
            else:
                missing.add(model)
        before = [decode(row['data'],nf[field]) for field in ('hitHeight','hitRadius')]
        after = [decode(original['data'],nf[field]) for field in ('hitHeight','hitRadius')] if model in eligible and original else before
        for field, old, new in zip(('hitHeight','hitRadius'),before,after):
            if old != new:
                assert nf[field][1] == 'f32' and nf[field][4] is None
                # Copy the official float bytes exactly, without decimal rounding.
                pos = nf[field][2]
                raw[offsets[rid]+pos:offsets[rid]+pos+4] = original['data'][pos:pos+4]
                changed.add(rid)
        records.append((rid,npc_names.get(rid,''),model,
                        '是' if model in eligible else '否',
                        '是' if rid in vanilla['NpcParam']['rows'] else '否',
                        source_id if model in eligible else '',
                        *before,*after,'是' if rid in changed else '否',
                        '官方无处决配对，未改' if model not in eligible else
                        '官方同ID' if source_id == rid else
                        '同模型官方行映射' if source_id is not None else '待人工核查'))
    assert not missing, f'Vanilla ripostable models without an NPC base: {missing}'
    BUILT.write_bytes(raw)
    _, check = read_bnd(BUILT)
    assert len(check) == len(mod)
    for table in mod:
        for rid, row in mod[table]['rows'].items():
            got = check[table]['rows'][rid]['data']
            if table == 'NpcParam' and rid in changed:
                expected = bytearray(row['data'])
                source_id = next(rec[5] for rec in records if rec[0] == rid)
                for field in ('hitHeight','hitRadius'):
                    p = nf[field][2]
                    expected[p:p+4] = vanilla['NpcParam']['rows'][source_id]['data'][p:p+4]
                assert got == bytes(expected),(table,rid)
            else:
                assert got == row['data'],(table,rid)
    template,_ = decrypt_official((ROOT.parent/'upload/regulation.bin').read_bytes())
    encrypted = encrypt_native(template,bytes(raw))
    assert decrypt_official(encrypted)[1] == bytes(raw)
    REG.write_bytes(encrypted)
    with AUDIT.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f)
        w.writerow(('NPC行ID','名称','模型','原版有处决配对','原版有同ID行','参考原版NPC行','旧接触高度','旧接触半径','新接触高度','新接触半径','是否修复','判断'))
        w.writerows(records)
    prefix='Elden_Ascended_Mod_Age of the Endless Mod/'
    replacements={prefix+'regulation.bin',prefix+'ModEngine/mod/regulation.bin'}
    note=prefix+'Ascended_v0.10.2_处决测试说明.md'
    with zipfile.ZipFile(ZIP_IN) as src,zipfile.ZipFile(ZIP_OUT,'w') as dst:
        assert src.testzip() is None and replacements <= set(src.namelist())
        for info in src.infolist():
            dst.writestr(info,encrypted if info.filename in replacements else src.read(info))
        dst.write(ROOT/'docs/v0.10.2.md',note)
        dst.write(AUDIT,prefix+'审查清单/v0.10.2_all_npc_riposte_audit.csv')
    with zipfile.ZipFile(ZIP_OUT) as z:
        assert z.testzip() is None
        assert all(z.read(k)==encrypted for k in replacements)
    print('NPC',len(records),'eligible models',len(eligible),'changed NPC',len(changed),
          'new eligible variants',sum(r[3]=='是' and r[4]=='否' for r in records),
          'zip',ZIP_OUT.stat().st_size,hashlib.sha256(ZIP_OUT.read_bytes()).hexdigest())

if __name__=='__main__': main()
