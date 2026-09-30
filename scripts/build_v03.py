"""Add vanilla 1.17.1-only PARAM rows to the Ascended v0.2 binder.

This intentionally retains all shared Ascended rows.  It is a test branch:
native current-game menu text and player motion files take precedence, while
the owner's installed game supplies any paid expansion assets and entitlement.
"""

from __future__ import annotations

import collections
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import zipfile

import zstandard as zstd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_regulation import read_bnd

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'inputs/Ascended_优化版_v0.2_完整包.zip'
VANILLA = ROOT / 'inputs/vanilla_1.17.1.bnd'
WORK = ROOT / 'work'
OUT = ROOT / 'output'
PREFIX = 'Elden_Ascended_Mod_Age of the Endless Mod/'
KEY = bytes.fromhex('99 BF FC 36 6A 6B C8 C6 F5 82 7D 09 36 02 D6 76 '
                    'C4 28 92 A0 1C 20 7F B0 24 D3 AF 4E 49 3F EF 99')
EXCLUDE_SUFFIXES = (
    '/chr/c0000.anibnd.dcx', '/action/script/c0000.hks',
    '/item.msgbnd.dcx', '/menu.msgbnd.dcx',
)


def decrypt(blob: bytes):
    iv, ct = blob[:16], blob[16:]
    dec = Cipher(algorithms.AES(KEY), modes.CBC(iv)).decryptor()
    p = PKCS7(128).unpadder()
    dcx = p.update(dec.update(ct) + dec.finalize()) + p.finalize()
    assert dcx[:4] == b'DCX\0' and dcx[0x28:0x2c] == b'ZSTD'
    expected, compressed = struct.unpack_from('>II', dcx, 0x1c)
    assert len(dcx) == 0x4c + compressed
    with zstd.ZstdDecompressor().stream_reader(io.BytesIO(dcx[0x4c:])) as reader:
        raw = reader.read()
    assert len(raw) == expected and raw[:4] == b'BND4'
    return dcx, raw


def encrypt(dcx_template: bytes, raw: bytes):
    params = zstd.ZstdCompressionParameters.from_level(15, window_log=16,
                                                       write_content_size=False)
    comp = zstd.ZstdCompressor(compression_params=params).compress(raw)
    dcx = bytearray(dcx_template[:0x4c])
    struct.pack_into('>II', dcx, 0x1c, len(raw), len(comp))
    iv = os.urandom(16)
    pad = PKCS7(128).padder()
    payload = pad.update(bytes(dcx) + comp) + pad.finalize()
    enc = Cipher(algorithms.AES(KEY), modes.CBC(iv)).encryptor()
    return iv + enc.update(payload) + enc.finalize()


def binder_headers(raw: bytes):
    result = {}
    count = struct.unpack_from('<I', raw, 12)[0]
    for i in range(count):
        head = 0x40 + i * 36
        flag, _, size, orig_size, offset, ident, nameoff = struct.unpack_from(
            '<IIQQIII', raw, head)
        assert flag == 0x40 and size == orig_size and ident == i
        end = nameoff
        while raw[end:end+2] != b'\0\0':
            end += 2
        name = raw[nameoff:end].decode('utf-16le').split('\\')[-1].removesuffix('.param')
        result[name] = (head, offset, size)
    return result


def insert_rows(param: bytes, updates: dict[int, bytes], row_size: int):
    """Expand a modern 64-bit-offset PARAM, retaining every old row and name."""
    assert updates and len(updates) + struct.unpack_from('<H', param, 10)[0] < 65536
    flags = param[0x2d]
    assert flags & 0x80 and flags & 4
    first, width = 0x40, 24
    count = struct.unpack_from('<H', param, 10)[0]
    old_end = first + width * count
    delta = width * len(updates)
    entries = []
    for i in range(count):
        rid, reserved, dataoff, nameoff = struct.unpack_from('<iIQQ', param, first + i*width)
        assert rid not in updates, (rid, reserved)
        assert reserved == 0, (rid, reserved)
        entries.append((rid, dataoff + delta, nameoff + delta if nameoff else 0))
    # The new rows are placed beyond the old string table, preserving old bytes
    # and offsets.  Each new row references a shared empty UTF-16 name.
    base = bytearray(param[:old_end] + bytes(delta) + param[old_end:])
    for h in (0, 0x10, 0x30):
        old = struct.unpack_from('<Q', base, h)[0]
        if old >= old_end:
            struct.pack_into('<Q', base, h, old + delta)
    struct.pack_into('<H', base, 10, count + len(updates))
    empty_name = len(base)
    base.extend(b'\0\0')
    while len(base) % 8:
        base.append(0)
    for rid in sorted(updates):
        assert len(updates[rid]) == row_size
        entries.append((rid, len(base), empty_name))
        base.extend(updates[rid])
    assert len(entries) == count + len(updates)
    for i, (rid, dataoff, nameoff) in enumerate(sorted(entries, key=lambda x: x[0])):
        struct.pack_into('<iIQQ', base, first + i*width, rid, 0, dataoff, nameoff)
    return bytes(base)


def main():
    OUT.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=True)
    with zipfile.ZipFile(SOURCE) as source:
        assert source.testzip() is None
        top = PREFIX + 'regulation.bin'
        nested = PREFIX + 'ModEngine/mod/regulation.bin'
        assert source.read(top) == source.read(nested)
        dcx, baseline = decrypt(source.read(top))
        (WORK/'v02.bnd').write_bytes(baseline)
        version, asc = read_bnd(WORK/'v02.bnd')
        vanilla_version, vanilla = read_bnd(VANILLA)
        assert version == '11601000' and vanilla_version == '11711000'
        assert set(asc) == set(vanilla) and len(asc) == 194

        # In the 664-byte EquipParamWeapon row, residentSpEffectId2 is a signed
        # 32-bit value at byte 88. Check both the official empty slot and an
        # existing Ascended weapon before applying it to new weapon rows.
        effect_offset = 88
        assert struct.unpack_from('<i', asc['EquipParamWeapon']['rows'][1000000]['data'], effect_offset)[0] == 6202065
        imported = {}
        payloads = {}
        weapon_effect_count = 0
        for table in asc:
            new_ids = sorted(vanilla[table]['rows'].keys() - asc[table]['rows'].keys())
            if not new_ids:
                continue
            assert asc[table]['ptype'] == vanilla[table]['ptype']
            assert asc[table]['row_size'] == vanilla[table]['row_size']
            entries = {}
            for rid in new_ids:
                data = bytearray(vanilla[table]['rows'][rid]['data'])
                if table == 'EquipParamWeapon':
                    assert struct.unpack_from('<i', data, effect_offset)[0] == -1
                    struct.pack_into('<i', data, effect_offset, 6202065)
                    weapon_effect_count += 1
                entries[rid] = bytes(data)
            imported[table] = new_ids
            payloads[table] = entries
        assert len(imported['EquipParamWeapon']) == 82
        assert weapon_effect_count == 82
        assert imported['BaseChrSelectMenuParam'] == [2010, 2011]
        assert imported['CharMakeMenuListItemParam'] == [100210, 100211]
        assert all(x in imported['CharaInitParam'] for x in (3010, 3011, 3120, 3121, 3122, 3123))

        raw = bytearray(baseline)
        binder = binder_headers(baseline)
        for table, entries in payloads.items():
            head, offset, length = binder[table]
            param = insert_rows(baseline[offset:offset+length], entries,
                                asc[table]['row_size'])
            while len(raw) % 16:
                raw.append(0)
            new_offset = len(raw)
            assert new_offset < 2**32
            raw.extend(param)
            struct.pack_into('<QQI', raw, head+8, len(param), len(param), new_offset)
        result = bytes(raw)
        reg = encrypt(dcx, result)
        assert decrypt(reg)[1] == result

        (WORK/'v03.bnd').write_bytes(result)
        check_version, check = read_bnd(WORK/'v03.bnd')
        assert check_version == version and check.keys() == asc.keys()
        for table in asc:
            for rid, rec in asc[table]['rows'].items():
                assert check[table]['rows'][rid]['data'] == rec['data'], (table,rid)
            assert check[table]['rows'].keys() == (asc[table]['rows'].keys() | vanilla[table]['rows'].keys())
            for rid in imported.get(table, []):
                assert check[table]['rows'][rid]['data'] == payloads[table][rid], (table,rid)

        changed = {top: reg, nested: reg}
        dropped = []
        for info in source.infolist():
            n = info.filename
            if n.startswith(PREFIX + 'ModEngine/mod/') and n.endswith(EXCLUDE_SUFFIXES):
                dropped.append(n)
        assert len(dropped) >= 30

        notes = OUT/'Ascended_优化版_v0.3_测试说明.md'
        notes.write_text(f'''# Ascended v0.3 新版装备和职业测试包

基于 v0.2 的平衡参数制作。官方 1.17.1 提供了两项新增开局职业与新版装备。本包保持 Ascended 共有参数行原样，向旧版参数容器中增加 **{sum(map(len,imported.values()))} 项仅新版原版才有的参数行**（共 {len(imported)} 张参数表），其中武器强化阶段等武器行为 **82 行**、新防具 **18 行**、职业选择 **2 行**，以及起始装备、战技、子弹、商店、掉落、面容等相关行。82 行新武器均接入 v0.2 的常驻 1.5 倍玩家效果。

## 安装

1. **必须有当前 PC 版游戏 1.17.1，以及你自己合法拥有并安装的 Tarnished Pack。** 本包不含 DLC 模型、图片、文本和游戏程序，也不会解除 DLC 权限。若游戏没有相应资源与权限，角色可能不可选、装备模型或图标可能缺失。
2. 备份存档与旧 MOD。将完整包解压到**新文件夹**，从本包 `ModEngine` 中启动测试。不要直接覆盖旧 v0.2 文件夹，因为旧版的玩家动作和文本文件需要真正移走，覆盖解压不会删除它们。
3. 本测试包移除了旧版 `c0000.anibnd.dcx`、`c0000.hks` 和各语言 `item/menu.msgbnd.dcx` 覆盖，让游戏使用目前安装的新版玩家动作和官方名称。由此 Ascended 自定义玩家动作和装备文字可能失去；怪物、地图和其他脚本文件仍取自 v0.2。
4. 新建角色检查“伊杜斯骑士 / 重装骑士”（游戏中的名称以你的官方语言文本为准）是否出现、起始装备与属性是否正常，再检查新武器普通攻击、战技、升级、商店与地图拾取。建议离线测试并记录异常位置和截图。

## 范围和限制

- 1.16 参数容器内增加新版独有行，保留 v0.2 的 1.5 倍玩家倍率、敌方血量抗性、失衡与弹反试验；**这不是对整个 MOD 的 1.17.1 迁移**。
- 新角色是否出现在菜单还可能受 DLC 授权及引擎内逻辑影响。新版地图事件、商人和地图资源由你已安装的官方游戏提供；若 MOD 中旧地图或事件覆盖相同路径，部分新增拾取物可能仍无法出现。
- 目前仅完成参数结构和依赖的静态核对，未在游戏内加载测试。若开局职业不可选或某把武器的战技失效，请记录职业／武器名称、发生场景、所用游戏版本与启动方式，便于按实际报错继续修正。

本包没有重打包任何官方 DLC 资源；已拥有的官方内容始终由玩家自己的游戏安装加载。
''', encoding='utf-8')

        package = OUT/'Ascended_优化版_v0.3_新版武器职业测试包.zip'
        with zipfile.ZipFile(package, 'w') as out:
            for info in source.infolist():
                if info.filename in dropped:
                    continue
                data = changed.get(info.filename)
                out.writestr(copy.copy(info), source.read(info) if data is None else data)
            out.write(notes, PREFIX + notes.name)
        # A list of exact row IDs and removed overrides makes the test scope inspectable.
        manifest = {
            'source': SOURCE.name,
            'version': version,
            'official_reference_version': vanilla_version,
            'imported_rows': {t: {'count':len(ids), 'ids':ids} for t,ids in imported.items()},
            'imported_row_count': sum(map(len, imported.values())),
            'new_weapon_effect_rows': weapon_effect_count,
            'dropped_mod_overrides': dropped,
            'regulation_sha256': hashlib.sha256(reg).hexdigest(),
            'package_sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
        }
        (OUT/'v03_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'tables':len(imported), 'rows':manifest['imported_row_count'],
                          'weapon_rows':weapon_effect_count, 'removed_overrides':len(dropped),
                          'zip_bytes':package.stat().st_size}, ensure_ascii=False))


if __name__ == '__main__':
    main()
