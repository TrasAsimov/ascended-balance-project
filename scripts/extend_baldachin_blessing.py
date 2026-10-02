"""Set normal Baldachin's Blessing use buff to 120 seconds.

Apply on the latest integrated input; retain all other module changes.
Requires ARMOR_REGULATION_KEY_HEX, matching PARAM definitions and existing
project helper modules. No format key is included in this source.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import zstandard as zstd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from disable_player_debuffs import unpack
from analyze_regulation import read_param
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'systems/armor/scripts'))
from formats import bnd_entries, bnd_repack, bnd_patch, param_patch, dcx_unpack, dcx_pack
from field_diff import fields, decode
from build_zhocn_patch import fmg_read, fmg_write

ITEM_ID, EFFECT_ID, CHILD_ID, SECONDS = 3360, 503355, 503356, 120.0
INFO = 'Uses 10 FP to boost poise for 2 minutes'
OLD_INFO = 'Uses 10 FP to boost poise for 30 minutes'
CAPTION_SUFFIX = '\n\nEffect: When used, spends 10 FP to boost poise for 2 minutes.'
OLD_SUFFIX = '\n\nEffect: When used, spends 10 FP to boost poise for 30 minutes.'

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def patch_params(raw, paramdefs):
    parts = bnd_entries(raw)
    assert len(parts) == 194 and raw[24:32] == b'11711000'
    sp = read_param(parts['SpEffectParam.param'][1], 'SpEffectParam')
    goods = read_param(parts['EquipParamGoods.param'][1], 'EquipParamGoods')
    layouts = {}
    for name, filename, table in [('SpEffect', 'SpEffect.xml', sp),
                                   ('Goods', 'EquipParamGoods.xml', goods)]:
        fs, size = fields(paramdefs / filename)
        assert size == table['row_size']
        layouts[name] = {f[0]: f for f in fs}
    g = goods['rows'][ITEM_ID]['data']; gl = layouts['Goods']; sl = layouts['SpEffect']
    assert decode(g, gl['refCategory']) == 2
    assert decode(g, gl['refId_default']) == EFFECT_ID
    assert decode(g, gl['consumeMP']) == 10
    row = sp['rows'][EFFECT_ID]['data']
    assert decode(row, sl['cycleOccurrenceSpEffectId']) == CHILD_ID
    assert decode(row, sl['motionInterval']) == 0.05
    assert decode(sp['rows'][CHILD_ID]['data'], sl['effectEndurance']) == 0.1
    f = sl['effectEndurance']; assert f[1] == 'f32' and f[2:4] == (8, 4)
    before = decode(row, f)
    assert before in (30.0, 1800.0, SECONDS), 'Unexpected base duration: review input'
    patched = bytearray(row); struct.pack_into('<f', patched, f[2], SECONDS)
    table = param_patch(parts['SpEffectParam.param'][1], {EFFECT_ID: bytes(patched)}, {}, sp['row_size'])
    output = bnd_repack(raw, {'SpEffectParam.param': table})
    after_parts = bnd_entries(output)
    assert parts.keys() == after_parts.keys()
    for name, (_, body) in parts.items():
        if name != 'SpEffectParam.param': assert body == after_parts[name][1], name
    # In-place PARAM edit permits only one float; all directories/names remain exact.
    before_table = parts['SpEffectParam.param'][1]
    allowed = set()
    for j in range(struct.unpack_from('<H', before_table, 10)[0]):
        rid, _, off, _ = struct.unpack_from('<iIQQ', before_table, 64 + 24*j)
        if rid == EFFECT_ID: allowed = set(range(off + 8, off + 12))
    assert len(allowed) == 4 and len(table) == len(before_table)
    assert all(a == b or i in allowed for i, (a,b) in enumerate(zip(before_table, table)))
    parsed = read_param(table, 'SpEffectParam')
    changed = [i for i in sp['rows'] if sp['rows'][i] != parsed['rows'][i]]
    assert changed == ([EFFECT_ID] if before != SECONDS else [])
    assert decode(parsed['rows'][EFFECT_ID]['data'], f) == SECONDS
    return output, {'goods_id': ITEM_ID, 'speffect_id': EFFECT_ID,
                    'field': 'effectEndurance', 'before': before, 'after': SECONDS,
                    'child_id': CHILD_ID, 'child_duration_seconds': 0.1,
                    'refresh_interval_seconds': 0.05, 'changed_rows': changed,
                    'unchanged_tables': 193, 'unchanged_speffect_rows': len(sp['rows'])-len(changed)}

def patch_text(blob):
    raw = dcx_unpack(blob); parts = bnd_entries(raw); updates = {}; records = []
    names = fmg_read(parts['GoodsName.fmg'][1])
    assert names[ITEM_ID] == "Baldachin's Blessing"
    for name in ['GoodsInfo.fmg', 'GoodsCaption.fmg']:
        entries = fmg_read(parts[name][1]); original = dict(entries)
        old = entries[ITEM_ID]; assert isinstance(old, str)
        if name == 'GoodsInfo.fmg':
            assert old in ('Uses FP to temporarily boost poise', OLD_INFO, INFO)
            entries[ITEM_ID] = INFO
        else:
            # Retain existing carry effect and flavor, append only use duration.
            base = old[:-len(OLD_SUFFIX)] if old.endswith(OLD_SUFFIX) else old
            entries[ITEM_ID] = base if base.endswith(CAPTION_SUFFIX) else base + CAPTION_SUFFIX
        changed = [i for i in entries if entries[i] != original[i]]
        assert changed in ([], [ITEM_ID])
        new = fmg_write(entries); assert fmg_read(new) == entries
        if changed: updates[name] = new
        records.append({'fmg': name, 'id': ITEM_ID, 'before': old, 'after': entries[ITEM_ID]})
    output = dcx_pack(bnd_patch(raw, updates)) if updates else blob
    checked = bnd_entries(dcx_unpack(output))
    for name, (_,body) in parts.items():
        if name not in updates: assert checked[name][1] == body
        else:
            old, new = fmg_read(body), fmg_read(checked[name][1])
            assert old.keys() == new.keys()
            assert all(old[i] == new[i] for i in old if i != ITEM_ID)
    return output, records

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--paramdefs', type=Path, required=True)
    p.add_argument('--item-dlc01', type=Path, required=True)
    p.add_argument('--item-dlc02', type=Path, required=True)
    args = p.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    key = bytes.fromhex(os.environ['ARMOR_REGULATION_KEY_HEX'])
    source = args.input.read_bytes(); header, raw = unpack(source, key)
    patched, params = patch_params(raw, args.paramdefs)
    assert patch_params(patched, args.paramdefs)[0] == patched
    compressed = zstd.ZstdCompressor(compression_params=zstd.ZstdCompressionParameters.from_level(
        15, window_log=16, write_content_size=False)).compress(patched)
    h = bytearray(header); struct.pack_into('>II', h, 28, len(patched), len(compressed))
    plain = bytes(h) + compressed; plain += bytes(-len(plain) % 16)
    iv = bytes(16); enc = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    result = iv + enc.update(plain) + enc.finalize(); assert unpack(result,key)[1] == patched
    name = '07_Baldachin_2min_20261002_regulation.bin'
    (args.output/name).write_bytes(result)
    audit = {'scope': 'normal Baldachin use buff only', 'param_version':'11711000',
             'input_sha256':sha(source), 'output_sha256':sha(result),
             'output_bytes':len(result), 'parameters':params, 'texts':[],
             'checks':['193 other tables unchanged','only effect 503355 duration changed',
                       'Goods, child effects, Radiant variant and all other rows unchanged',
                       'metadata retained; compact BND; idempotence; encrypted round trip',
                       'text only GoodsInfo/Caption 3360; all other entries unchanged'],
             'game_validation':'not run'}
    for label, path in [('dlc01',args.item_dlc01),('dlc02',args.item_dlc02)]:
        blob=path.read_bytes(); edited, texts=patch_text(blob)
        assert patch_text(edited)[0] == edited
        output='07_Baldachin_2min_20261002_engus_item_'+label+'.msgbnd.dcx'
        (args.output/output).write_bytes(edited)
        audit['texts'].append({'input_sha256':sha(blob),'output_sha256':sha(edited),'output':output,'rows':texts})
    (args.output/'07_Baldachin_2min_20261002_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:audit[k] for k in ['output_sha256','output_bytes','parameters','game_validation']}))

if __name__ == '__main__':main()
