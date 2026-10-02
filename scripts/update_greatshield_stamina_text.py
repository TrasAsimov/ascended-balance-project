"""Change only Greatshield Talisman caption in owned English archives."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'systems/armor/scripts')]
from formats import bnd_entries,bnd_patch,dcx_unpack,dcx_pack
from fmg import fmg_read,fmg_write
CAPTION='Reduces stamina consumed when guarding by 80%.'
def patch(blob):
    raw=dcx_unpack(blob);parts=bnd_entries(raw);name='AccessoryCaption.fmg'
    d=fmg_read(parts[name][1]);before=dict(d);assert 4100 in d
    if d[4100]==CAPTION:return blob
    d[4100]=CAPTION;result=dcx_pack(bnd_patch(raw,{name:fmg_write(d)}))
    after=bnd_entries(dcx_unpack(result))
    assert all(after[n][1]==v[1] for n,v in parts.items() if n!=name)
    check=fmg_read(after[name][1]);assert check.keys()==before.keys()
    assert all(check[k]==v for k,v in before.items() if k!=4100)
    assert check[4100]==CAPTION
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    for name in ['item_dlc01.msgbnd.dcx','item_dlc02.msgbnd.dcx']:
        result=patch((a.input/name).read_bytes());assert patch(result)==result
        (a.output/('01_Greatshield_80pct_20261002_engus_'+name)).write_bytes(result)
    (a.output/'01_Greatshield_80pct_20261002_description_zh.json').write_text(json.dumps({'accessory_id':4100,'caption':'格挡时精力消耗减少80%。','status':'merge data; not a zhocn game archive'},ensure_ascii=False,indent=2)+'\n')
    print('Only Greatshield caption changed; both English archives round-trip and idempotence passed')
if __name__=='__main__':main()
