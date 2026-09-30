"""Stage restoration of Spectral Steed Whistle usage settings."""
from __future__ import annotations

import csv
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / 'work'))
from analyze_regulation import read_bnd
from field_diff import defs, fields, decode
from build_v04 import decrypt_official
from build_v05 import active_rows, encrypt_native

SOURCE = ROOT / 'work/pending_remembrance_params.bnd'
OFFICIAL = ROOT / 'work/vanilla_117.bnd'
OUT = ROOT / 'work/pending_torrent.bnd'
REG = ROOT / 'output/pending_torrent_regulation.bin'


def main():
    data = bytearray(SOURCE.read_bytes())
    _, mod = read_bnd(SOURCE)
    _, vanilla = read_bnd(OFFICIAL)
    table = 'EquipParamGoods'
    rid = 130  # Spectral Steed Whistle; ID 181 is a separate variant.
    old = mod[table]['rows'][rid]['data']
    expected = vanilla[table]['rows'][rid]['data']
    assert len(old) == len(expected)
    f = {v[0]: v for v in fields(defs()[mod[table]['ptype']])[0]}
    differences = [(key, decode(old, spec), decode(expected, spec))
                   for key, spec in f.items() if decode(old, spec) != decode(expected, spec)]
    assert {r[0] for r in differences} == {'yesNoDialogMessageId', 'opmeMenuType', 'pad3'}, differences
    assert decode(expected, f['yesNoDialogMessageId']) == 20000800
    assert decode(expected, f['opmeMenuType']) == 9
    at = active_rows(data, table)[rid]
    data[at:at + len(expected)] = expected
    OUT.write_bytes(data)
    _, check = read_bnd(OUT)
    for t, meta in mod.items():
        for row_id, row in meta['rows'].items():
            assert check[t]['rows'][row_id]['data'] == (expected if (t, row_id) == (table, rid) else row['data'])
    with (ROOT / 'changes/pending_torrent.csv').open('w', encoding='utf-8-sig', newline='') as fp:
        w = csv.writer(fp)
        w.writerow(('参数表', '行ID', '字段', '原值', '恢复值'))
        w.writerows((table, rid, *r) for r in differences)
    template, _ = decrypt_official((ROOT.parent / 'upload/regulation.bin').read_bytes())
    encrypted = encrypt_native(template, bytes(data))
    assert decrypt_official(encrypted)[1] == bytes(data)
    REG.write_bytes(encrypted)
    print('restored Spectral Steed Whistle row', rid, 'changed fields', differences)


if __name__ == '__main__':
    main()
