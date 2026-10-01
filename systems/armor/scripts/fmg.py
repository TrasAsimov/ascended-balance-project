import struct

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