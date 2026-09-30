"""Build a targeted Simplified Chinese item-text overlay from owned game files.

The inputs must be the user's matching 1.17.1 zhocn item_dlc01/02 BND4
archives, or their DFLT-wrapped DCX forms. Kraken DCX must first be unpacked
with a tool that uses the owner's game Oodle DLL. No original game text is
stored in this repository.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import struct
import zlib

NORMAL_BASE = (2952, 2953, 2955, 2956, 2957, 2958, 2960, 2961, 2962, 2963, 2964)
DLC = (2002900, 2002901, 2002902, 2002903, 2002904,
       2002905, 2002907, 2002908, 2002909, 2002910)
HEART_ID = 2001431
MARK = "【Ascended Balance 效果】"
NORMAL_EFFECT = (
    "最大生命值提高5%；物理与各属性攻击力提高2.5%；魔法与祷告伤害提高2.5%。"
    "符合条件的每位追忆首领各提供一层。使用后不会消耗。"
)
ACCESSORY = {
    2090: ("致命一击伤害提高400%。", "大幅提高致命一击伤害"),
    2120: ("连续攻击的最后一击伤害提高150%。", "提高连续攻击最后一击的伤害"),
    2130: ("蓄力攻击伤害提高320%。", "大幅提高蓄力攻击伤害"),
    2140: ("魔法与祷告攻击力提高300%；最终伤害仍受目标防御力影响。", "大幅提高魔法与祷告攻击力"),
    2150: ("箭矢与弩箭伤害提高100%；弓本体和弹药的其他加成另行计算。", "提高箭矢与弩箭的伤害"),
    2180: ("跳跃攻击伤害提高150%。", "大幅提高跳跃攻击伤害"),
    2200: ("防御反击伤害提高300%。", "大幅提高防御反击伤害"),
    4100: ("格挡时的精力消耗减少90%。", "大幅减少格挡时的精力消耗"),
}
HEART = {
    "GoodsName_dlc01.fmg": "强化之魂",
    "GoodsInfo_dlc01.fmg": "使用后刷新已击败追忆首领的力量",
    "GoodsCaption_dlc01.fmg": (
        "旅程开始时获得的强化之魂。\n\n"
        "使用后，根据已经击败且符合条件的追忆首领刷新增益。"
        "每位首领各提供最大生命值5%、物理与各属性攻击力2.5%，"
        "以及魔法与祷告伤害2.5%的增益。未击败任何符合条件的首领时没有效果。\n\n"
        "使用后不会消耗；与同一追忆的单独增益不叠加。"
        "四种特殊追忆保留各自的特殊效果。"
    ),
}
EXISTING_ENGLISH_HEART = {
    "GoodsName_dlc01.fmg": "Empowered Soul",
    "GoodsInfo_dlc01.fmg": "Refreshes power from defeated remembrance bosses",
    "GoodsCaption_dlc01.fmg": "An empowered soul granted at the beginning of the journey.",
}


def unpack(blob: bytes) -> bytes:
    if blob[:4] == b"BND4":
        return blob
    if blob[:4] == b"DCX\0" and blob[0x28:0x2c] == b"DFLT":
        expected, packed = struct.unpack_from(">II", blob, 0x1c)
        raw = zlib.decompress(blob[0x4c:0x4c + packed])
        assert len(raw) == expected and raw[:4] == b"BND4"
        return raw
    raise ValueError("输入是 Kraken 或未知格式；请先用匹配游戏版本的工具解成 BND4，不能用旧版简中文本包覆盖。")


def pack_dflt(raw: bytes) -> bytes:
    # Standard 0x4c-byte DFLT DCX header, matching the format already used
    # by this project's English overlays.
    header = bytearray.fromhex(
        "44 43 58 00 00 01 10 00 00 00 00 18 00 00 00 24"
        " 00 00 00 44 00 00 00 4c 44 43 53 00 00 00 00 00"
        " 00 00 00 00 44 43 50 00 44 46 4c 54 00 00 00 20"
        " 09 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
        " 00 01 01 00 44 43 41 00 00 00 00 08"
    )
    assert len(header) == 0x4c and header[0x28:0x2c] == b"DFLT"
    compressed = zlib.compress(raw, 9)
    struct.pack_into(">II", header, 0x1c, len(raw), len(compressed))
    header.extend(compressed)
    return bytes(header)


def fmg_read(raw: bytes) -> dict[int, str | None]:
    assert raw[:4] == b"\0\0\x02\0" and len(raw) == struct.unpack_from("<i", raw, 4)[0]
    groups, total = struct.unpack_from("<ii", raw, 12)
    pointers = struct.unpack_from("<q", raw, 24)[0]
    result: dict[int, str | None] = {}
    for i in range(groups):
        index, first, last, pad = struct.unpack_from("<iiiI", raw, 40 + i * 16)
        assert pad == 0
        for rid in range(first, last + 1):
            offset = struct.unpack_from("<q", raw, pointers + 8 * (index + rid - first))[0]
            if not offset:
                result[rid] = None
                continue
            end = offset
            while raw[end:end + 2] != b"\0\0":
                end += 2
            result[rid] = raw[offset:end].decode("utf-16le")
    assert len(result) == total
    return result


def fmg_write(entries: dict[int, str | None]) -> bytes:
    ids = sorted(entries)
    groups = []
    first = last = None
    start_index = 0
    for i, rid in enumerate(ids):
        if first is None:
            first = last = rid
            start_index = i
        elif rid == last + 1:
            last = rid
        else:
            groups.append((start_index, first, last))
            first = last = rid
            start_index = i
    if first is not None:
        groups.append((start_index, first, last))
    raw = bytearray(40 + 16 * len(groups) + 8 * len(ids))
    raw[:4] = b"\0\0\x02\0"
    raw[8] = 1
    struct.pack_into("<iiIqq", raw, 12, len(groups), len(ids), 255, 40 + 16 * len(groups), 0)
    for i, (index, begin, end) in enumerate(groups):
        struct.pack_into("<iiiI", raw, 40 + i * 16, index, begin, end, 0)
    ptrs = 40 + 16 * len(groups)
    for i, rid in enumerate(ids):
        if entries[rid] is not None:
            struct.pack_into("<q", raw, ptrs + i * 8, len(raw))
            raw.extend(entries[rid].encode("utf-16le") + b"\0\0")
    struct.pack_into("<i", raw, 4, len(raw))
    assert fmg_read(bytes(raw)) == entries
    return bytes(raw)


def bnd_parts(raw: bytes):
    assert raw[:4] == b"BND4"
    parts = {}
    for i in range(struct.unpack_from("<I", raw, 12)[0]):
        h = 0x40 + 36 * i
        _, _, size, _, off, _, nameoff = struct.unpack_from("<IIQQIII", raw, h)
        end = nameoff
        while raw[end:end + 2] != b"\0\0":
            end += 2
        name = raw[nameoff:end].decode("utf-16le").split("\\")[-1]
        parts[name] = (h, raw[off:off + size])
    return parts


def append_effect(existing: str, text: str) -> str:
    assert existing and MARK not in existing
    return existing.rstrip() + "\n\n" + MARK + "\n" + text


def patch_one(source: Path, out: Path) -> dict[str, int]:
    original = unpack(source.read_bytes())
    parts = bnd_parts(original)
    updates = {}
    counts = {}

    def edit(name, target_ids, transform):
        assert name in parts, f"缺少 {name}: {source}"
        records = fmg_read(parts[name][1]); before = dict(records)
        for rid in target_ids:
            assert rid in records, (name, rid)
            records[rid] = transform(rid, records[rid])
        changed = {rid for rid in records if records[rid] != before[rid]}
        assert changed == set(target_ids), (name, changed)
        updates[name] = fmg_write(records)
        counts[name] = len(changed)

    edit("AccessoryCaption.fmg", ACCESSORY,
         lambda rid, old: append_effect(old, ACCESSORY[rid][0]))
    edit("AccessoryInfo.fmg", (2140, 2150, 4100),
         lambda rid, old: ACCESSORY[rid][1])
    edit("GoodsCaption.fmg", NORMAL_BASE,
         lambda rid, old: append_effect(old, NORMAL_EFFECT))
    edit("GoodsCaption_dlc01.fmg", DLC,
         lambda rid, old: append_effect(old, NORMAL_EFFECT))
    for name, text in HEART.items():
        assert name in parts, (name, source)
        records = fmg_read(updates.get(name, parts[name][1]))
        previous = records.get(HEART_ID)
        assert previous in (None, "", text) or (
            isinstance(previous, str) and previous.startswith(EXISTING_ENGLISH_HEART[name])
        ), (name, HEART_ID, previous)
        records[HEART_ID] = text
        updates[name] = fmg_write(records)
        counts[name] = counts.get(name, 0) + 1

    result = bytearray(original)
    for name, (h, payload) in parts.items():
        if name not in updates:
            continue
        while len(result) % 16:
            result.append(0)
        offset = len(result)
        new = updates[name]
        result.extend(new)
        struct.pack_into("<QQI", result, h + 8, len(new), len(new), offset)
    checked = bnd_parts(bytes(result))
    assert all(checked[name][1] == payload for name, (_, payload) in parts.items() if name not in updates)
    assert all(fmg_read(checked[name][1]) == fmg_read(payload) for name, payload in updates.items())
    out.parent.mkdir(parents=True, exist_ok=True)
    packed = pack_dflt(bytes(result))
    assert unpack(packed) == bytes(result)
    out.write_bytes(packed)
    return counts


def main():
    p = argparse.ArgumentParser(description="Patch matching-version zhocn item texts only")
    p.add_argument("item_dlc01", type=Path, help="当前官方简中 item_dlc01.msgbnd.dcx 或解包后的 BND4")
    p.add_argument("item_dlc02", type=Path, help="当前官方简中 item_dlc02.msgbnd.dcx 或解包后的 BND4")
    p.add_argument("output_mod", type=Path, help="输出 MOD 根目录，例如 ModEngine/mod")
    args = p.parse_args()
    for variant, source in (("item_dlc01", args.item_dlc01), ("item_dlc02", args.item_dlc02)):
        out = args.output_mod / "msg" / "zhocn" / f"{variant}.msgbnd.dcx"
        counts = patch_one(source, out)
        print(out, counts)


if __name__ == "__main__":
    main()
