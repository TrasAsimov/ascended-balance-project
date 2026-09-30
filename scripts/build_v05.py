"""Apply verified player-facing fixes to the compact native 1.17.1 binder.

The text-resource repair is tracked separately: the game text archives are
Kraken-compressed and need editable FMG sources for localization.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import struct

import zstandard as zstd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from analyze_regulation import read_bnd
from build_v03 import KEY, binder_headers
from build_v04 import decrypt_official

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / 'work'
OUT = ROOT / 'output'
VANILLA_REG = ROOT / 'inputs/vanilla_1.17.1_regulation.bin'


def active_rows(raw: bytes, table: str) -> dict[int, int]:
    _, off, length = binder_headers(raw)[table]
    count = struct.unpack_from('<H', raw, off + 10)[0]
    rows = {}
    for i in range(count):
        rid, _, dataoff, _ = struct.unpack_from('<iIQQ', raw, off + 0x40 + i * 24)
        if rid in rows:
            raise ValueError(f'duplicate row ID in {table}: {rid}')
        rows[rid] = off + dataoff
    return rows


def compact(raw: bytes, official: bytes) -> bytes:
    first = min(x[1] for x in binder_headers(official).values())
    result = bytearray(official[:first])
    count = struct.unpack_from('<I', raw, 12)[0]
    for i in range(count):
        head = 0x40 + i * 36
        size = struct.unpack_from('<Q', raw, head + 8)[0]
        old_offset = struct.unpack_from('<I', raw, head + 24)[0]
        while len(result) % 16:
            result.append(0)
        new_offset = len(result)
        result.extend(raw[old_offset:old_offset + size])
        struct.pack_into('<QQI', result, head + 8, size, size, new_offset)
    return bytes(result)


def encrypt_native(dcx_template: bytes, raw: bytes) -> bytes:
    params = zstd.ZstdCompressionParameters.from_level(
        15, window_log=16, write_content_size=False)
    compressed = zstd.ZstdCompressor(compression_params=params).compress(raw)
    dcx = bytearray(dcx_template[:0x4c])
    struct.pack_into('>II', dcx, 0x1c, len(raw), len(compressed))
    plaintext = bytes(dcx) + compressed
    plaintext += bytes((-len(plaintext)) % 16)
    iv = bytes(16)
    enc = Cipher(algorithms.AES(KEY), modes.CBC(iv)).encryptor()
    return iv + enc.update(plaintext) + enc.finalize()


def main():
    OUT.mkdir(exist_ok=True)
    official_encrypted = VANILLA_REG.read_bytes()
    official_dcx, official = decrypt_official(official_encrypted)
    source = compact((WORK/'v04.bnd').read_bytes(), official)
    (WORK/'v05_source.bnd').write_bytes(source)
    _, old = read_bnd(WORK/'v05_source.bnd')
    (WORK/'v05_official.bnd').write_bytes(official)
    _, vanilla = read_bnd(WORK/'v05_official.bnd')
    assert len(old) == len(vanilla) == 194
    result = bytearray(source)

    # The new 264-byte layout keeps baseAccSlotNum at byte 13.
    assert old['PlayerCommonParam']['row_size'] == 264
    player = active_rows(source, 'PlayerCommonParam')[0]
    assert result[player + 13] == 1
    result[player + 13] = 4

    # HUD gauge lengths are scaled by the displayed maximum limits, not the
    # character's actual HP/FP/stamina. Twice the official limit halves the
    # length for a given resource amount.
    assert old['MenuCommonParam']['row_size'] == 264
    menu = active_rows(source, 'MenuCommonParam')[0]
    hud_limits = {}
    for offset, label in ((8, 'HP'), (12, 'FP'), (16, 'stamina')):
        before = struct.unpack_from('<i', result, menu + offset)[0]
        expected = struct.unpack_from('<i', vanilla['MenuCommonParam']['rows'][0]['data'], offset)[0]
        assert before == expected and before > 0
        after = before * 2
        struct.pack_into('<i', result, menu + offset, after)
        hud_limits[label] = {'before':before, 'after':after}

    # Restore the original skill assigned to every official weapon. Keep all
    # other weapon bytes, including the planned 1.5x effect and upgrades.
    weapon_rows = active_rows(source, 'EquipParamWeapon')
    changed_weapons = []
    for rid, rec in vanilla['EquipParamWeapon']['rows'].items():
        if rid not in weapon_rows:
            continue
        off = weapon_rows[rid] + 408
        original = rec['data'][408:412]
        if result[off:off+4] != original:
            changed_weapons.append(rid)
            result[off:off+4] = original

    # SwordArtsParam contains skill rules and FP costs; Gem stores the skills
    # on Ashes of War. Both must match the corresponding official rows.
    restored = {}
    for table in ('SwordArtsParam', 'EquipParamGem'):
        rows = active_rows(source, table)
        size = old[table]['row_size']
        assert size == vanilla[table]['row_size']
        changed = []
        for rid, rec in vanilla[table]['rows'].items():
            if rid not in rows:
                continue
            at = rows[rid]
            if result[at:at+size] != rec['data']:
                result[at:at+size] = rec['data']
                changed.append(rid)
        restored[table] = changed

    built = bytes(result)
    (WORK/'v05.bnd').write_bytes(built)
    version, check = read_bnd(WORK/'v05.bnd')
    assert version == '11711000'
    assert check['PlayerCommonParam']['rows'][0]['data'][13] == 4
    for off, label in ((8, 'HP'), (12, 'FP'), (16, 'stamina')):
        assert struct.unpack_from('<i',check['MenuCommonParam']['rows'][0]['data'],off)[0] == hud_limits[label]['after']
    for rid, rec in vanilla['EquipParamWeapon']['rows'].items():
        if rid in check['EquipParamWeapon']['rows']:
            assert check['EquipParamWeapon']['rows'][rid]['data'][408:412] == rec['data'][408:412]
    for table in restored:
        for rid, rec in vanilla[table]['rows'].items():
            if rid in check[table]['rows']:
                assert check[table]['rows'][rid]['data'] == rec['data']
    assert len(changed_weapons) == 33

    encrypted = encrypt_native(official_dcx, built)
    assert decrypt_official(encrypted)[1] == built
    (OUT/'v05_pending_text_regulation.bin').write_bytes(encrypted)
    manifest = {
        'status':'staged; awaiting new class name/item text resources and further player feedback',
        'talisman_initial_slots':{'before':1,'after':4},
        'hud_display_limits':hud_limits,
        'weapon_skill_assignments_restored':changed_weapons,
        'official_skill_rows_restored':{k:len(v) for k,v in restored.items()},
        'mod_only_weapons_without_official_counterpart':[60000001,60002001],
        'regulation_sha256':hashlib.sha256(encrypted).hexdigest(),
    }
    (OUT/'v05_pending_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:manifest[k] for k in ('talisman_initial_slots','hud_display_limits','official_skill_rows_restored')},ensure_ascii=False))


if __name__ == '__main__':
    main()
