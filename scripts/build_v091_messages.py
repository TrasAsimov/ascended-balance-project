"""Update Arrow's Sting caption in both English item archives from v0.9."""
from __future__ import annotations
import csv,zipfile,zlib
from pathlib import Path
from build_v05_messages import parse_fmg,write_fmg,bnd_replace,dflt_pack
from build_v09_messages import parts,P
ROOT=Path(__file__).resolve().parent.parent
OLD='Effect: enhances arrow and bolt damage by 50%. Other bow and ammunition bonuses apply separately.'
NEW='Effect: enhances arrow and bolt damage by 100%. Other bow and ammunition bonuses apply separately.'

def main():
 out=ROOT/'output/v091_text';out.mkdir(parents=True,exist_ok=True);ledger=[]
 with zipfile.ZipFile(ROOT/'output/Ascended_Balance_v0.9_Test.zip') as package:
  for variant in ('item_dlc01','item_dlc02'):
   original=package.read(P+variant+'.msgbnd.dcx')
   assert original[0x28:0x2c]==b'DFLT'
   uncompressed=zlib.decompress(original[0x4c:]);before=parts(uncompressed)
   caption=parse_fmg(before['AccessoryCaption.fmg']);old=caption[2150]
   assert old.count(OLD)==1 and '50%' not in old.replace(OLD,'')
   caption[2150]=old.replace(OLD,NEW)
   updated=bnd_replace(uncompressed,{'AccessoryCaption.fmg':write_fmg(caption)})
   candidate=dflt_pack(original,updated)
   verify=parts(zlib.decompress(candidate[0x4c:]))
   assert parse_fmg(verify['AccessoryCaption.fmg'])==caption
   assert all(verify[k]==before[k] for k in before if k!='AccessoryCaption.fmg')
   (out/(variant+'.msgbnd.dcx')).write_bytes(candidate)
   ledger.append((variant,'AccessoryCaption.fmg',2150,OLD,NEW))
 with (ROOT/'changes/v0.9.1_description_changes.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(('文本包','FMG','护符ID','原文效果句','新效果句'));w.writerows(ledger)
 print('Updated English captions:',len(ledger))
if __name__=='__main__':main()
