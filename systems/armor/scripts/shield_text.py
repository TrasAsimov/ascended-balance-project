"""Remove shield lore while retaining Ascended's existing mechanical effect lines."""
import re
from fmg import fmg_read, fmg_write


def is_shield(rid, name):
    # Native small/medium/greatshield families, thrusting shields, and the
    # separately numbered Shield of Night. Names cover mod-added shields.
    return bool(name and name != '[ERROR]' and
                (30000000 <= rid < 33000000 or 62500000 <= rid < 62530000 or
                 'shield' in name.lower()))


def effects_only(text):
    effects = []
    inside = False
    for line in (text or '').splitlines():
        match = re.match(r'^\s*Effect:[ \t]*(.*)$', line)
        if match:
            inside = True
            line = match[1]
        elif not inside:
            continue
        line = line.strip()
        # Some original captions accidentally label lore "Effect:" or put
        # a second numeric effect on an unlabelled line (e.g. Briar shield).
        # Keep numeric mechanic lines; do not promote lore to an effect.
        if re.match(r'^[+-]?\d+(?:\.\d+)?%?\s+\S', line):
            effects.append(line)
        elif line:
            inside = False
    return '\n\n'.join('Effect: ' + line for line in effects)


def patch_shields(parts, canonical=None):
    names = {rid: name for filename, (_, body) in parts.items()
             if filename.startswith('WeaponName')
             for rid, name in fmg_read(body).items()}
    updates, descriptions, no_effect = {}, {}, []
    for filename, (_, body) in parts.items():
        if not filename.startswith('WeaponCaption'):
            continue
        entries = fmg_read(body)
        for rid, text in list(entries.items()):
            if not is_shield(rid, names.get(rid)) or text is None:
                continue
            entries[rid] = (canonical or {}).get(str(rid), effects_only(text))
            descriptions[str(rid)] = entries[rid]
            if not entries[rid]:
                no_effect.append(rid)
        if fmg_read(body) != entries:
            updates[filename] = fmg_write(entries)
    return updates, descriptions, no_effect
