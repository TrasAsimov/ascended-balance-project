"""Halve positive status buildup in player spell attack graphs.

Run once after armor/core integration and extra-penalty cleanup. Private
copies isolate shared Bullet/AtkParam_Pc/SpEffect rows from original users.
Requires ARMOR_REGULATION_KEY_HEX and matching ARMOR_PARAMDEFS.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import struct
import sys

import zstandard as zstd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from disable_player_debuffs import sha, unpack
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'systems/armor/scripts'))
from analyze_regulation import read_param
from field_diff import decode, defs, fields, TYPES
from formats import bnd_entries, bnd_repack, param_patch

# 7400000/7410000 are reserved by the minor-boss heart module.
BASE_ID, END_ID = 7500000, 7600000
STATUS = ['poizonAttackPower','diseaseAttackPower','bloodAttackPower',
          'curseAttackPower','freezeAttackPower','sleepAttackPower','madnessAttackPower']
CHAINS = ['replaceSpEffectId','cycleOccurrenceSpEffectId','atkOccurrenceSpEffectId']


def patch(raw):
    parts = bnd_entries(raw)
    assert len(parts) == 194
    required = ['Magic','EquipParamGoods','Bullet','AtkParam_Pc','SpEffectParam']
    tables = {t: read_param(parts[t+'.param'][1], t) for t in required}
    layouts, sizes = {}, {}
    definitions = defs()
    for t in required:
        fs, size = fields(definitions[tables[t]['ptype']])
        assert size == tables[t]['row_size'], t
        layouts[t], sizes[t] = {f[0]: f for f in fs}, size
    for t in ['Bullet','AtkParam_Pc','SpEffectParam']:
        assert not any(BASE_ID <= i < END_ID for i in tables[t]['rows']), (
            'Reserved IDs occupied; use an unpatched integration input', t)

    def get(t, i, k):
        return decode(tables[t]['rows'][i]['data'], layouts[t][k])

    def write(t, body, k, value):
        f = layouts[t][k]
        assert f[4] is None and f[6] == 1
        struct.pack_into('<'+TYPES[f[1]][0], body, f[2], value)

    # ER player spell item types: sorcery/incantation and their alternate types.
    # Spell ID is the corresponding Goods row ID; NPC-only Magic has no such item.
    players = {i for i in tables['Magic']['rows'] if i in tables['EquipParamGoods']['rows']
               and get('EquipParamGoods', i, 'goodsType') in [5,16,17,18]}
    roots, edges, todo = {}, {}, []
    for i in sorted(players):
        roots[i] = []
        for j in range(1,11):
            category = get('Magic', i, 'refCategory'+str(j))
            # Direct self buffs / weapon enchantments (category 2) are unchanged.
            target = {0: 'AtkParam_Pc', 1: 'Bullet'}.get(category)
            rid = get('Magic', i, 'refId'+str(j))
            if target and rid in tables[target]['rows']:
                roots[i].append(('refId'+str(j), (target, rid)))
                todo.append((target, rid))
    while todo:
        node = todo.pop()
        if node in edges:
            continue
        t, i = node
        out = []
        if t == 'Bullet':
            out += [(k, ('Bullet', get(t,i,k))) for k in ['HitBulletID','intervalCreateBulletId']]
            out += [('atkId_Bullet', ('AtkParam_Pc', get(t,i,'atkId_Bullet')))]
            out += [(k, ('SpEffectParam',get(t,i,k))) for k in ['spEffectId'+str(j) for j in range(5)]]
        elif t == 'AtkParam_Pc':
            out += [(k, ('SpEffectParam',get(t,i,k))) for k in ['spEffectId'+str(j) for j in range(5)]]
        else:
            out += [(k, ('SpEffectParam',get(t,i,k))) for k in CHAINS]
        edges[node] = [(k, target) for k,target in out if target[1] in tables[target[0]]['rows']]
        todo.extend(target for _,target in edges[node])
    status_nodes = {node for node in edges if node[0] == 'SpEffectParam'
                    and any(get(*node,k) > 0 for k in STATUS)}
    affected = set(status_nodes)
    while True:
        parents = {node for node, out in edges.items() if any(target in affected for _,target in out)}
        if parents <= affected:
            break
        affected |= parents
    mappings = {}
    for t in ['Bullet','AtkParam_Pc','SpEffectParam']:
        ids = sorted(i for table,i in affected if table == t)
        assert len(ids) < END_ID-BASE_ID
        mappings[t] = {i: BASE_ID+j for j,i in enumerate(ids)}
    added = defaultdict(dict)
    records = []
    for t,i in sorted(affected):
        body = bytearray(tables[t]['rows'][i]['data'])
        for field, (target, rid) in edges[t,i]:
            if rid in mappings[target]:
                write(t,body,field,mappings[target][rid])
        if t == 'SpEffectParam':
            changed = {}
            for k in STATUS:
                before = get(t,i,k)
                if before > 0:
                    # Integral engine fields: nearest integer, minimum one.
                    after = max(1,(before+1)//2)
                    write(t,body,k,after)
                    changed[k] = {'before':before,'after':after}
            if changed:
                records.append({'source_id':i,'private_id':mappings[t][i],'buildup':changed})
        added[t][mappings[t][i]] = bytes(body)
    magic_changes, spell_records = {}, []
    for i, targets in roots.items():
        body = bytearray(tables['Magic']['rows'][i]['data'])
        changed = {}
        for field,(target,rid) in targets:
            if rid in mappings[target]:
                write('Magic',body,field,mappings[target][rid])
                changed[field] = {'table':target,'before':rid,'after':mappings[target][rid]}
        if changed:
            magic_changes[i] = bytes(body)
            spell_records.append({'magic_id':i,'attack_references':changed})
    assert records and spell_records
    updates = {t+'.param':param_patch(parts[t+'.param'][1],{},added[t],sizes[t])
               for t in ['Bullet','AtkParam_Pc','SpEffectParam'] if added[t]}
    updates['Magic.param'] = param_patch(parts['Magic.param'][1],magic_changes,{},sizes['Magic'])
    output = bnd_repack(raw,updates)
    result = bnd_entries(output)
    assert all(result[n][1] == body for n,(_,body) in parts.items() if n not in updates)
    parsed = {t:read_param(result[t+'.param'][1],t) for t in required}
    for t in required:
        for i,row in tables[t]['rows'].items():
            expected = magic_changes.get(i,row['data']) if t == 'Magic' else row['data']
            assert parsed[t]['rows'][i]['data'] == expected, (t,i)
            assert parsed[t]['rows'][i]['name'] == row['name'], (t,i,'name')
        assert set(parsed[t]['rows']) == set(tables[t]['rows']) | set(added[t])
    # Independently limit private changes to positive buildup and copied graph IDs.
    for t,i in sorted(affected):
        before = tables[t]['rows'][i]['data']
        after = parsed[t]['rows'][mappings[t][i]]['data']
        allowed = {field for field,(target,rid) in edges[t,i] if rid in mappings[target]}
        if t == 'SpEffectParam':
            allowed |= {k for k in STATUS if get(t,i,k)>0}
        for k,f in layouts[t].items():
            a,b = decode(before,f),decode(after,f)
            if k not in allowed:
                assert a == b, (t,i,k,a,b)
            elif k in STATUS:
                assert b == max(1,(a+1)//2), (t,i,k)
    for i,row in magic_changes.items():
        for k,f in layouts['Magic'].items():
            if not k.startswith('refId'):
                assert decode(row,f) == get('Magic',i,k), (i,k)
    # Every positive buildup reachable from a changed spell must use a private
    # copy; every reference without a positive-buildup descendant stays original.
    for node in affected:
        for _,target in edges[node]:
            assert (target in affected) == (target[1] in mappings[target[0]])
    audit = {'multiplier':0.5,'rounding':'nearest integer, minimum one for positive values',
             'player_magic_candidates':len(players),'changed_magic_rows':len(magic_changes),
             'private_added_rows':{t:len(added[t]) for t in ['Bullet','AtkParam_Pc','SpEffectParam']},
             'unchanged_param_members':len(parts)-len(updates),
             'private_mapping':{t:{str(i):j for i,j in m.items()} for t,m in mappings.items()},
             'buildup_effects':records,'spells':spell_records,
             'validation':['all existing Bullet/AtkParam_Pc/SpEffect rows byte-identical',
                           'existing Magic changes limited to selected player attack refId fields',
                           'NPC-only Magic and every non-target PARAM member identical',
                           'private copies differ only in graph references and positive buildup',
                           'status burst/DoT damage, duration, target flags and immunity preserved',
                           'direct self buffs and weapon enchantments preserved',
                           'NPC resistance/growth, armor, weapons, talismans and existing fixes preserved'],
             'limitations':['AI actors reusing a player Magic row also follow its updated attack graph; NPC-only Magic and ordinary enemy attack graphs remain original.',
                            'Projectile count and hit chains retained; 50% per-hit buildup does not guarantee 50% fewer procs.',
                            'This does not halve damage after a status has triggered.'],
             'game_validation':'not run'}
    return output,audit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--expected-sha256')
    args=p.parse_args()
    assert args.input.resolve()!=args.output.resolve()
    key=bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    source=args.input.read_bytes()
    if args.expected_sha256:
        assert sha(source)==args.expected_sha256
    header,raw=unpack(source,key)
    output,audit=patch(raw)
    # Prevent accidental repeated scaling: patched input is explicitly rejected.
    try:
        patch(output)
    except AssertionError as e:
        assert 'Reserved IDs occupied' in str(e)
    else:
        raise AssertionError('Repeated application must be rejected')
    packed=zstd.ZstdCompressor(compression_params=zstd.ZstdCompressionParameters.from_level(
        15,window_log=16,write_content_size=False)).compress(output)
    h=bytearray(header)
    struct.pack_into('>II',h,28,len(output),len(packed))
    plain=bytes(h)+packed
    plain+=bytes(-len(plain)%16)
    iv=bytes(16)
    encryptor=Cipher(algorithms.AES(key),modes.CBC(iv)).encryptor()
    result=iv+encryptor.update(plain)+encryptor.finalize()
    assert unpack(result,key)[1]==output
    audit.update(input_sha256=sha(source),output_sha256=sha(result),output_bytes=len(result),
                 bnd_sha256=sha(output),bnd_bytes=len(output),param_version=output[24:32].decode(),
                 status='static checks passed; game validation not run')
    audit['validation'] += ['repeated application rejected','encrypted round-trip passed']
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.audit.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(result)
    args.audit.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:audit[k] for k in ['changed_magic_rows','private_added_rows',
                                         'output_sha256','output_bytes']}))


if __name__=='__main__':
    main()
