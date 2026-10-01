"""Exercise the emitted heart instruction stream, not merely the formulas."""
import argparse
import json
from pathlib import Path
import random
import struct
from build_minor_boss_heart import *


def arguments(ins, specs):
    formats = {0:'B',1:'H',2:'I',3:'b',4:'h',5:'i',6:'f',8:'I'}
    args, pos = [], 0
    for arg in specs[ins[:2]]['args']:
        fmt = formats[arg['type']]
        size = struct.calcsize(fmt)
        pos += -pos % size
        args.append(struct.unpack_from('<'+fmt, ins[2], pos)[0])
        pos += size
    return args


def execute(program, flags, effects):
    flags, effects = set(flags), set(effects)
    pc = 0
    while pc < len(program):
        op, a = program[pc]
        pc += 1
        if op == (2004,21):
            assert a[0] == PLAYER
            effects.discard(a[1])
        elif op == (2004,8):
            assert a[0] == PLAYER
            effects.add(a[1])
        elif op == (2003,22):
            assert a[2] == 0
            flags.difference_update(range(a[0],a[1]+1))
        elif op == (2003,9):
            flags.symmetric_difference_update([a[0]])
        elif op == (1003,1):
            assert a[2] == 0
            if (a[3] in flags) == bool(a[1]):
                pc += a[0]
        elif op == (1000,4):
            assert a == [1]
            return flags,effects
        else:
            raise AssertionError(op)
    raise AssertionError('No restart')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--emedf',type=Path,required=True)
    p.add_argument('--common',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args = p.parse_args()
    manifest = load_manifest(ROOT/'data/minor_boss_heart.json')
    extra = extension(manifest,args.emedf)
    ev = Emevd(dcx_unpack(args.common.read_bytes()))
    event = next(e for e in ev.events if e['id']==REFRESH_EVENT)
    assert event['ins'][-len(extra):] == extra
    docs = json.loads(args.emedf.read_text())
    specs = {(b['index'],i['index']):i for b in docs['main_classes'] for i in b['instrs']}
    program = [(i[:2],arguments(i,specs)) for i in extra]
    boss_flags = [b['flag_id'] for b in manifest['bosses']]
    excluded = {b['flag_id'] for b in manifest['excluded_remembrance_bosses']}
    tiers = {PARENT_START+n for n in range(1,182)} | {SPELL_START+n for n in range(1,182)}
    untouched = {321412,321435,7200000,6202050}
    cases = []
    # Cover every count across several distinct subsets, and each boss alone.
    rng = random.Random(20261002)
    for n in range(182):
        cases.extend([set(boss_flags[:n]),set(boss_flags[-n:]) if n else set(),set(rng.sample(boss_flags,n))])
    cases.extend({f} for f in boss_flags)
    for i,killed in enumerate(cases):
        expected = untouched | ({PARENT_START+len(killed),SPELL_START+len(killed)} if killed else set())
        start_flags = killed | excluded | set(range(COUNTER_START,COUNTER_START+COUNTER_BITS))
        flags,effects = execute(program,start_flags,tiers|untouched|{BAYLE_PARENT,BAYLE_CHILD})
        assert effects == expected,(i,len(killed),effects)
        assert flags.intersection(boss_flags) == killed
        assert excluded <= flags
        number = sum((1<<bit) for bit in range(COUNTER_BITS) if COUNTER_START+bit in flags)
        assert number == len(killed)
        # Reusing the heart must refresh, never accumulate another tier.
        flags2,effects2 = execute(program,flags,effects)
        assert (flags2,effects2)==(flags,effects)
    # Explicit progression, death/reload-like empty active state, and NG+ reset.
    effects = untouched
    for n in [0,1,2,127,128,180,181,181,1,0]:
        flags,effects = execute(program,set(boss_flags[:n]),effects)
        assert effects == untouched | ({PARENT_START+n,SPELL_START+n} if n else set())
    # Bayle must receive one remembrance tier without changing the minor count.
    bayle_cases = 0
    for n in [0,1,127,181]:
        killed=set(boss_flags[:n])
        for present in [False,True]:
            f=killed | ({2054390800} if present else set())
            flags,effects=execute(program,f,tiers|untouched|{BAYLE_PARENT,BAYLE_CHILD})
            expected=untouched | ({PARENT_START+n,SPELL_START+n} if n else set()) | ({BAYLE_PARENT,BAYLE_CHILD} if present else set())
            assert effects==expected
            assert execute(program,flags,effects)==(flags,effects)
            bayle_cases+=1
    result = {'bayle_separate_and_repeat_cases':bayle_cases,'instruction_simulation_cases':len(cases),'repeat_use_cases':len(cases),
              'all_counts_0_to_181':True,'each_boss_individually':181,
              'excluded_remembrance_flags_ignored':25,'stale_tiers_cleared':True,
              'scratch_counter_reset':True,'progression_and_reset_cases':10,
              'game_validation':'not run'}
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
