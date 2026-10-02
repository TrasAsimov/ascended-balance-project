"""Patch v0.10.8 armor captions and Bandit Mask membership, without packaging.

Owned inputs: --input <directory containing ModEngine and Armor_Core>.
Outputs: --output <handoff directory>. Leaves regulation.bin unchanged.
"""
from pathlib import Path
import argparse, copy, hashlib, itertools, json, re, struct, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'systems/armor/scripts'))
from formats import Emevd, bnd_entries, bnd_patch, dcx_pack, dcx_unpack
from fmg import fmg_read, fmg_write
from shield_text import patch_shields, effects_only, is_shield


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blocks(text, language):
    """Read existing compact captions without changing effect scope or values."""
    found = []
    for line in text.splitlines()[2:]:
        if not line.strip():
            continue
        match = re.match(r'(Piece|[234] pcs|单件|[234]件) · (.*)', line)
        if match:
            found.append([match[1], match[2]])
        elif line.startswith('    ') and found:
            found.append([found[-1][0], line.strip()])
        else:
            raise ValueError(('Unexpected caption format', language, line))
    return found


def render(group, effects, language):
    count = group['full']
    header = (f"{group['name']}（{count}件）" if language == 'zh' else
              f"{group['english_name']} ({count} {'piece' if count == 1 else 'pieces'})")
    result = [header]
    for label, effect in effects:
        if language == 'zh':
            label = '效果' if label == '单件' else label + '效果'
        else:
            label = 'Effect' if label == 'Piece' else label.split()[0] + '-Piece Effect'
        result.append(label + ': ' + effect)
    return '\n\n'.join(result)


def checks(event):
    return [(struct.unpack_from('<bb2xii', args), layer)
            for bank, index, args, layer in event['ins'] if (bank, index) == (3, 34)]


def active(event, equipment):
    """Evaluate the actual equipment/condition instructions before combat checks."""
    state = {}
    def add(group, value):
        state[group] = (state.get(group, False) or value if group < 0 else
                        state.get(group, True) and value)
    for bank, index, args, _ in event['ins']:
        if (bank, index) == (3, 34):
            group, slot, rid, comparison = struct.unpack('<bb2xii', args)
            assert comparison == -1
            add(group, equipment[slot] == rid)
        elif (bank, index) == (0, 0):
            group, expected, source, pad = struct.unpack('<bBbB', args)
            assert expected == 1 and pad == 0
            add(group, state[source])
        elif (bank, index) == (4, 14):
            return state[15]
        else:
            raise AssertionError(('Unexpected condition instruction', bank, index))
    raise AssertionError('No combat-state gate')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    src, out = args.input, args.output
    family = json.loads((ROOT / 'systems/armor/config/families.json').read_text())
    groups, armors = family['groups'], family['armors']
    ids = set(map(int, armors))
    assert len(ids) == 741
    ownership = {}
    for key, group in groups.items():
        assert group['full'] == sum(bool(v) for v in group['pieces'].values())
        for slot, members in group['pieces'].items():
            for rid in members:
                assert rid not in ownership
                ownership[rid] = (key, int(slot))
                assert (armors[str(rid)]['key'], armors[str(rid)]['slot']) == ownership[rid]
    assert set(ownership) == ids
    assert ownership[1401000] == ('93', 0)

    regulation = (src / 'ModEngine/mod/regulation.bin').read_bytes()
    assert sha(regulation) == 'bf923783389021372e1d33d7bcc5e776c9b32e155af59f58fc0003142da44398', 'Use the verified v0.10.8 base'
    path = Path('ModEngine/mod/event/common.emevd.dcx')
    original_blob = (src / path).read_bytes()
    assert sha(original_blob) == 'e1307c8f0e5ef2e4eef82cd7adbb6fda88495f93e2007c69797786acdcd901d6', 'Use the verified v0.10.8 event base'
    original = Emevd(dcx_unpack(original_blob))
    changed = copy.deepcopy(original)
    by_id = {e['id']: e for e in changed.events}
    targets = {9000157: ('93', 2), 9000158: ('93', 4),
               9000187: ('140', 2), 9000188: ('140', 4)}
    for rid, (key, tier) in targets.items():
        event = by_id[rid]
        assert not event['params'], 'Instruction insertion requires unparameterized events'
        replacement = []
        edits = 0
        for instruction in event['ins']:
            bank, index, body, layer = instruction
            armor = struct.unpack_from('<i', body, 4)[0] if (bank, index) == (3, 34) else None
            if key == '140' and armor == 1401000:
                edits += 1
                continue
            replacement.append(instruction)
            if key == '93' and armor == 930000:
                assert struct.unpack('<bb2xii', body) == (-1, 0, 930000, -1)
                modified = bytearray(body)
                struct.pack_into('<i', modified, 4, 1401000)
                replacement.append((bank, index, bytes(modified), layer))
                edits += 1
        assert edits == 1
        event['ins'] = replacement
        expected = {(int(slot), member) for slot, members in groups[key]['pieces'].items() for member in members}
        assert {(c[1], c[2]) for c, _ in checks(event)} == expected
    unchanged = 0
    for before, after in zip(original.events, changed.events):
        assert before['id'] == after['id']
        if before['id'] not in targets:
            assert before == after
            unchanged += 1
        else:
            # All condition-combination, relative skips, grants and cleanup remain intact.
            assert [i for i in before['ins'] if i[:2] != (3, 34)] == [i for i in after['ins'] if i[:2] != (3, 34)]
    cases = 0
    for rid, (key, tier) in targets.items():
        slot_options = [groups[key]['pieces'][str(slot)] + [0, 9999999] for slot in range(4)]
        for loadout in itertools.product(*slot_options):
            count = sum(loadout[slot] in groups[key]['pieces'][str(slot)] for slot in range(4))
            assert active(by_id[rid], loadout) == (count >= tier), (rid, loadout)
            cases += 1
    assert active(by_id[9000158], (1401000, 931100, 930200, 930300))
    assert not active(by_id[9000187], (1401000, 1400100, 0, 0))
    assert active(by_id[9000188], (1400000, 1400100, 1400200, 1400300))
    packed = dcx_pack(changed.write())
    reread = Emevd(dcx_unpack(packed))
    assert reread.events == changed.events and reread.linked == original.linked and reread.strings == original.strings
    (out / path).parent.mkdir(parents=True, exist_ok=True)
    (out / path).write_bytes(packed)

    zh_original = json.loads((src / 'Armor_Core/description_zh.json').read_text())
    zh_updated = copy.deepcopy(zh_original)
    english = {}
    archive_counts = {}
    effect_checks = 0
    shield_counts = {}
    shields_all = {}
    shield_empty = set()
    # v0.10.8 DLC01 contains vanilla shield captions, while DLC02 holds
    # Ascended's effect text. Use existing DLC02 mechanics in both tables.
    shield_canonical = {}
    for name in ('item_dlc01', 'item_dlc02'):
        native_parts = bnd_entries(dcx_unpack((src / f'ModEngine/mod/msg/engus/{name}.msgbnd.dcx').read_bytes()))
        _, native_shields, _ = patch_shields(native_parts)
        for rid, text in native_shields.items():
            if text or rid not in shield_canonical:
                shield_canonical[rid] = text
    for name in ('item_dlc01', 'item_dlc02'):
        path = Path(f'ModEngine/mod/msg/engus/{name}.msgbnd.dcx')
        parts = bnd_entries(dcx_unpack((src / path).read_bytes()))
        existing = {}
        for filename, (_, body) in parts.items():
            if filename.startswith('ProtectorCaption'):
                for rid, text in fmg_read(body).items():
                    if rid in ids and text:
                        assert rid not in existing or existing[rid] == text
                        existing[rid] = text
        assert set(existing) == ids
        rendered = {}
        for rid, old_text in existing.items():
            group = groups[armors[str(rid)]['key']]
            effects = blocks(old_text, 'en')
            if rid == 1401000:
                effects = [v for v in effects if v[0] == 'Piece'] + [v for v in blocks(existing[930000], 'en') if v[0] != 'Piece']
            rendered[rid] = render(group, effects, 'en')
            assert blocks(old_text, 'en') == effects or rid == 1401000
            if str(rid) in english:
                assert english[str(rid)] == rendered[rid]
            english[str(rid)] = rendered[rid]
        updates = {}
        for filename, (_, body) in parts.items():
            if not filename.startswith('ProtectorCaption'):
                continue
            entries = fmg_read(body)
            for rid in entries.keys() & ids:
                entries[rid] = rendered[rid]
            updates[filename] = fmg_write(entries)
        shield_updates, shields, no_effect = patch_shields(parts, shield_canonical)
        updates.update(shield_updates)
        shield_counts[name] = len(shields)
        shield_empty.update(no_effect)
        shields_all[name] = shields
        raw = bnd_patch(dcx_unpack((src / path).read_bytes()), updates)
        repacked = dcx_pack(raw)
        check = bnd_entries(dcx_unpack(repacked))
        for filename, (_, body) in parts.items():
            if filename not in updates:
                assert check[filename][1] == body
            else:
                before, after = fmg_read(body), fmg_read(check[filename][1])
                assert before.keys() == after.keys()
                for rid in before:
                    if filename.startswith('ProtectorCaption'):
                        assert after[rid] == (rendered[rid] if rid in ids else before[rid])
                        effect_checks += rid in ids
                    else:
                        assert after[rid] == shields.get(str(rid), before[rid])
                        if str(rid) in shields:
                            assert after[rid] == shield_canonical[str(rid)]
                            assert all(block.startswith('Effect: ') for block in after[rid].split('\n\n') if block)
        (out / path).parent.mkdir(parents=True, exist_ok=True)
        (out / path).write_bytes(repacked)
        archive_counts[name] = len(rendered)
    for rid in ids:
        group = groups[armors[str(rid)]['key']]
        effects = blocks(zh_original[str(rid)], 'zh')
        if rid == 1401000:
            effects = [v for v in effects if v[0] == '单件'] + [v for v in blocks(zh_original['930000'], 'zh') if v[0] != '单件']
        zh_updated[str(rid)] = render(group, effects, 'zh')
    for key in zh_original.keys() - {str(rid) for rid in ids}:
        assert zh_updated[key] == zh_original[key]
    for descriptions in (english, {str(rid): zh_updated[str(rid)] for rid in ids}):
        for rid, text in descriptions.items():
            logical = text.split('\n\n')
            assert len(logical) > 1
            assert all('\n' not in block and re.match(r'(Effect|[234]-Piece Effect|效果|[234]件效果): ', block) for block in logical[1:])
            assert not re.search(r'[×x]\d', text)
    assert 'Effect: Sleep resistance +400 points' in english['1401000']
    assert '2-Piece Effect: Jump attack stance damage +10%' in english['1401000']
    assert '4-Piece Effect: Jump attack damage +10%' in english['1401000']
    assert shields_all['item_dlc02']['32050000'] == 'Effect: 20% strike absorb\n\nEffect: 200 madness resist'
    assert not (out / 'ModEngine/mod/regulation.bin').exists()
    assert (src / 'ModEngine/mod/regulation.bin').read_bytes() == regulation
    for filename, data in [('description_zh.json', zh_updated), ('description_en.json', english), ('shield_description_en.json', shields_all)]:
        path = out / 'Armor_Core' / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    report = {
        'base': 'v0.10.8', 'mask_id': 1401000, 'family': 'Raptor / Bandit Set',
        'set_slots': 4, 'mask_single_effect': 'Sleep resistance +400 points (unchanged)',
        'modified_event_ids': list(targets), 'unchanged_events': unchanged,
        'actual_condition_loadouts_verified': cases, 'armor_descriptions': 741,
        'archive_coverage': archive_counts, 'english_caption_readbacks': effect_checks,
        'regulation_sha256_unchanged': sha(regulation),
        'heart_event_20007902': 'unchanged', 'other_FMG_members': 'byte-identical except target armor and shield caption tables',
        'shield_caption_coverage': shield_counts, 'shields_without_existing_effect_text': len(shield_empty),
        'shield_effect_source': 'existing v0.10.8 DLC02 Ascended text mirrored into vanilla DLC01 shield captions',
        'shield_no_effect_behavior': 'lore removed; caption empty; no invented bonus',
        'shield_briar_continuation': shields_all['item_dlc02']['32050000'],
        'other_caption_entries': 'all entries outside 741 armor and shield captions unchanged', 'nonarmor_chinese_entries': 'unchanged',
        'format': 'blank line between every Effect block; percentages; set name and total slots',
        'real_zhocn_archive': 'not generated; owned Chinese archive unavailable',
        'in_game_visual_and_activation_test': 'not run; handoff for integration and game verification',
        'packaging': 'not performed',
        'files': {str(p.relative_to(out)): {'size': p.stat().st_size, 'sha256': sha(p.read_bytes())}
                  for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'verification.json'},
        'mask_caption': english['1401000'],
    }
    (out / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
