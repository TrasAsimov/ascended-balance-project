"""Add an isolated +40% skill effect to Alexander; set player HP curve to x2.5."""
import argparse
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from disable_player_debuffs import unpack
from build_minor_boss_heart import pack_regulation
from analyze_regulation import read_param
from field_diff import fields, decode
from formats import bnd_entries, bnd_repack, param_patch, dcx_unpack, dcx_pack, bnd_patch
from fmg import fmg_read, fmg_write

ACCESSORY = 1231
PRIMARY = 312310
SKILL_EFFECT = 78212310
RATES = ('physicsAttackRate','magicAttackRate','fireAttackRate','thunderAttackRate','darkAttackRate')
INFO = 'Increases skill damage by 40%.'
CAPTION = ('Shard of the late Alexander, a shattered warrior jar.\n\n'
           'Effect: Increases skill damage by 40%.\n'
           'Effect: Increases defense by 500 and application of status to enemies by 200.\n\n'
           'Scraps of stewed flesh cling to the shard, and tatters of ornaments can be seen '
           'mingled within the slime. Relics of a red-haired champion, it would seem.')

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def patch(raw, official, defs):
    parts = bnd_entries(raw)
    original = bnd_entries(official)
    assert len(parts)==194 and raw[24:32]==official[24:32]==b'11711000'
    tables = {}; vanilla = {}; maps = {}; sizes = {}
    for table,filename in [('EquipParamAccessory','EquipParamAccessory'),
                           ('SpEffectParam','SpEffect'),('CalcCorrectGraph','CalcCorrectGraph')]:
        layout,size = fields(defs/(filename+'.xml'))
        tables[table] = read_param(parts[table+'.param'][1],table)
        vanilla[table] = read_param(original[table+'.param'][1],table)
        assert size==tables[table]['row_size']==vanilla[table]['row_size'],table
        maps[table] = {f[0]:f for f in layout}; sizes[table] = size
    def get(table,rid,field,source=tables):
        return decode(source[table]['rows'][rid]['data'],maps[table][field])
    def put(body,table,field,value):
        f = maps[table][field]
        fmt = {'f32':'f','s32':'i'}[f[1]]
        assert f[4] is None and f[6]==1
        struct.pack_into('<'+fmt,body,f[2],value)
    assert get('EquipParamAccessory',ACCESSORY,'refId')==PRIMARY
    # Native skill selectors and an otherwise neutral official effect are retained.
    skill = bytearray(vanilla['SpEffectParam']['rows'][PRIMARY]['data'])
    assert get('SpEffectParam',PRIMARY,'magicSubCategoryChange1',vanilla)==112
    assert get('SpEffectParam',PRIMARY,'magicSubCategoryChange2',vanilla)==111
    for field in RATES:
        assert abs(get('SpEffectParam',PRIMARY,field,vanilla)-1.15)<0.000001
        put(skill,'SpEffectParam',field,1.4)
    skill = bytes(skill)
    resident = bytearray(tables['EquipParamAccessory']['rows'][ACCESSORY]['data'])
    slots = ['residentSpEffectId'+str(i) for i in range(1,5)]
    occupied = [s for s in slots if get('EquipParamAccessory',ACCESSORY,s)==SKILL_EFFECT]
    assert len(occupied)<=1
    slot = occupied[0] if occupied else next((s for s in slots if get('EquipParamAccessory',ACCESSORY,s) in (0,-1)),None)
    assert slot is not None,'No free accessory resident slot; do not overwrite existing effects'
    put(resident,'EquipParamAccessory',slot,SKILL_EFFECT)
    added = {}
    if SKILL_EFFECT in tables['SpEffectParam']['rows']:
        assert tables['SpEffectParam']['rows'][SKILL_EFFECT]['data']==skill,'Private effect collision'
    else:
        added[SKILL_EFFECT] = skill
    curve = bytearray(tables['CalcCorrectGraph']['rows'][100]['data'])
    hp_changes = []
    for i in range(5):
        field = 'stageMaxGrowVal'+str(i)
        baseline = get('CalcCorrectGraph',100,field,vanilla)
        current = get('CalcCorrectGraph',100,field)
        assert current in (baseline*2,baseline*2.5),(field,current,baseline)
        put(curve,'CalcCorrectGraph',field,baseline*2.5)
        hp_changes.append({'field':field,'official':baseline,'before':current,'after':baseline*2.5,
                           'vigor':get('CalcCorrectGraph',100,'stageMaxVal'+str(i))})
    # The existing universal effect is neutral for HP: do not multiply the new curve again.
    assert get('SpEffectParam',6202065,'maxHpRate')==1.0
    updates = {}
    expected = {'EquipParamAccessory':{ACCESSORY:bytes(resident)},'CalcCorrectGraph':{100:bytes(curve)}}
    for table,changes in expected.items():
        if any(tables[table]['rows'][rid]['data']!=body for rid,body in changes.items()):
            updates[table+'.param'] = param_patch(parts[table+'.param'][1],changes,{},sizes[table])
    if added:
        updates['SpEffectParam.param'] = param_patch(parts['SpEffectParam.param'][1],{},added,sizes['SpEffectParam'])
    result = bnd_repack(raw,updates) if updates else raw
    checked = bnd_entries(result)
    for name,(_,body) in parts.items():
        if name not in updates:
            assert checked[name][1]==body,name
    for table in tables:
        after = read_param(checked[table+'.param'][1],table)
        for rid,record in tables[table]['rows'].items():
            target = expected.get(table,{}).get(rid,record['data'])
            assert after['rows'][rid]['data']==target and after['rows'][rid]['name']==record['name'],(table,rid)
        if table=='SpEffectParam':
            assert after['rows'][SKILL_EFFECT]['data']==skill
        else:
            assert after['rows'].keys()==tables[table]['rows'].keys()
    # Whitelist: 4 bytes in the accessory; only 5 curve growth floats.
    offset = maps['EquipParamAccessory'][slot][2]
    original_resident = tables['EquipParamAccessory']['rows'][ACCESSORY]['data']
    assert resident[:offset]==original_resident[:offset] and resident[offset+4:]==original_resident[offset+4:]
    allowed = {maps['CalcCorrectGraph']['stageMaxGrowVal'+str(i)][2]+j for i in range(5) for j in range(4)}
    old_curve = tables['CalcCorrectGraph']['rows'][100]['data']
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(old_curve,curve)))
    report = {'accessory_id':ACCESSORY,'unchanged_primary_effect':PRIMARY,
              'added_skill_effect':SKILL_EFFECT,'resident_slot':slot,
              'skill_damage_multiplier':1.4,'skill_selectors':[112,111],
              'native_skill_template':'official 1.17.1 SpEffect 312310',
              'existing_defense_and_status_bonuses':'preserved byte-for-byte',
              'hp_graph_id':100,'hp_changes':hp_changes,'global_max_hp_rate':1.0,
              'other_tables_unchanged':191,'all_existing_speffect_rows_unchanged':True,
              'hp_curve_knots_and_shape_unchanged':True,'npc_params_unchanged':True,
              'changed_members':sorted(updates),'game_tested':False}
    return result,report

def patch_text(blob):
    parts = bnd_entries(dcx_unpack(blob)); updates = {}; before = {}; changed = []
    for name,text in [('AccessoryInfo.fmg',INFO),('AccessoryCaption.fmg',CAPTION)]:
        entries = fmg_read(parts[name][1]);before[name] = dict(entries)
        assert ACCESSORY in entries
        if entries[ACCESSORY]!=text:
            entries[ACCESSORY] = text;updates[name] = fmg_write(entries);changed.append(name)
    if not updates:
        return blob,[]
    result = dcx_pack(bnd_patch(dcx_unpack(blob),updates));after = bnd_entries(dcx_unpack(result))
    for name,(_,body) in parts.items():
        if name not in updates:
            assert after[name][1]==body,name
    for name,text in [('AccessoryInfo.fmg',INFO),('AccessoryCaption.fmg',CAPTION)]:
        entries = fmg_read(after[name][1]);assert entries.keys()==before[name].keys()
        assert all(entries[k]==v for k,v in before[name].items() if k!=ACCESSORY)
        assert entries[ACCESSORY]==text
    return result,changed

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--regulation',type=Path,required=True)
    parser.add_argument('--official-bnd',type=Path,required=True)
    parser.add_argument('--paramdefs',type=Path,required=True)
    parser.add_argument('--item-bnd',type=Path,action='append',default=[])
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    key = bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    source = args.regulation.read_bytes();header,raw = unpack(source,key)
    result,report = patch(raw,args.official_bnd.read_bytes(),args.paramdefs)
    assert patch(result,args.official_bnd.read_bytes(),args.paramdefs)[0]==result
    blob = source if result==raw else pack_regulation(header,result,key)
    assert unpack(blob,key)[1]==result
    prefix = '01_Alexander40_HP250_20261002'
    reg = args.output/(prefix+'_regulation.bin');reg.write_bytes(blob)
    report.update(input_sha256=sha(source),output_sha256=sha(blob),output_bytes=len(blob),
                  idempotent=True,encrypted_roundtrip=True,texts=[])
    for path in args.item_bnd:
        text = path.read_bytes();changed,names = patch_text(text)
        assert patch_text(changed)[0]==changed
        suffix = 'item_dlc01.msgbnd.dcx' if 'dlc01' in path.name else 'item_dlc02.msgbnd.dcx'
        target = args.output/(prefix+'_engus_'+suffix);target.write_bytes(changed)
        report['texts'].append({'input':path.name,'input_sha256':sha(text),
                                'output':target.name,'output_sha256':sha(changed),'changed_fmgs':names,
                                'accessory_id':ACCESSORY,'non_target_entries_preserved':True,'idempotent':True})
    chinese = {'status':'merge source; not an installable zhocn archive','accessory_id':ACCESSORY,
               'info':'战技伤害增加40%。',
               'caption':'效果：战技伤害增加40%。\n效果：防御增加500，对敌人施加的异常累积增加200。',
               'player_hp_note':'玩家基础生命成长由原版的2倍提高到2.5倍；相对当前基础血量增加25%。'}
    (args.output/(prefix+'_description_zh.json')).write_text(json.dumps(chinese,ensure_ascii=False,indent=2)+'\n')
    (args.output/(prefix+'_audit.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'sha256':sha(blob),'bytes':len(blob),'changed_members':report['changed_members'],
                      'skill_multiplier':1.4,'hp_99':5250},ensure_ascii=False))

if __name__=='__main__':
    main()
