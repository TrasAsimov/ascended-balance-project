"""Stage Ascended's jump movement multiplier on the matching current-game HKS.

Input must be decompiled readable Lua from the user's current game version.
The old Ascended HKS must not be substituted: its skill mapping predates new gear.
"""
from pathlib import Path
import argparse


def main():
    p = argparse.ArgumentParser()
    p.add_argument("current_decompiled_hks", type=Path)
    p.add_argument("output_hks", type=Path)
    args = p.parse_args()
    blob = args.current_decompiled_hks.read_bytes()
    assert not blob.startswith(b"\x1bLua"), "Decompile the current HKS first"
    source = blob.decode("utf-8-sig")
    assert source.count("function Act_Jump()") == 1
    start = source.index("function Act_Jump()")
    end = source.find("\nfunction ", start + 1)
    if end < 0:
        end = len(source)
    body = source[start:end]
    anchor = "    local damage_type = env(202)\n"
    assert body.count(anchor) == 1
    assert "act(2001, 1.4)" not in body
    changed = body.replace(anchor, anchor + "    act(2001, 1.4)\n", 1)
    patched = source[:start] + changed + source[end:]
    assert patched.replace(changed, body, 1) == source
    args.output_hks.parent.mkdir(parents=True, exist_ok=True)
    args.output_hks.write_text(patched, encoding="utf-8", newline="\n")
    print(f"Wrote jump-only HKS: {args.output_hks}")


if __name__ == "__main__":
    main()
