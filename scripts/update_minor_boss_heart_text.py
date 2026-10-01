"""Replace only the reusable heart's info/caption in owned English archives."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from formats import bnd_entries,bnd_patch,dcx_pack,dcx_unpack
from fmg import fmg_read,fmg_write

HEART_ID = 2001431
TEXT = {
    'GoodsInfo_dlc01.fmg':'Refreshes bonuses from defeated bosses',
    'GoodsCaption_dlc01.fmg':(
        'Use to refresh bonuses from defeated bosses.\n'
        'Minor bosses (excluding Bayle): max HP, FP and stamina +0.2% each.\n'
        'Weapon attack power and sorcery/incantation damage +0.1% each.\n'
        'These bonuses add together; repeat use only refreshes.\n'
        'Bayle grants a remembrance-tier bonus. Not consumed on use.'),
}
ZH = {
    'GoodsName_dlc01.fmg':'强化之魂',
    'GoodsInfo_dlc01.fmg':'刷新已击败首领的增益',
    'GoodsCaption_dlc01.fmg':(
        '使用后刷新已击败首领的增益。\n'
        '每场小首领（贝勒除外）：生命、法力、精力上限各+0.2%。\n'
        '武器攻击力、魔法/祷告伤害各+0.1%。\n'
        '上述奖励加算；重复使用仅刷新。\n'
        '贝勒按追忆首领奖励；使用后不消耗。'),
}


def patch(blob):
    parts = bnd_entries(dcx_unpack(blob))
    if all(fmg_read(parts[name][1]).get(HEART_ID)==text for name,text in TEXT.items()):
        return blob
    updates = {}
    before = {}
    for name,text in TEXT.items():
        d = fmg_read(parts[name][1])
        assert HEART_ID in d
        before[name] = dict(d)
        d[HEART_ID] = text
        updates[name] = fmg_write(d)
    result = dcx_pack(bnd_patch(dcx_unpack(blob),updates))
    after = bnd_entries(dcx_unpack(result))
    assert parts.keys()==after.keys()
    for name,(_,original) in parts.items():
        if name not in updates:
            assert after[name][1]==original
        else:
            d=fmg_read(after[name][1])
            assert d[HEART_ID]==TEXT[name]
            assert d.keys()==before[name].keys()
            assert all(d[k]==v for k,v in before[name].items() if k!=HEART_ID)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    for name in ['item_dlc01.msgbnd.dcx','item_dlc02.msgbnd.dcx']:
        result=patch((args.input/name).read_bytes())
        assert patch(result)==result
        (args.output/name).write_bytes(result)
    (args.output/'heart_description_zh.json').write_text(json.dumps(
        {'goods_id':HEART_ID,'text':ZH,'status':'merge data; not a zhocn game archive'},
        ensure_ascii=False,indent=2)+'\n')
    print('Two English archives checked; only heart info/caption changed; Chinese merge data saved')


if __name__=='__main__':
    main()
