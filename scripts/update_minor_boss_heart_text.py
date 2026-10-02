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
    'GoodsInfo_dlc01.fmg':'Refreshes field, dungeon and remembrance boss bonuses',
    'GoodsCaption_dlc01.fmg':(
        'Use after defeating a boss to refresh bonuses for this journey.\n\n'
        'Minor bosses: tracked field, cave, catacomb, tunnel and evergaol encounters '
        '(150 in the base game, 31 in the DLC). Each encounter grants max HP, FP '
        'and stamina +0.2%, weapon attack power and sorcery/incantation damage +0.1%. '
        'Minor-boss bonuses add together; a group boss fight counts as one encounter.\n\n'
        'The 21 eligible standard remembrance bosses, plus Bayle, retain their '
        'separate bonuses: max HP +5%, weapon attack power and sorcery/incantation '
        'damage +2.5% each. They do not also count as minor bosses. '
        'The four special remembrances retain their own effects.\n\n'
        'Already defeated encounters are counted. Repeat use refreshes the same '
        'bonuses, without adding duplicate rewards. Reuse after death or reloading '
        'to restore bonuses. Not consumed on use.'),
}
ZH = {
    'GoodsName_dlc01.fmg':'强化之魂',
    'GoodsInfo_dlc01.fmg':'刷新野外、地牢与追忆首领的奖励',
    'GoodsCaption_dlc01.fmg':(
        '击败首领后使用，刷新当前周目的首领奖励。\n\n'
        '小区域首领：已登记的野外、洞窟、地下墓地、坑道、封印监牢首领战，'
        '共181场（本体150场、DLC 31场）。每击败一场，生命、法力、精力上限各+0.2%，'
        '武器攻击力及魔法/祷告伤害各+0.1%。小首领奖励加算；同场多名首领只计一场。\n\n'
        '21位符合条件的普通追忆首领及贝勒保留独立奖励：每位生命上限+5%，'
        '武器攻击力及魔法/祷告伤害各+2.5%，不再计入小首领奖励。'
        '四种特殊追忆保留各自效果。\n\n'
        '当前周目已击败的首领也会计入。重复使用仅刷新，不重复领奖；'
        '死亡或重载后再次使用可恢复增益。使用后不消耗。'),
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
