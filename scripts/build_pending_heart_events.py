"""Stage event source for a manually refreshed, single remembrance aggregator.

This emits DarkScript3 source only; a game-compatible compiled EMEVD and
in-game verification are required before inclusion in a release.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT.parent / '.tools/events_mod/common.emevd.dcx.js'
OUT = ROOT / 'work/pending_common.emevd.dcx.js'

# Goods ID, acquisition flags, existing normal remembrance effect.
BUFFS = (
    (2952, (510040,), 321424),
    (2953, (510210,), 321425),
    (2955, (510120, 12057190), 321426),
    (2956, (510160,), 321427),
    (2957, (510070,), 321428),
    (2958, (12057090,), 321429),
    (2960, (510110,), 321430),
    (2961, (510310,), 321431),
    (2962, (510330,), 321432),
    (2963, (510230,), 321433),
    (2964, (510080, 12037840), 321434),
    (2002905, (510400,), 321417),
    (2002907, (510430,), 321418),
    (2002901, (510460,), 321413),
    (2002910, (510480,), 321421),
    (2002909, (510550,), 321420),
    (2002908, (510560,), 321419),
    (2002904, (510600,), 321416),
    (2002902, (510620,), 321414),
    (2002900, (510640,), 321412),
    (2002903, (510900,), 321415),
)
assert len(BUFFS) == 21
assert len({entry[0] for entry in BUFFS}) == len({entry[2] for entry in BUFFS}) == 21

def main():
    source = SOURCE.read_bytes()
    newline = b'\r\n' if b'\r\n' in source else b'\n'
    raw = source.decode('utf-8-sig')
    assert '$InitializeEvent(0, 20007901);' not in raw
    assert '$Event(20007901,' not in raw and '$Event(20007902,' not in raw
    # Flag 60000 is set by the flask item-lot awarded after the Stranded Graveyard
    # awakening (m18_00_00_00 event 18000020). Old saves with the flag get one heart.
    anchor = '    $InitializeEvent(0, 6911);'
    assert raw.count(anchor) == 1
    raw = raw.replace(anchor, anchor + '\n    $InitializeEvent(0, 20007901);\n    $InitializeEvent(0, 20007902);')
    giver = '''$Event(20007901, Restart, function() {
    DisableNetworkSync();
    EndIf(!PlayerIsInOwnWorld());
    EndIf(EventFlag(699990));
    WaitFor(EventFlag(60000));
    DirectlyGivePlayerItem(ItemType.Goods, 2001431, 699990, 1);
});

'''
    checks = []
    for good, flags, effect in BUFFS:
        condition = ' || '.join(f'EventFlag({flag})' for flag in flags)
        checks.append(f'    // Goods {good}: one copy of effect {effect} when its boss reward flag is set.\n'
                      f'    if ({condition}) {{\n'
                      f'        SetSpEffect(10000, {effect});\n'
                      f'    }}')
    refresher = '''$Event(20007902, Restart, function() {
    DisableNetworkSync();
    WaitFor(PlayerIsInOwnWorld() && CharacterHasSpEffect(10000, 321422));
    ClearSpEffect(10000, 321422);
''' + '\n'.join(f'    ClearSpEffect(10000, {effect});' for _,_,effect in BUFFS) + '\n' + '\n'.join(checks) + '''
    RestartEvent();
});
'''
    raw += '\n' + giver + refresher
    OUT.write_bytes(newline.join(part.encode('utf-8') for part in raw.replace('\r\n', '\n').split('\n')))
    check = OUT.read_text(encoding='utf-8')
    assert check.count('DirectlyGivePlayerItem(ItemType.Goods, 2001431, 699990, 1)') == 1
    assert check.count('ClearSpEffect(10000, 321422)') == 1
    print('staged common EMEVD source', len(BUFFS), 'boss-linked effects')

if __name__ == '__main__':
    main()
