"""Port compatible Ascended v0.3 PARAM rows into a native 1.17.1 binder.

This is an experimental compatibility build. Tables whose row layouts changed
are left at their official 1.17.1 values and reported in the manifest.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import zipfile

import zstandard as zstd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from analyze_regulation import read_bnd
from build_v03 import KEY, PREFIX, binder_headers, encrypt, insert_rows

ROOT = Path(__file__).resolve().parent.parent
VANILLA_REG = ROOT / 'inputs/vanilla_1.17.1_regulation.bin'
V03_ZIP = ROOT / 'inputs/Ascended_优化版_v0.3_新版武器职业测试包.zip'
WORK = ROOT / 'work'
OUT = ROOT / 'output'


def decrypt_official(blob: bytes) -> tuple[bytes, bytes]:
    assert len(blob) > 16 and (len(blob) - 16) % 16 == 0
    dec = Cipher(algorithms.AES(KEY), modes.CBC(blob[:16])).decryptor()
    padded = dec.update(blob[16:]) + dec.finalize()
    assert padded[:4] == b'DCX\0' and padded[0x28:0x2c] == b'ZSTD'
    expected, compressed = struct.unpack_from('>II', padded, 0x1c)
    end = 0x4c + compressed
    assert end <= len(padded) and not any(padded[end:])
    dcx = padded[:end]
    with zstd.ZstdDecompressor().stream_reader(io.BytesIO(dcx[0x4c:])) as reader:
        raw = reader.read()
    assert len(raw) == expected and raw[:4] == b'BND4'
    return dcx, raw


def patch_table(raw_param: bytes, original: dict, target: dict, table: str):
    size = target['row_size']
    assert size and size == original['row_size']
    result = bytearray(raw_param)
    flags = result[0x2d]
    assert flags & 0x80 and flags & 4
    count = struct.unpack_from('<H', result, 10)[0]
    assert count == target['declared_rows']
    patched = 0
    for i in range(count):
        rid, _, dataoff, _ = struct.unpack_from('<iIQQ', result, 0x40 + 24 * i)
        if rid in original['rows']:
            data = original['rows'][rid]['data']
            assert len(data) == size and dataoff + size <= len(result)
            result[dataoff:dataoff + size] = data
            patched += 1
        elif table == 'EquipParamWeapon':
            # v0.3 used the same resident effect for newly added weapons.
            if rid in NEW_WEAPONS:
                assert struct.unpack_from('<i', result, dataoff + 88)[0] == -1
                struct.pack_into('<i', result, dataoff + 88, 6202065)
    added = {rid: row['data'] for rid, row in original['rows'].items()
             if rid not in target['rows']}
    if added:
        result = bytearray(insert_rows(bytes(result), added, size))
    return bytes(result), patched, len(added)


NEW_WEAPONS: set[int] = set()


def main():
    WORK.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    top = PREFIX + 'regulation.bin'
    nested = PREFIX + 'ModEngine/mod/regulation.bin'
    with zipfile.ZipFile(V03_ZIP) as source:
        assert source.testzip() is None
        assert source.read(top) == source.read(nested)
        # The source binder is v0.3, including Ascended and the 426 new rows.
        from build_v03 import decrypt
        _, source_raw = decrypt(source.read(nested))
        official_dcx, official_raw = decrypt_official(VANILLA_REG.read_bytes())
        (WORK/'v03_source.bnd').write_bytes(source_raw)
        (WORK/'v04_official.bnd').write_bytes(official_raw)
        src_version, src = read_bnd(WORK/'v03_source.bnd')
        official_version, vanilla = read_bnd(WORK/'v04_official.bnd')
        assert (src_version, official_version) == ('11601000', '11711000')
        assert src.keys() == vanilla.keys() and len(src) == 194

        global NEW_WEAPONS
        # v0.3 contains these rows already, so identify them from its manifest.
        manifest03 = json.loads((ROOT/'inputs/v03_manifest.json').read_text(encoding='utf-8'))
        NEW_WEAPONS = set(manifest03['imported_rows']['EquipParamWeapon']['ids'])
        assert len(NEW_WEAPONS) == 82

        raw = bytearray(official_raw)
        headers = binder_headers(official_raw)
        skipped, stats = [], {}
        for table, target in vanilla.items():
            old = src[table]
            assert target['ptype'] == old['ptype'], table
            if target['row_size'] != old['row_size']:
                skipped.append({'table':table,'old_size':old['row_size'],
                                'official_size':target['row_size']})
                continue
            head, offset, length = headers[table]
            rebuilt, patched, added = patch_table(
                official_raw[offset:offset + length], old, target, table)
            if not patched and not added and table != 'EquipParamWeapon':
                continue
            while len(raw) % 16:
                raw.append(0)
            new_offset = len(raw)
            assert new_offset < 2 ** 32
            raw.extend(rebuilt)
            struct.pack_into('<QQI', raw, head + 8, len(rebuilt), len(rebuilt), new_offset)
            stats[table] = {'shared_rows_ported':patched,'ascended_only_rows':added}

        built = bytes(raw)
        (WORK/'v04.bnd').write_bytes(built)
        version, check = read_bnd(WORK/'v04.bnd')
        assert version == official_version
        skipped_names = {x['table'] for x in skipped}
        for table in src:
            expected = (vanilla[table]['rows'].keys() if table in skipped_names
                        else vanilla[table]['rows'].keys() | src[table]['rows'].keys())
            assert check[table]['rows'].keys() == expected, table
            if table in skipped_names:
                assert check[table]['rows'] == vanilla[table]['rows'], table
                continue
            for rid, row in src[table]['rows'].items():
                assert check[table]['rows'][rid]['data'] == row['data'], (table, rid)
        assert not [x for x in skipped if src[x['table']]['rows'].keys()
                    - vanilla[x['table']]['rows'].keys()]
        reg = encrypt(official_dcx, built)
        assert decrypt(reg)[1] == built

        notes = OUT/'Ascended_优化版_v0.4_测试说明.md'
        notes.write_text('''# Ascended v0.4：1.17.1 原生参数容器兼容测试

v0.3 加载时报告 “Failed to save game / Save data is corrupted”。用户隔离测试显示：原版、禁用 MOD 加载器、移开 MOD regulation.bin 均可启动，因此本版以玩家提供的官方 1.17.1 容器重建参数包。

将本完整包解压到新文件夹，备份存档，从本包 ModEngine/launchmod_eldenring.bat 离线启动；不要覆盖旧版。先检查是否能进入角色选择或已有存档，然后再测试 Ascended 的平衡与新增武器。

本版把 184 张布局相同的参数表中共有行沿用 v0.3，并保留官方新增行；同时移植 Ascended 独有行。10 张布局已变化的表保留 1.17.1 原版内容，因此其中的 Ascended 改动暂时缺失。其他共有行整体沿用旧版值，仍可能覆盖部分官方新版改动。此包只通过静态解析和回读验证，尚未经过游戏内验证。如果仍报存档损坏，请停止使用并反馈截图，不要删除或覆盖存档。

本包不含游戏程序或官方 DLC 权限；随机化未开始。完整差异见仓库 docs/v0.4.md 和 changes/v0.4_manifest.json。
''', encoding='utf-8')
        package = OUT/'Ascended_优化版_v0.4_1.17.1兼容测试包.zip'
        with zipfile.ZipFile(package, 'w') as out:
            for info in source.infolist():
                if info.filename.endswith('v0.3_测试说明.md'):
                    continue
                data = reg if info.filename in (top, nested) else source.read(info)
                out.writestr(copy.copy(info), data)
            out.write(notes, PREFIX + notes.name)

        manifest = {
            'source_version':src_version,'base_version':official_version,
            'shared_rows_ported':sum(v['shared_rows_ported'] for v in stats.values()),
            'ascended_only_rows':sum(v['ascended_only_rows'] for v in stats.values()),
            'skipped_layout_changed_tables':skipped,'table_stats':stats,
            'native_new_weapons_with_effect':len(NEW_WEAPONS),
            'regulation_sha256':hashlib.sha256(reg).hexdigest(),
            'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
        }
        (OUT/'v04_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:manifest[k] for k in ('shared_rows_ported','ascended_only_rows','skipped_layout_changed_tables','native_new_weapons_with_effect')},ensure_ascii=False))


if __name__ == '__main__':
    main()
