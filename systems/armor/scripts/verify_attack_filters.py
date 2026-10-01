"""Check all reward attack filters against native selectors and previous bytes.

This is a static engine-filter model, not an in-game damage test.
"""
from pathlib import Path
import argparse, collections, hashlib, json, math, sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parents[1] / 'scripts'))
from analyze_regulation import read_bnd
from field_diff import defs, fields, decode

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--previous-bnd', type=Path)
    args = parser.parse_args()
    _, out = read_bnd(ROOT / 'data/result.bnd')
    _, native = read_bnd(ROOT / 'inputs/work/vanilla.bnd')
    layout = {f[0]: f for f in fields(defs()[out['SpEffectParam']['ptype']])[0]}
    rows = out['SpEffectParam']['rows']
    def val(rid, key): return decode(rows[rid]['data'], layout[key])
    groups = json.loads((ROOT / 'data/sets.json').read_text())
    rewards = [r for g in groups.values() for r in g['rewards']]
    checked = collections.Counter()
    for reward in rewards:
        rid = reward['effect']; template = reward['template'] or 1950
        source = native['SpEffectParam']['rows'][template]['data']
        for key in ['wepParamChange', 'magParamChange', 'miracleParamChange',
                    'magicSubCategoryChange1', 'magicSubCategoryChange2',
                    'magicSubCategoryChange3', 'throwAttackParamChange']:
            expected = reward['fields'].get(key, decode(source, layout[key]))
            if template == 1950 and key in ['wepParamChange', 'magParamChange', 'miracleParamChange']:
                expected = {'wepParamChange': 0, 'magParamChange': 1, 'miracleParamChange': 1}[key]
            assert val(rid, key) == expected, (rid, key, val(rid, key), expected)
        for key, expected in reward['fields'].items():
            assert math.isclose(val(rid, key), expected, rel_tol=1e-6, abs_tol=1e-6), (rid, key)
        for key in ['effectTargetSelf', 'effectTargetPlayer', 'effectTargetLive']:
            assert val(rid, key) == 1, (rid, key)
        assert val(rid, 'spCategory') == 0
        checked['all_reward_roots'] += 1
        if template == 1950: checked['neutral_rewards_include_weapons'] += 1
    # Native action subcategories must still exist in the installed player attacks.
    attack_table = out['AtkParam_Pc']
    af = {f[0]: f for f in fields(defs()[attack_table['ptype']])[0]}
    counts = collections.Counter()
    for row in attack_table['rows'].values():
        for code in {decode(row['data'], af[k]) for k in ['subCategory1', 'subCategory2']}:
            counts[code] += 1
    selector_refs = {100:321300, 102:321800, 103:322000, 104:321200}
    action_checks = []
    for reward in rewards:
        rid = reward['effect']; code = val(rid, 'magicSubCategoryChange1')
        if code not in selector_refs: continue
        ref = native['SpEffectParam']['rows'][selector_refs[code]]['data']
        assert decode(ref, layout['magicSubCategoryChange1']) == code
        assert val(rid, 'wepParamChange') == decode(ref, layout['wepParamChange']) == 0
        assert counts[code] > 0
        # Both hands are included by 0; unrelated subcategories must remain excluded.
        for hand in [1, 2]:
            assert val(rid, 'wepParamChange') in [0, hand]
            assert 0 not in [val(rid, 'magicSubCategoryChange'+str(i)) for i in [1]]
        action_checks.append({'effect': rid, 'category': code, 'native_reference':selector_refs[code],
                              'player_attack_rows': counts[code], 'both_hands':'included'})
    changed = []
    if args.previous_bnd:
        _, old = read_bnd(args.previous_bnd)
        assert out.keys() == old.keys()
        target_ids = {r['effect'] for r in rewards if not r['template']}
        for name, table in out.items():
            assert table['rows'].keys() == old[name]['rows'].keys()
            for rid, row in table['rows'].items():
                before = old[name]['rows'][rid]['data']; after = row['data']
                if before == after: continue
                assert name == 'SpEffectParam' and rid in target_ids
                assert decode(before, layout['wepParamChange']) == 3
                assert decode(after, layout['wepParamChange']) == 0
                offset = layout['wepParamChange'][2]
                assert before[:offset] == after[:offset] and before[offset+1:] == after[offset+1:]
                changed.append(rid)
        assert set(changed) == target_ids
    report = {'reward_checks':dict(checked),'action_filter_checks': action_checks,
              'only_weapon_filter_changed_rows':len(changed),
              'all_other_parameter_rows':'byte-identical' if args.previous_bnd else 'not compared',
              'regulation_sha256':hashlib.sha256((ROOT/'ModEngine/mod/regulation.bin').read_bytes()).hexdigest(),
              'runtime_validation':'not run; player reports jump/charge/counter fail, critical and magic work'}
    (ROOT/'data/attack_filter_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='action_filter_checks'},indent=2))

if __name__ == '__main__': main()
