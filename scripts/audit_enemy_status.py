"""Read-only comparison of enemy status resistance and attack-side buildup.

Inputs are decrypted BND4 regulation containers; no game files are changed.
Use ARMOR_PARAMDEFS to select matching ER definitions if needed.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'systems/armor/scripts'))
from analyze_regulation import read_bnd
from field_diff import decode, defs, fields


def audit(current: Path, official: Path):
    version, tables = read_bnd(current)
    official_version, vanilla = read_bnd(official)
    definitions = defs()
    layout = {}
    needed = ['NpcParam', 'SpEffectParam', 'ResistCorrectParam', 'Bullet',
              'Magic', 'BehaviorParam_PC', 'EquipParamGoods', 'AtkParam_Npc']
    for table in needed:
        field_list, size = fields(definitions[tables[table]['ptype']])
        assert size == tables[table]['row_size'] == vanilla[table]['row_size'], table
        layout[table] = {f[0]: f for f in field_list}

    def get(table, row, key):
        return decode(row['data'], layout[table][key])

    result = {'scope': 'Static comparison; NPC rows include variants, summons and friendly actors. Not a game test.',
              'current_version': version, 'official_version': official_version,
              'current_bnd_sha256': hashlib.sha256(current.read_bytes()).hexdigest(),
              'official_bnd_sha256': hashlib.sha256(official.read_bytes()).hexdigest()}
    shared = {i: r for i, r in tables['NpcParam']['rows'].items()
              if i in vanilla['NpcParam']['rows'] and get('NpcParam', r, 'hp') > 0}
    resistance_keys = [k for k in layout['NpcParam'] if k.startswith('resist_')]
    result['shared_positive_hp_npc_rows'] = len(shared)
    result['npc_resistance_comparison'] = {}
    for key in resistance_keys:
        counts = Counter()
        lowered = []
        for i, r in shared.items():
            a, b = get('NpcParam', r, key), get('NpcParam', vanilla['NpcParam']['rows'][i], key)
            counts['lower' if a < b else 'higher' if a > b else 'same'] += 1
            if a < b:
                lowered.append({'id': i, 'official': b, 'current': a})
        result['npc_resistance_comparison'][key] = {'counts': dict(counts), 'lowered_rows': lowered}
    result['npc_examples'] = []
    for i in [43110000,30100000,21200000,21300000,25000000,52200000,47300000,47500000,48000000,21300014]:
        r = tables['NpcParam']['rows'][i]
        result['npc_examples'].append({'id': i, 'base_resistance_before_effects': {
            k: {'official': get('NpcParam', vanilla['NpcParam']['rows'][i], k), 'current': get('NpcParam', r, k)}
            for k in resistance_keys}})
    result['npc_correction_reference_changes'] = {
        k: sum(get('NpcParam', r, k) != get('NpcParam', vanilla['NpcParam']['rows'][i], k)
               for i, r in tables['NpcParam']['rows'].items() if i in vanilla['NpcParam']['rows'])
        for k in layout['NpcParam'] if k.startswith('resistCorrectId_')}
    assert tables['ResistCorrectParam']['rows'].keys() == vanilla['ResistCorrectParam']['rows'].keys()
    result['resist_correct_changed_rows'] = sum(r['data'] != vanilla['ResistCorrectParam']['rows'][i]['data']
                                              for i, r in tables['ResistCorrectParam']['rows'].items())
    attack_keys = [k for k in ['poizonAttackPower','diseaseAttackPower','bloodAttackPower',
                             'curseAttackPower','freezeAttackPower','sleepAttackPower','madnessAttackPower']
                   if k in layout['SpEffectParam']]
    increases = []
    for i, r in tables['SpEffectParam']['rows'].items():
        old = vanilla['SpEffectParam']['rows'].get(i)
        if old is None:
            continue
        for k in attack_keys:
            a, b = get('SpEffectParam', r, k), get('SpEffectParam', old, k)
            if a > b and a > 0:
                increases.append({'id': i, 'field': k, 'official': b, 'current': a})
    result['shared_buildup_increases'] = increases
    reducer_keys = [k for k in layout['SpEffectParam'] if k.startswith('change') and k.endswith('ResistPoint')]
    reducers = {}
    for i, r in tables['SpEffectParam']['rows'].items():
        negative = {k: get('SpEffectParam', r, k) for k in reducer_keys if get('SpEffectParam', r, k) < 0}
        if not negative:
            continue
        reducers[i] = {'id': i, 'resistance_point_changes': negative,
                       'duration': get('SpEffectParam', r, 'effectEndurance'), 'direct_references': []}
    for table in ['Bullet', 'AtkParam_Npc']:
        keys = [k for k in layout[table] if k.lower().startswith('speffectid')]
        for i, r in tables[table]['rows'].items():
            for k in keys:
                target = get(table, r, k)
                if target in reducers:
                    reducers[target]['direct_references'].append({'table': table, 'id': i, 'field': k})
    # Traverse actual Bullet child links and typed Goods references (category 1 = Bullet).
    links = {i: [get('Bullet', r, k) for k in ['HitBulletID','intervalCreateBulletId']]
             for i, r in tables['Bullet']['rows'].items()}
    for effect in reducers.values():
        reached = {r['id'] for r in effect['direct_references'] if r['table'] == 'Bullet'}
        while True:
            parents = {i for i, children in links.items() if any(c in reached for c in children)}
            if parents <= reached:
                break
            reached |= parents
        callers = []
        for i, r in tables['EquipParamGoods']['rows'].items():
            if get('EquipParamGoods', r, 'refCategory') != 1:
                continue
            for k in ['refId_default', 'refId_1']:
                if get('EquipParamGoods', r, k) in reached:
                    callers.append({'goods_id': i, 'field': k, 'bullet': get('EquipParamGoods', r, k)})
        effect['typed_goods_callers'] = callers
        effect['reference_counts'] = dict(Counter(r['table'] for r in effect['direct_references']))
    result['resistance_reducers'] = list(reducers.values())
    result['goods_redirections'] = []
    for i in [330,340,360,370,640,670,1720,1730,1840,1841]:
        a, b = tables['EquipParamGoods']['rows'][i], vanilla['EquipParamGoods']['rows'][i]
        result['goods_redirections'].append({'id': i, 'official_bullet': get('EquipParamGoods', b, 'refId_default'),
                                             'current_bullet': get('EquipParamGoods', a, 'refId_default')})
    result['resident_immunity_examples'] = {
        str(i): {k: get('SpEffectParam', tables['SpEffectParam']['rows'][i], k)
                 for k in ['disableCurse','disableMadness']}
        for i in [90030,90060]}
    result['area_resistance_multiplier_examples'] = {
        str(i): {k: {'official': get('SpEffectParam', vanilla['SpEffectParam']['rows'][i], k),
                    'current': get('SpEffectParam', tables['SpEffectParam']['rows'][i], k)}
                 for k in layout['SpEffectParam'] if k.startswith('regist') and k.endswith('ChangeRate')}
        for i in [7000,7040,7090]}
    # Spell topology is essential: shared grease OnAttack effects are also used
    # directly by projectiles, so item labels do not establish the actual source.
    spell_changes = []
    for magic_id, magic in tables['Magic']['rows'].items():
        pending = {get('Magic', magic, 'refId'+str(j)) for j in range(1,11)
                   if get('Magic', magic, 'refCategory'+str(j)) == 1}
        visited = set()
        changes = []
        while pending:
            bullet_id = pending.pop()
            if bullet_id in visited or bullet_id not in tables['Bullet']['rows']:
                continue
            visited.add(bullet_id)
            bullet = tables['Bullet']['rows'][bullet_id]
            pending.update(links[bullet_id])
            old = vanilla['Bullet']['rows'].get(bullet_id)
            status = []
            for slot in ['spEffectId'+str(j) for j in range(5)]:
                effect_id = get('Bullet', bullet, slot)
                effect = tables['SpEffectParam']['rows'].get(effect_id)
                if effect is None:
                    continue
                values = {k: get('SpEffectParam', effect, k) for k in attack_keys
                          if get('SpEffectParam', effect, k) > 0}
                if not values:
                    continue
                official_id = get('Bullet', old, slot) if old else None
                official_effect = vanilla['SpEffectParam']['rows'].get(official_id)
                original = {k: get('SpEffectParam', official_effect, k) for k in attack_keys
                            if get('SpEffectParam', official_effect, k) > 0} if official_effect else {}
                if original != values or official_id != effect_id:
                    status.append({'slot': slot, 'official_effect_id': official_id,
                                   'current_effect_id': effect_id,
                                   'official_positive_buildup': original, 'current_positive_buildup': values})
            if status:
                changes.append({'bullet_id': bullet_id, 'status_changes': status,
                                'numShoot': {'official': get('Bullet', old, 'numShoot') if old else None,
                                             'current': get('Bullet', bullet, 'numShoot')},
                                'HitBulletID': {'official': get('Bullet', old, 'HitBulletID') if old else None,
                                                'current': get('Bullet', bullet, 'HitBulletID')}})
        if changes:
            spell_changes.append({'magic_id': magic_id, 'reachable_changed_bullets': changes})
    result['spell_projectile_status_changes'] = spell_changes
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--current-bnd', type=Path, required=True)
    p.add_argument('--official-bnd', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = audit(args.current_bnd, args.official_bnd)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'npc_rows': result['shared_positive_hp_npc_rows'],
                      'correction_changes': result['resist_correct_changed_rows'],
                      'buildup_increase_fields': len(result['shared_buildup_increases']),
                      'reducer_rows': len(result['resistance_reducers'])}))
