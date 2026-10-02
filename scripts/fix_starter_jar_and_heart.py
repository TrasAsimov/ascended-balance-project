"""Stage local fixes on the latest integrated inputs; no packaging/publication.

Run after class/loadout, remembrance, jar-shard and keepsake modules. Supply
matching Paramdex definitions and EMEDF; the key is read only from environment.
"""
import argparse
import json
import os
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--regulation', type=Path, required=True)
    p.add_argument('--common', type=Path, required=True)
    p.add_argument('--engus', type=Path, required=True)
    p.add_argument('--paramdefs', type=Path, required=True)
    p.add_argument('--emedf', type=Path, required=True)
    p.add_argument('--eventparam', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    os.environ['ARMOR_PARAMDEFS'] = str(a.paramdefs.resolve())
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root/'scripts'),str(root/'systems/armor/scripts')]
    from build_minor_boss_heart import (unpack, sha, load_manifest, patch_params,
        patch_event, pack_regulation, COUNTER_START, COUNTER_BITS, PHYSICAL_POWER)
    from revise_new_class_builds import patch as class_patch, LIGHT_ROWS, HEAVY_ROWS
    from update_minor_boss_heart_text import patch as text_patch, HEART_ID, TEXT, ZH
    from verify_minor_boss_heart import allocations
    from formats import bnd_entries, dcx_unpack, Emevd
    from analyze_regulation import read_param
    from field_diff import defs, fields, decode
    from verify_layout import directory

    ranges = allocations(a.eventparam)
    assert all(any(lo <= f < hi for lo,hi in ranges)
               for f in range(COUNTER_START,COUNTER_START+COUNTER_BITS))
    manifest = load_manifest(root/'data/minor_boss_heart.json')
    source = a.regulation.read_bytes()
    common = a.common.read_bytes()
    key = bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    header, raw = unpack(source,key)
    sp_definition = defs()[read_param(bnd_entries(raw)['SpEffectParam.param'][1],'SpEffectParam')['ptype']]
    heart_raw, layout, expected = patch_params(raw,sp_definition,181)
    result_raw, class_audit = class_patch(heart_raw)
    new_common, extra, prefix = patch_event(common,manifest,a.emedf)
    assert len(prefix) == 72
    assert patch_params(result_raw,sp_definition,181)[0] == result_raw
    assert class_patch(result_raw)[0] == result_raw
    assert patch_event(new_common,manifest,a.emedf)[0] == new_common

    before, after = bnd_entries(raw), bnd_entries(result_raw)
    changed_tables = [k for k in before if before[k][1] != after[k][1]]
    assert set(changed_tables) <= {'CharaInitParam.param','SpEffectParam.param'}
    actual_rows = {}
    for t in ('CharaInitParam','SpEffectParam'):
        old = read_param(before[t+'.param'][1],t)
        new = read_param(after[t+'.param'][1],t)
        fs,size = fields(defs()[old['ptype']])
        fl = {f[0]:f for f in fs}
        old_dir,old_end = directory(before[t+'.param'][1],size)
        new_dir,new_end = directory(after[t+'.param'][1],size)
        assert old_dir.keys() == new_dir.keys() and old_end == new_end
        actual_rows[t] = []
        for rid,row in old['rows'].items():
            assert new['rows'][rid]['name'] == row['name']
            assert new_dir[rid][:3] == old_dir[rid][:3]
            if new['rows'][rid]['data'] == row['data']:
                continue
            allowed = (['equip_Accessory01'] if t == 'CharaInitParam' else PHYSICAL_POWER)
            assert rid in (LIGHT_ROWS+HEAVY_ROWS if t == 'CharaInitParam' else range(7400001,7400182))
            byte_offsets = {i for k in allowed for i in range(fl[k][2],fl[k][2]+fl[k][3])}
            assert all(i in byte_offsets for i,(x,y) in enumerate(zip(row['data'],new['rows'][rid]['data'])) if x != y)
            actual_rows[t].append({'id':rid,'fields':{
                k:{'before':decode(row['data'],fl[k]),'after':decode(new['rows'][rid]['data'],fl[k])}
                for k in allowed if decode(row['data'],fl[k]) != decode(new['rows'][rid]['data'],fl[k])}})
    # The fixed class reference resolves to the already-approved +40% small shard.
    acc = read_param(after['EquipParamAccessory.param'][1],'EquipParamAccessory')
    af = {f[0]:f for f in fields(defs()[acc['ptype']])[0]}
    assert decode(acc['rows'][1230]['data'],af['refId']) == 312300
    sp = read_param(after['SpEffectParam.param'][1],'SpEffectParam')
    for k in ('physicsAttackRate','magicAttackRate','fireAttackRate','thunderAttackRate','darkAttackRate'):
        assert abs(decode(sp['rows'][312300]['data'],layout[k])-1.4) < 1e-6
    assert Emevd(dcx_unpack(common)).linked == Emevd(dcx_unpack(new_common)).linked
    a.output.mkdir(parents=True,exist_ok=True)
    reg = pack_regulation(header,result_raw,key)
    files = {'regulation.bin':reg,'common.emevd.dcx':new_common}
    text_inputs = {}
    for name in ('item_dlc01.msgbnd.dcx','item_dlc02.msgbnd.dcx'):
        original = (a.engus/name).read_bytes()
        text_inputs[name] = sha(original)
        changed = text_patch(original)
        assert text_patch(changed) == changed
        files['engus_'+name] = changed
    for name,data in files.items():
        (a.output/name).write_bytes(data)
    zh = {'goods_id':HEART_ID,'text':ZH,'status':'merge source; not a zhocn runtime archive'}
    (a.output/'heart_description_zh.json').write_text(json.dumps(zh,ensure_ascii=False,indent=2)+'\n')
    audit = {
        'input_regulation_sha256':sha(source),'input_common_sha256':sha(common),
        'input_engus_sha256':text_inputs,
        'output_files':{k:{'sha256':sha(v),'bytes':len(v)} for k,v in files.items()},
        'param_changes':actual_rows,'changed_tables':changed_tables,
        'other_param_table_payloads_preserved':194-len(changed_tables),
        'class_accessories':class_audit['accessories'],
        'small_jar_shard_skill_multiplier':1.4,
        'counter_flags':[COUNTER_START,COUNTER_START+COUNTER_BITS-1],
        'counter_allocated_in_EFID_common':True,'eventparam_sha256':sha(a.eventparam.read_bytes()),
        'heart_event':20007902,'preserved_prefix_instructions':len(prefix),
        'extension_instructions':len(extra),'other_events_preserved':True,
        'minor_boss_encounters':181,'minor_resource_per_encounter':.002,
        'minor_attack_and_spell_per_encounter':.001,
        'minor_resource_cap':1.362,'minor_attack_and_spell_cap':1.181,
        'bayle_and_original_remembrance_logic_preserved':True,
        'message_changes':{'id':HEART_ID,'fmgs':list(TEXT)},
        'idempotence':True,'encrypted_roundtrip':True,
        'latest_inventory_keepsakes_hp_and_armor_preserved':True,
        'game_validation':'not run','package_created':False,'published':False}
    (a.output/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'files':audit['output_files'],'changed_row_counts':{k:len(v) for k,v in actual_rows.items()},
                      'game_validation':audit['game_validation']},ensure_ascii=False))


if __name__ == '__main__':
    main()
