"""Rename the armor hit-reaction caption; never modify gameplay parameters.

Run on the latest integrated input, not an old whole-file replacement:
python scripts/update_hit_stagger_text.py --input item_dlc02.msgbnd.dcx --output patched.msgbnd.dcx
The same command accepts armor description JSON files.
"""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'systems/armor/scripts'))
from formats import bnd_entries, bnd_patch, dcx_pack, dcx_unpack
from fmg import fmg_read, fmg_write
RENAMES = {'Hit-reaction grade 1': 'Reduced hit stagger',
           '受击动作等级 1': '减轻受击硬直'}


def rename(text):
    if not isinstance(text, str):
        return text
    for old, new in RENAMES.items():
        text = text.replace(old, new)
    return text


def patch_archive(blob):
    raw = dcx_unpack(blob)
    parts = bnd_entries(raw)
    updates, changed = {}, []
    for name, (_, body) in parts.items():
        if not name.startswith('ProtectorCaption'):
            continue
        original = fmg_read(body)
        entries = {rid: rename(text) for rid, text in original.items()}
        ids = [rid for rid in entries if entries[rid] != original[rid]]
        if ids:
            updates[name] = fmg_write(entries)
            changed.extend(ids)
    if not updates:
        return blob, changed
    result = dcx_pack(bnd_patch(raw, updates))
    reread = bnd_entries(dcx_unpack(result))
    assert reread.keys() == parts.keys()
    for name, (_, body) in parts.items():
        if name not in updates:
            assert reread[name][1] == body
        else:
            before, after = fmg_read(body), fmg_read(reread[name][1])
            assert before.keys() == after.keys()
            assert after == {rid: rename(text) for rid, text in before.items()}
    return result, changed


def patch_json(data):
    changed = []
    def visit(value, path=''):
        if isinstance(value, dict):
            return {k: visit(v, path + '/' + k) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v, path + '/' + str(i)) for i, v in enumerate(value)]
        result = rename(value)
        if result != value:
            changed.append(path)
        return result
    return visit(data), changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.input.suffix == '.json':
        result, changed = patch_json(json.loads(args.input.read_text()))
        body = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
        assert patch_json(result) == (result, [])
    else:
        body, changed = patch_archive(args.input.read_bytes())
        assert patch_archive(body) == (body, [])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(body)
    print(json.dumps({'output': str(args.output), 'changed_captions': len(changed),
                      'idempotent': True, 'parameters': 'untouched'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
