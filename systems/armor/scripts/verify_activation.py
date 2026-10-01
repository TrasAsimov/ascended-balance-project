"""Independent applicability and constructor reachability regression checks.

Run after build.py and verify.py. --previous-bnd documents the omitted masks
in the prior build; this is not an engine or in-game result.
"""
from pathlib import Path
import argparse,json,struct,sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT.parents[1]/'scripts'))
from analyze_regulation import read_bnd
from field_diff import defs,fields,decode
from formats import Emevd,dcx_unpack

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--previous-bnd',type=Path)
    args=parser.parse_args()
    _,out=read_bnd(ROOT/'data/result.bnd');table=out['SpEffectParam']
    layout={f[0]:f for f in fields(defs()[table['ptype']])[0]}
    groups=json.loads((ROOT/'data/sets.json').read_text())
    rewards=[r for g in groups.values() for r in g['rewards']]
    old=None
    if args.previous_bnd:_,old=read_bnd(args.previous_bnd)
    required=['effectTargetSelf','effectTargetPlayer','effectTargetLive']
    mask_fields=['effectTargetSelf','effectTargetFriend','effectTargetPlayer','effectTargetAI','effectTargetLive','effectTargetGhost']
    excluded=[];changed=[]
    reward_ids={eid for r in rewards for eid in [r['effect'],*r['children']]}
    for eid in reward_ids:
        body=table['rows'][eid]['data']
        assert all(decode(body,layout[k])==1 for k in required),(eid,'inapplicable target')
        if old:
            before=old['SpEffectParam']['rows'][eid]['data']
            if any(decode(before,layout[k])==0 for k in required):excluded.append(eid)
            if before!=body:changed.append(eid)
    if old:
        for name,t in out.items():
            assert t['rows'].keys()==old[name]['rows'].keys()
            for eid,row in t['rows'].items():
                before=old[name]['rows'][eid]['data']
                if before==row['data']:continue
                assert name=='SpEffectParam' and eid in reward_ids,(name,eid)
                expected=bytearray(before)
                for key in mask_fields:
                    f=layout[key];raw=int.from_bytes(expected[f[2]:f[2]+f[3]],'little')
                    mask=((1<<f[4])-1)<<f[5]
                    expected[f[2]:f[2]+f[3]]=((raw&~mask)|(1<<f[5])).to_bytes(f[3],'little')
                assert expected==row['data'],('other reward values changed',eid)
    native=Emevd((ROOT/'inputs/reference/common.emevd').read_bytes())
    built=Emevd(dcx_unpack((ROOT/'ModEngine/mod/event/common.emevd.dcx').read_bytes()))
    before=next(e for e in native.events if e['id']==0)['ins']
    constructor=next(e for e in built.events if e['id']==0)['ins']
    prefix=constructor[:-len(before)]
    assert constructor[len(prefix):]==before and len(prefix)==len(rewards)==308
    called=[]
    for bank,index,raw,layer in prefix:
        assert (bank,index)==(2000,0) and layer is None
        slot,eid,arg=struct.unpack('<iII',raw);assert slot==arg==0
        called.append(eid)
    assert called==[r['event'] for r in rewards] and len(set(called))==len(called)
    # Exercise both actual native early exits. The old append placement never
    # reaches any new initialization in these scenarios; the prefix always does.
    def started(ins,other_world,flag2052):
        events=[]
        for bank,index,raw,_ in ins:
            if (bank,index)==(1003,14) and other_world:break
            if (bank,index)==(1003,2) and flag2052 and struct.unpack_from('<I',raw,4)[0]==2052:break
            if (bank,index)==(2000,0):
                eid=struct.unpack_from('<I',raw,4)[0]
                if eid in called:events.append(eid)
        return events
    old_constructor=before+prefix
    scenarios=[]
    for other in [False,True]:
        for flag in [False,True]:
            assert started(constructor,other,flag)==called
            old_count=len(started(old_constructor,other,flag))
            assert old_count==(0 if other or flag else len(called))
            scenarios.append({'other_world':other,'flag2052':flag,'previous_started':old_count,'new_started':len(called)})
    report={'required_wearer_masks_verified':len(reward_ids),'previous_inapplicable_rewards':len(excluded),'only_applicability_masks_changed_rows':len(changed),'initialized_rewards':len(called),'constructor_scenarios':scenarios,'game_validation':'not run; player reports current bug-fixed build enters game but set effects fail; installed hash not provided'}
    (ROOT/'data/activation_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
