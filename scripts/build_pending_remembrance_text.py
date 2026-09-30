"""Stage English descriptions for all 25 remembrances; not a release."""
from __future__ import annotations
import csv,zipfile,zlib
from pathlib import Path
from build_v05_messages import parse_fmg,write_fmg,bnd_replace,dflt_pack
from build_v09_messages import parts,P
from build_pending_remembrance_params import DLC_IDS,NORMAL_BASE_IDS,SPECIAL_BASE_IDS
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output/pending_remembrance_text'
NEW=('Effect: raises maximum HP by 5%, weapon attack power by 2.5%, '
     'and sorcery/incantation damage by 2.5%\n(Not consumed on use)')
RUNE='Alternatively, it can be used to gain a great bounty of runes.'
HEART_ID=2001431
HEART_TEXT={
 'GoodsName_dlc01.fmg':'Empowered Soul',
 'GoodsInfo_dlc01.fmg':'Refreshes power from defeated remembrance bosses',
 'GoodsCaption_dlc01.fmg':(
  'An empowered soul granted at the beginning of the journey.\n\n'
  'Use it to refresh the power of eligible remembrance bosses you have defeated. '
  'Each of the 21 eligible bosses raises maximum HP by 5%, weapon attack power by 2.5%, '
  'and sorcery/incantation damage by 2.5%. '
  'It has no effect before any eligible boss is defeated.\n\n'
  'It is not consumed on use. The four special remembrances retain their separate effects.'),
}

def main():
 OUT.mkdir(parents=True,exist_ok=True);ledger=[]
 with zipfile.ZipFile(ROOT/'output/Ascended_Balance_v0.9.1_Test.zip') as source:
  base=source.read(P+'item_dlc02.msgbnd.dcx')
  ref=parse_fmg(parts(zlib.decompress(base[0x4c:]))['GoodsCaption.fmg'])
  special={rid:ref[rid][ref[rid].index('Effect:'):ref[rid].index('The power of its namesake')].strip() for rid in SPECIAL_BASE_IDS}
  for variant in ('item_dlc01','item_dlc02'):
   original=source.read(P+variant+'.msgbnd.dcx');assert original[0x28:0x2c]==b'DFLT'
   packed=zlib.decompress(original[0x4c:]);before=parts(packed);updates={}
   for name,rids in (('GoodsCaption.fmg',tuple(range(2950,2965))),('GoodsCaption_dlc01.fmg',DLC_IDS)):
    d=parse_fmg(before[name]);unchanged=dict(d)
    for rid in rids:
     old=d[rid];assert old and old.startswith('Remembrance')
     if rid in SPECIAL_BASE_IDS:
      if 'Effect:' not in old:
       first,rest=old.split('\n',1);d[rid]=first+'\n\n'+special[rid]+'\n'+rest
     else:
      # Replace only the prior short effect sentence; preserve the lore.
      if 'Effect:' in old:
       i=old.index('Effect:');j=old.index('The power of its namesake',i)
       d[rid]=old[:i]+NEW+'\n\n'+old[j:]
      else:
       first,rest=old.split('\n',1);d[rid]=first+'\n\n'+NEW+'\n'+rest
     d[rid]=d[rid].replace(RUNE,'')
     assert ('Effect:' in d[rid] and 'Not consumed' in d[rid]) or rid==2954
     assert d[rid]!=old,(variant,name,rid)
     ledger.append((variant,name,rid,old[:240].replace('\n',' / '),d[rid][:240].replace('\n',' / ')))
    assert {rid for rid in d if d[rid]!=unchanged[rid]}==set(rids)
    updates[name]=write_fmg(d)
   # The recycled DLC goods row 2001431 has no vanilla text entry. Give the
   # one starter heart its own name, short description, and long description.
   for name,value in HEART_TEXT.items():
    d=parse_fmg(before[name]);assert d.get(HEART_ID) is None,(variant,name)
    d[HEART_ID]=value;updates[name]=write_fmg(d)
    ledger.append((variant,name,HEART_ID,'<empty>',value[:240].replace('\n',' / ')))
   candidate=dflt_pack(original,bnd_replace(packed,updates))
   verify=parts(zlib.decompress(candidate[0x4c:]))
   assert all(parse_fmg(verify[name])==parse_fmg(new) for name,new in updates.items())
   assert all(verify[name]==raw for name,raw in before.items() if name not in updates)
   (OUT/(variant+'.msgbnd.dcx')).write_bytes(candidate)
 with (ROOT/'changes/pending_remembrance_text.csv').open('w',encoding='utf-8-sig',newline='') as fp:
  w=csv.writer(fp);w.writerow(('文本包','FMG','追忆ID','原说明开头','待合并说明开头'));w.writerows(ledger)
 print('staged caption entries',len(ledger),'archives',len(tuple(OUT.glob('*.dcx'))))
if __name__=='__main__':main()
