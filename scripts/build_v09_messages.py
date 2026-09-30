"""Patch the two English item overlays from v0.8 without disturbing other FMGs."""
from __future__ import annotations
import csv,struct,sys,zipfile,zlib
from pathlib import Path
from build_v05_messages import parse_fmg,write_fmg,bnd_replace,dflt_pack
ROOT=Path(__file__).resolve().parent.parent
P='Elden_Ascended_Mod_Age of the Endless Mod/ModEngine/mod/msg/engus/'
LINES={
 2090:'Effect: enhances critical hit damage by 400%',
 2120:'Effect: enhances the final hit of an attack chain by 150%',
 2130:'Effect: enhances charged attack damage by 320%',
 2140:'Effect: boosts sorcery and incantation attack power by 300%. Final damage varies with target defense.',
 2150:'Effect: enhances arrow and bolt damage by 50%. Other bow and ammunition bonuses apply separately.',
 2180:'Effect: enhances jump attack damage by 150%',
 2200:'Effect: enhances guard counter damage by 300%',
 4100:'Effect: reduces stamina consumed while guarding by 90%',
}
INFO={2140:'Boosts sorcery and incantation attack power',2150:'Enhances arrow and bolt damage',4100:'Greatly reduces guarding stamina consumption'}

def parts(raw):
 assert raw[:4]==b'BND4'
 found={}
 for i in range(struct.unpack_from('<I',raw,12)[0]):
  h=0x40+36*i;_,_,size,_,off,_,nameoff=struct.unpack_from('<IIQQIII',raw,h)
  end=nameoff
  while raw[end:end+2]!=b'\0\0':end+=2
  name=raw[nameoff:end].decode('utf-16le').split('\\')[-1]
  found[name]=raw[off:off+size]
 return found

def main():
 out=ROOT/'output/v09_text';out.mkdir(parents=True,exist_ok=True)
 ledger=[]
 with zipfile.ZipFile(ROOT/'output/Ascended_Balance_v0.8_Test.zip') as package:
  for variant in ('item_dlc01','item_dlc02'):
   original=package.read(P+variant+'.msgbnd.dcx')
   assert original[0x28:0x2c]==b'DFLT'
   uncompressed=zlib.decompress(original[0x4c:])
   p=parts(uncompressed);updates={}
   for name in ('AccessoryCaption.fmg','AccessoryInfo.fmg'):
    records=parse_fmg(p[name]);before=dict(records)
    if name=='AccessoryCaption.fmg':
     for rid,line in LINES.items():
      txt=records[rid];assert txt is not None and txt.count('Effect:')==1
      start=txt.index('Effect:');end=txt.find('\n',start)
      if end<0:end=len(txt)
      records[rid]=txt[:start]+line+txt[end:]
      ledger.append([variant,name,rid,txt[start:end],line])
    else:
     for rid,text in INFO.items():
      old=records[rid];assert old
      records[rid]=text;ledger.append([variant,name,rid,old,text])
    assert {key for key in records if records[key]!=before[key]}==set(LINES if name=='AccessoryCaption.fmg' else INFO)
    updates[name]=write_fmg(records)
   updated=bnd_replace(uncompressed,updates)
   candidate=dflt_pack(original,updated)
   verify=parts(zlib.decompress(candidate[0x4c:]))
   assert all(parse_fmg(verify[k])==parse_fmg(updates[k]) for k in updates)
   assert all(verify[k]==p[k] for k in p if k not in updates)
   (out/(variant+'.msgbnd.dcx')).write_bytes(candidate)
 with (ROOT/'changes/v0.9_description_changes.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(('文本包','FMG','护符ID','原文效果句','新效果句'));w.writerows(ledger)
 print('English text overlays',len(ledger),'entries',sum(p.stat().st_size for p in out.glob('*.dcx')))
if __name__=='__main__':main()
