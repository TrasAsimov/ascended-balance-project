"""Upgrade-dependent physical melee AR; private copies leave caster tables intact."""
import argparse
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'systems/armor/scripts'))
from analyze_regulation import read_param
from disable_player_debuffs import unpack
from build_minor_boss_heart import pack_regulation
from formats import bnd_entries, bnd_repack, param_patch, dcx_unpack
from field_diff import fields, decode
from fmg import fmg_read

# Fixed mapping allows repeat application without multiplying already boosted rows.
SOURCE_GROUPS = tuple(range(0, 1300, 100)) + (2200, 5000, 6000)
TIERS = (
    ('small', 1.50, (1, 35, 37, 88, 91, 95)),
    ('standard', 1.65, (3, 9, 13, 14, 15, 17, 21, 24, 25, 39, 92)),
    ('medium', 1.75, (16, 28, 90, 93)),
    ('heavy', 1.80, (5, 11, 19, 23, 29, 31, 94)),
    ('colossal', 5000.0 / 2649.85875, (7, 41)),
    ('ghiza_wheel', 2800.0 / 2147.964, ()),
    ('serpent_fixed', 1.0, ()),
)
TYPE_TIER = {kind:i for i,(_,_,kinds) in enumerate(TIERS) for kind in kinds}
STATS = (('Strength','Strength'), ('Dexterity','Agility'),
         ('Magic','Magic'), ('Faith','Faith'), ('Luck','Luck'))

def private_id(tier, source):
    return 10000 + tier*2000 + SOURCE_GROUPS.index(source)*100

def source_id(pointer, tier):
    if pointer in SOURCE_GROUPS:
        return pointer
    start = 10000 + tier*2000
    idx, remainder = divmod(pointer-start, 100)
    assert remainder == 0 and 0 <= idx < len(SOURCE_GROUPS), ('unknown reinforcement', pointer, tier)
    return SOURCE_GROUPS[idx]

def context(raw, defs):
    parts = bnd_entries(raw)
    kinds = ('EquipParamWeapon','ReinforceParamWeapon','CalcCorrectGraph','AttackElementCorrectParam')
    tables = {t:read_param(parts[t+'.param'][1], t) for t in kinds}
    maps = {}
    for t in kinds:
        layout,size = fields(defs/(t+'.xml'))
        assert size == tables[t]['row_size'], (t,size,tables[t]['row_size'])
        maps[t] = {f[0]:f for f in layout}
    return parts,tables,maps

def value(tables, maps, table, rid, field):
    return decode(tables[table]['rows'][rid]['data'],maps[table][field])

def physical_ar(tables, maps, rid, reinforcement, stat=99):
    v = lambda t,r,f:value(tables,maps,t,r,f)
    w = lambda f:v('EquipParamWeapon',rid,f)
    r = lambda f:v('ReinforceParamWeapon',reinforcement,f)
    graph = w('correctType_Physics')
    xs = [v('CalcCorrectGraph',graph,'stageMaxVal'+str(i)) for i in range(5)]
    ys = [v('CalcCorrectGraph',graph,'stageMaxGrowVal'+str(i)) for i in range(5)]
    # This report uses max-stat endpoints; no approximation of intermediate curves.
    assert stat == 99 and xs[-1] == 99, ('unsupported model graph',graph,xs)
    growth = ys[-1]/100
    aec = w('attackElementCorrectId')
    bonus = 0.0
    for engine,weapon in STATS:
        if v('AttackElementCorrectParam',aec,'is'+engine+'Correct_byPhysics'):
            coefficient = v('AttackElementCorrectParam',aec,'overwrite'+engine+'CorrectRate_byPhysics')
            if coefficient < 0:
                coefficient = w('correct'+weapon)
            bonus += coefficient/100*r('correct'+weapon+'Rate')*growth*\
                v('AttackElementCorrectParam',aec,'Influence'+engine+'CorrectRate_byPhysics')/100
    return w('attackBasePhysics')*r('physicsAtkRate')*(1+bonus)

def apply(raw, defs, item_bnd):
    parts,tables,maps = context(raw,defs)
    v = lambda t,r,f:value(tables,maps,t,r,f)
    names = {rid:name for n,(_,b) in bnd_entries(dcx_unpack(item_bnd)).items()
             if 'WeaponName' in n for rid,name in fmg_read(b).items()
             if name and name.strip() and '[ERROR]' not in name}
    weapons = tables['EquipParamWeapon']['rows']
    roots = {rid for rid in names if rid%10000==0 and rid in weapons}
    caster_roots = {rid for rid in roots if v('EquipParamWeapon',rid,'enableMagic') or
                    v('EquipParamWeapon',rid,'enableMiracle')}
    changes = {}; selected = []; groups = {}; added = {}; reinforced_changes = {}
    rein = tables['ReinforceParamWeapon']['rows']
    wp = maps['EquipParamWeapon']['reinforceTypeId']
    rp = maps['ReinforceParamWeapon']['physicsAtkRate']
    assert wp[1:4] == ('s16',218,2) and rp[1]=='f32'
    for rid,record in weapons.items():
        root = rid//10000*10000
        # Explicit Ascended dagger rows retain their declared original family.
        if root not in roots:
            if rid not in (60000001,60002001):
                continue
            root = v('EquipParamWeapon',rid,'originEquipWep')//10000*10000
        kind = v('EquipParamWeapon',rid,'wepType')
        if root not in roots or root in caster_roots or kind not in TYPE_TIER:
            continue
        if v('EquipParamWeapon',rid,'attackBasePhysics') <= 0:
            continue
        if v('EquipParamWeapon',rid,'enableMagic') or v('EquipParamWeapon',rid,'enableMiracle'):
            continue
        tier = {23100000:5,17030000:6}.get(root,TYPE_TIER[kind])
        pointer = v('EquipParamWeapon',rid,'reinforceTypeId')
        # Accept the previous general-colossal candidate for this single exception.
        if root in (23100000,17030000) and pointer == private_id(TYPE_TIER[kind],2200):
            source = 2200
        else:
            source = source_id(pointer,tier)
        levels = []
        for level in range(26):
            if source+level not in rein:
                break
            levels.append(level)
        assert levels and len(levels)>1, ('unupgradable eligible row',rid,source)
        maximum = max(levels)
        target = private_id(tier,source)
        groups[target] = (tier,source,maximum)
        selected.append((rid,root,kind,tier,source,target,maximum))
        body = bytearray(record['data'])
        struct.pack_into('<h',body,wp[2],target)
        if body != record['data']:
            changes[rid] = bytes(body)
    for target,(tier,source,maximum) in groups.items():
        factor = TIERS[tier][1]
        for level in range(maximum+1):
            original = rein[source+level]['data']
            body = bytearray(original)
            old = struct.unpack_from('<f',original,rp[2])[0]
            extra = 1+(factor-1)*level/maximum
            struct.pack_into('<f',body,rp[2],old*extra)
            allowed = {rp[2]}
            if tier == 6:
                # Keep saved +1..+10 rows valid, but remove all offensive upgrade gains.
                baseline = rein[source]['data']
                flat_fields = ('physicsAtkRate','magicAtkRate','fireAtkRate','thunderAtkRate',
                               'darkAtkRate','correctStrengthRate','correctAgilityRate',
                               'correctMagicRate','correctFaithRate','correctLuckRate','baseAtkRate')
                for field in flat_fields:
                    definition = maps['ReinforceParamWeapon'][field]
                    assert definition[1]=='f32'
                    offset = definition[2]
                    body[offset:offset+4] = baseline[offset:offset+4]
                    allowed.add(offset)
            body = bytes(body)
            allowed_bytes = {offset+i for offset in allowed for i in range(4)}
            assert all(c==d or i in allowed_bytes for i,(c,d) in enumerate(zip(body,original)))
            if level == 0:
                assert body == original
            row = target+level
            if row in rein:
                # Existing rows must belong to this exact module; reject collisions.
                assert rein[row]['data'] == body, ('private row collision',row)
            else:
                added[row] = body
    # Avoid repacking an already patched input, preserving binary idempotency.
    if not changes and not added:
        result = raw
    else:
        updates = {
            'EquipParamWeapon.param':param_patch(parts['EquipParamWeapon.param'][1],changes,{},664),
            'ReinforceParamWeapon.param':param_patch(parts['ReinforceParamWeapon.param'][1],{},added,128),
        }
        result = bnd_repack(raw,updates)
    after,at,am = context(result,defs)
    assert parts.keys()==after.keys()
    for name,(_,body) in parts.items():
        if name not in ('EquipParamWeapon.param','ReinforceParamWeapon.param'):
            assert after[name][1]==body, name
    for rid,record in weapons.items():
        expected = changes.get(rid,record['data'])
        got = at['EquipParamWeapon']['rows'][rid]
        assert got['data']==expected and got['name']==record['name'], rid
        if rid in changes:
            assert expected[:wp[2]]==record['data'][:wp[2]] and expected[wp[2]+2:]==record['data'][wp[2]+2:]
    for rid,record in rein.items():
        assert at['ReinforceParamWeapon']['rows'][rid]==record, rid
    for rid,body in added.items():
        assert at['ReinforceParamWeapon']['rows'][rid]['data']==body
    comparisons = []
    for rid,root,kind,tier,source,target,maximum in selected:
        # Logical original baseline remains available after repeat application.
        old = physical_ar(tables,maps,rid,source+maximum)
        new = physical_ar(at,am,rid,target+maximum)
        if tier == 6:
            assert new == physical_ar(tables,maps,rid,source)
        else:
            assert abs(new/old-TIERS[tier][1]) < 0.000001
        assert physical_ar(tables,maps,rid,source)==physical_ar(at,am,rid,target)
        rates = [value(at,am,'ReinforceParamWeapon',target+l,'physicsAtkRate') for l in range(maximum+1)]
        if tier == 6:
            assert len(set(rates))==1
            assert all(physical_ar(at,am,rid,target+l)==new for l in range(maximum+1))
        else:
            assert all(b>a for a,b in zip(rates,rates[1:])), (rid,'nonmonotonic upgrade')
        comparisons.append({'id':rid,'base_id':root,'name':names[root],'type':kind,'tier':TIERS[tier][0],
            'original_reinforce':source,'private_reinforce':target,'max_level':maximum,
            'physical_ar_99_before':round(old,3),'physical_ar_99_after':round(new,3)})
    watchdog = next(c for c in comparisons if c['id']==23010000)
    assert abs(watchdog['physical_ar_99_after']-5000)<0.01, watchdog
    ghiza = next(c for c in comparisons if c['id']==23100000)
    assert abs(ghiza['physical_ar_99_after']-2800)<0.01, ghiza
    serpent = next(c for c in comparisons if c['id']==17030000)
    assert abs(serpent['physical_ar_99_after']-194.25)<0.01, serpent
    progression = []
    for level in range(watchdog['max_level']+1):
        progression.append({'level':level,
            'before':round(physical_ar(tables,maps,23010000,watchdog['original_reinforce']+level),2),
            'after':round(physical_ar(at,am,23010000,watchdog['private_reinforce']+level),2)})
    audit = {'module':'melee_reinforcement_20261002','model':'one-handed; 99 relevant stats; physical AR; no external buffs',
        'tiers':[{'name':n,'max_physical_multiplier':m,'weapon_types':ks} for n,m,ks in TIERS],
        'selected_weapon_rows':len(selected),'changed_weapon_rows':len(changes),'added_reinforce_rows':len(added),
        'private_groups':{str(k):{'tier':TIERS[t][0],'source':s,'max_level':m} for k,(t,s,m) in groups.items()},
        'unchanged_other_tables':len(parts)-2,'excluded_caster_base_ids':sorted(caster_roots),
        'watchdog_progression':progression,'weapons':comparisons,
        'checks':['all other member bytes preserved','all original reinforcement rows preserved',
                  'weapon changes confined to reinforcement pointer','+0 unchanged','physical endpoint ratios',
                  'ordinary selected reinforcement levels strictly increase; Serpent-Hunter offensive rates flat',
                  'private copies preserve all other fields outside explicit offensive rate changes'],
        'exceptions':{'ghiza_wheel_target':2800,'serpent_hunter_flat_physical_ar_99':194.25,
                      'serpent_hunter_flat_fields':list(flat_fields)},
        'serpent_hunter_progression':[{'level':l,'physical_ar_99':physical_ar(at,am,17030000,serpent['private_reinforce']+l)}
                                      for l in range(serpent['max_level']+1)]}
    return result,audit

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--regulation',type=Path,required=True)
    parser.add_argument('--item-bnd',type=Path,required=True,help='current item_dlc02, read names only')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--audit',type=Path,required=True)
    args = parser.parse_args()
    key = bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    defs = Path(os.environ['ARMOR_PARAMDEFS'])
    original = args.regulation.read_bytes()
    header,raw = unpack(original,key)
    result,audit = apply(raw,defs,args.item_bnd.read_bytes())
    again,_ = apply(result,defs,args.item_bnd.read_bytes())
    assert again==result, 'idempotency'
    blob = original if result==raw else pack_regulation(header,result,key)
    assert unpack(blob,key)[1]==result
    audit.update(input_sha256=hashlib.sha256(original).hexdigest(),output_sha256=hashlib.sha256(blob).hexdigest(),
                 output_bytes=len(blob),idempotent=True,encryption_readback=True,game_tested=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(blob)
    args.audit.parent.mkdir(parents=True,exist_ok=True)
    args.audit.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:audit[k] for k in ('selected_weapon_rows','changed_weapon_rows','added_reinforce_rows','output_sha256','idempotent')},indent=2))

if __name__=='__main__':
    main()
